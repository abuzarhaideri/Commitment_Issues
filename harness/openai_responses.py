"""OpenAI Responses transport, using the provider-neutral JSON action protocol."""
import json
from .models import OpenAICompatibleAdapter, ModelError, ProtocolError, ModelResponse, action_protocol_instruction, _action, _decode_json


class OpenAIResponsesAdapter(OpenAICompatibleAdapter):
    def __init__(self, model, base_url, api_key, reasoning_effort='low', timeout=60, max_output_tokens=8192, max_retries=2):
        super().__init__(model, base_url, api_key, native_tools=False,
                         timeout=timeout, max_output_tokens=max_output_tokens, max_retries=max_retries)
        if reasoning_effort not in ('none', 'low', 'medium', 'high', 'xhigh', 'max'):
            raise ValueError('Unsupported reasoning effort')
        self.reasoning_effort = reasoning_effort

    def _request_payload(self, messages, tools=None):
        return {'model': self.model, 'input': [
            {'role': 'system', 'content': action_protocol_instruction(tools)}, *messages],
            'reasoning': {'effort': self.reasoning_effort},
            'max_output_tokens': self.max_output_tokens, 'store': False}

    def generate(self, messages, tools=None):
        payload = self._request_payload(messages, tools)
        endpoint = self.base_url if self.base_url.endswith('/responses') else self.base_url + '/responses'
        result = _decode_json(self._post_endpoint(payload, endpoint))
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
                    if item.get('status') not in (None, 'completed'):
                        raise ProtocolError('Response message not completed; no actions executed')
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
