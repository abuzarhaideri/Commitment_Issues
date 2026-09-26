"""Gemini compatibility adapter with bounded free-tier pacing and retries.

The API key's billing tier is managed in AI Studio, not discoverable here.
The free development launcher requires the user to confirm a Free Tier project.
"""
import time
import json
import re
from urllib.parse import urlencode
import urllib.error
import urllib.request
from .models import OpenAICompatibleAdapter, ModelError, ModelHTTPError, ServiceUnavailableError, ProtocolError
from .rate_limits import RequestPacer, RateLimitError, retry_delay

GEMINI_ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta/openai'
FREE_DEVELOPMENT_MODEL = 'gemini-3.1-flash-lite'


def list_generation_models(api_key):
    """List advertised generation models without sending a generation request.

    Listing does not establish free-tier quota or compatibility-route access.
    Only validated model identifiers are returned; never response bodies or keys.
    """
    GeminiAdapter(FREE_DEVELOPMENT_MODEL, GEMINI_ENDPOINT, api_key)
    names, page_token, seen_tokens = set(), None, set()
    deadline = time.monotonic() + 60
    for _ in range(10):
        params = {'pageSize': 1000}
        if page_token:
            params['pageToken'] = page_token
        request = urllib.request.Request(
            'https://generativelanguage.googleapis.com/v1beta/models?' + urlencode(params),
            headers={'x-goog-api-key': api_key}, method='GET')
        try:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ModelError('Model listing time budget exhausted')
            with urllib.request.urlopen(request, timeout=min(30, remaining)) as response:
                raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise ModelError('Model listing exceeded size limit')
            data = json.loads(raw)
            if not isinstance(data, dict) or not isinstance(data.get('models', []), list):
                raise ModelError('Malformed model listing')
            for model in data.get('models', []):
                if not isinstance(model, dict):
                    continue
                name = model.get('name', '')
                if isinstance(name, str) and re.fullmatch(r'models/[A-Za-z0-9._-]+', name) and 'generateContent' in model.get('supportedGenerationMethods', []):
                    names.add(name.removeprefix('models/'))
            page_token = data.get('nextPageToken')
            if not page_token:
                return sorted(names)
            if not isinstance(page_token, str) or page_token in seen_tokens:
                raise ModelError('Malformed model listing pagination')
            seen_tokens.add(page_token)
        except urllib.error.HTTPError as exc:
            exc.close()
            raise ModelHTTPError(exc.code) from None
        except (urllib.error.URLError, OSError, TimeoutError, UnicodeError, ValueError, TypeError):
            raise ModelError('Model listing failed; no generation request was made') from None
    raise ModelError('Model listing exceeded pagination limit')


