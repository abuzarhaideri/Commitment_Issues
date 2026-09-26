"""OpenAI Responses transport, using the provider-neutral JSON action protocol."""
import json
import urllib.error
import urllib.request
from .models import OpenAICompatibleAdapter, ModelError, ProtocolError, ModelResponse, _action, _decode_json


class OpenAIResponsesAdapter(OpenAICompatibleAdapter):
    def __init__(self, model, base_url, api_key, reasoning_effort='low', timeout=60, max_output_tokens=8192):
        super().__init__(model, base_url, api_key, native_tools=False,
                         timeout=timeout, max_output_tokens=max_output_tokens)
        if reasoning_effort not in ('none', 'low', 'medium', 'high', 'xhigh', 'max'):
            raise ValueError('Unsupported reasoning effort')
        self.reasoning_effort = reasoning_effort

    def generate(self, messages, tools=None):
        instructions = ('Return only a strict JSON object {"actions": [{"action": "tool_name", '
                        '"arguments": {}, "goal": "reason"}]}. finish requires summary and '
                        'semantic_review strings. Available tools: ' + json.dumps(tools or []))
        payload = {'model': self.model, 'input': [
            {'role': 'system', 'content': instructions}, *messages],
            'reasoning': {'effort': self.reasoning_effort},
            'max_output_tokens': self.max_output_tokens, 'store': False}
        endpoint = self.base_url if self.base_url.endswith('/responses') else self.base_url + '/responses'
        request = urllib.request.Request(endpoint, data=json.dumps(payload).encode(),
                    headers={'Authorization': 'Bearer ' + self.api_key, 'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read(2 * 1024 * 1024 + 1)
                if len(raw) > 2 * 1024 * 1024:
                    raise ModelError('Model response exceeded size limit')
                result = _decode_json(raw.decode())
        except urllib.error.HTTPError as exc:
            exc.close()
            raise ModelError(f'Model request failed with HTTP status {exc.code}') from None
        except (urllib.error.URLError, OSError, TimeoutError, UnicodeError, ValueError):
            raise ModelError('Model request failed') from None
        if not isinstance(result, dict):
            raise ProtocolError('Malformed Responses API response')
        usage = result.get('usage')
        exact = isinstance(usage, dict) and all(type(usage.get(k)) is int and usage[k] >= 0 for k in ('input_tokens', 'output_tokens'))
        input_tokens = usage['input_tokens'] if exact else self.count_or_estimate_tokens(payload)
        output_tokens = usage['output_tokens'] if exact else self.count_or_estimate_tokens(result)
        try:
            if result.get('status') != 'completed':
                raise ProtocolError('Model response not completed; output allowance may be exhausted')
            output = result.get('output')
            if not isinstance(output, list):
                raise ProtocolError('Missing response output')
            texts = []
            for item in output:
                if not isinstance(item, dict):
                    raise ProtocolError('Malformed response output item')
                if item.get('type') == 'message':
                    for part in item.get('content', []):
                        if not isinstance(part, dict):
                            raise ProtocolError('Malformed response content')
                        if part.get('type') == 'refusal':
                            raise ProtocolError('Model declined the request')
                        if part.get('type') == 'output_text':
                            if not isinstance(part.get('text'), str):
                                raise ProtocolError('Response text must be a string')
                            texts.append(part['text'])
            content = ''.join(texts)
            decoded = _decode_json(content)
            if not isinstance(decoded, dict):
                raise ProtocolError('Action response must be an object')
            if 'actions' in decoded:
                if set(decoded) != {'actions'} or not isinstance(decoded['actions'], list):
                    raise ProtocolError('Response requires an actions array')
                actions = [_action(a) for a in decoded['actions']]
            else:
                actions = [_action(decoded)]
            if not actions:
                raise ProtocolError('Response contains no actions')
        except (TypeError, KeyError, AttributeError, ProtocolError) as exc:
            error = exc if isinstance(exc, ProtocolError) else ProtocolError('Malformed Responses API output')
            error.input_tokens, error.output_tokens, error.usage_estimated = input_tokens, output_tokens, not exact
            raise error from None
        return ModelResponse(actions, content, input_tokens, output_tokens, not exact)