class GeminiAdapter(OpenAICompatibleAdapter):
    def __init__(self, model, base_url, api_key, reasoning_effort='low', timeout=60,
                 max_output_tokens=8192, min_interval_seconds=12, max_rate_retries=3, api_route='compatibility'):
        super().__init__(model, base_url, api_key, native_tools=False,
                         timeout=timeout, max_output_tokens=max_output_tokens)
        if base_url.rstrip('/') != GEMINI_ENDPOINT:
            raise ValueError('Gemini adapter requires the official Gemini compatibility endpoint')
        if reasoning_effort not in ('minimal', 'low', 'medium', 'high'):
            raise ValueError('Gemini reasoning effort must be minimal, low, medium, or high')
        if type(max_rate_retries) is not int or not 0 <= max_rate_retries <= 5:
            raise ValueError('Rate-limit retries must be between 0 and 5')
        self.reasoning_effort = reasoning_effort
        if api_route not in ('compatibility', 'native'):
            raise ValueError('Gemini API route must be compatibility or native')
        if api_route == 'native' and not re.fullmatch(r'[A-Za-z0-9._-]+', model):
            raise ValueError('Invalid native Gemini model identifier')
        self.api_route = api_route
        self.pacer = RequestPacer(min_interval_seconds=min_interval_seconds)
        self.max_rate_retries = max_rate_retries
        self.http_requests = self.rate_limit_retries = 0
        self.rate_limit_wait_seconds = 0.0
        self.service_retries = 0
        self.service_wait_seconds = 0.0
        self.event_callback = None

    def prepare_payload(self, payload):
        payload['reasoning_effort'] = self.reasoning_effort
        system = [m['content'] for m in payload['messages'] if m['role'] == 'system']
        payload['messages'] = [{'role': 'system', 'content': '\n\n'.join(system)}] + [
            m for m in payload['messages'] if m['role'] != 'system']
        return payload

    def _event(self, kind, **data):
        if self.event_callback:
            self.event_callback(kind, **data)

    def _request(self, payload):
        if self.api_route == 'compatibility':
            return urllib.request.Request(self.base_url + '/chat/completions',
                data=json.dumps(payload).encode(),
                headers={'Authorization': 'Bearer ' + self.api_key, 'Content-Type': 'application/json'}, method='POST')
        system = [m['content'] for m in payload['messages'] if m['role'] == 'system']
        contents = [{'role': 'model' if m['role'] == 'assistant' else 'user',
                     'parts': [{'text': m['content']}]} for m in payload['messages'] if m['role'] != 'system']
        thinking = ({'thinkingBudget': {'minimal': 1024, 'low': 1024, 'medium': 8192, 'high': 24576}[self.reasoning_effort]}
                    if self.model.startswith('gemini-2.5-') else {'thinkingLevel': self.reasoning_effort})
        body = {'contents': contents, 'systemInstruction': {'parts': [{'text': '\n\n'.join(system)}]},
                'generationConfig': {'maxOutputTokens': self.max_output_tokens,
                                     'responseMimeType': 'application/json', 'thinkingConfig': thinking}}
        return urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/models/' + self.model + ':generateContent',
            data=json.dumps(body).encode(), headers={'x-goog-api-key': self.api_key, 'Content-Type': 'application/json'}, method='POST')

    def _normalize_response(self, body):
        if self.api_route == 'compatibility':
            return body
        try:
            result = json.loads(body)
            candidate = result['candidates'][0]
            parts = candidate.get('content', {}).get('parts', [])
            text = ''.join(p['text'] for p in parts if not p.get('thought') and isinstance(p.get('text'), str))
            if not text or candidate.get('finishReason') != 'STOP':
                raise ProtocolError('Native Gemini response has no complete action text')
            normalized = {'choices': [{'message': {'content': text}}]}
            usage = result.get('usageMetadata', {})
            keys = ('promptTokenCount', 'candidatesTokenCount')
            if all(type(usage.get(k)) is int and usage[k] >= 0 for k in keys):
                thoughts = usage.get('thoughtsTokenCount', 0)
                if type(thoughts) is int and thoughts >= 0:
                    normalized['usage'] = {'prompt_tokens': usage['promptTokenCount'],
                                           'completion_tokens': usage['candidatesTokenCount'] + thoughts}
            return json.dumps(normalized)
        except (ValueError, KeyError, IndexError, TypeError, AttributeError):
            raise ProtocolError('Malformed native Gemini response') from None

    def _post(self, payload):
        deadline = getattr(self, 'deadline', time.monotonic() + self.timeout)
        request = self._request(payload)
        for attempt in range(self.max_rate_retries + 1):
            started = time.monotonic()
            self.pacer.before_request(deadline)
            self.rate_limit_wait_seconds += time.monotonic() - started
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RateLimitError('Run time budget exhausted while waiting for API quota', terminal_quota=True)
            self.http_requests += 1
            self._event('http_request', attempt=attempt + 1)
            try:
                with urllib.request.urlopen(request, timeout=min(self.timeout, remaining)) as response:
                    raw = response.read(2 * 1024 * 1024 + 1)
                    if len(raw) > 2 * 1024 * 1024:
                        raise ModelError('Model response exceeded size limit')
                    return self._normalize_response(raw.decode())
            except urllib.error.HTTPError as exc:
                code = exc.code
                if code not in (429, 500, 502, 503, 504):
                    exc.close()
                    raise ModelHTTPError(code) from None
                headers = exc.headers
                try:
                    raw = exc.read(32768)
                finally:
                    exc.close()
                delay, daily = retry_delay(headers, raw)
                if code != 429:
                    self._event('service_unavailable', status_code=code, retry_after_seconds=delay)
                    if attempt == self.max_rate_retries:
                        raise ServiceUnavailableError(code) from None
                    self.service_retries += 1
                    print(f'Gemini temporarily unavailable (HTTP {code}): waiting before retry.', flush=True)
                    try:
                        waited = self.pacer.backoff(attempt, max(delay or 0, min(60, 12 * 2 ** attempt)), deadline)
                    except RateLimitError:
                        raise ServiceUnavailableError(code) from None
                    self.service_wait_seconds += waited
                    self._event('service_retry_wait', seconds=waited)
                    continue
                self._event('rate_limit', retry_after_seconds=delay, daily_quota=daily)
                if daily:
                    raise RateLimitError('Gemini daily quota exhausted; wait for reset. No provider switch was made.', retry_after=delay, terminal_quota=True) from None
                if attempt == self.max_rate_retries:
                    raise RateLimitError('Gemini quota unavailable after bounded retries; retry later. No provider switch was made.', retry_after=delay, terminal_quota=True) from None
                self.rate_limit_retries += 1
                print('Gemini rate limit: waiting before retry (no paid fallback).', flush=True)
                waited = self.pacer.backoff(attempt, delay, deadline)
                self.rate_limit_wait_seconds += waited
                self._event('rate_limit_wait', seconds=waited)
            except (urllib.error.URLError, OSError, TimeoutError, UnicodeError, ValueError):
                raise ModelError('Model request failed') from None
