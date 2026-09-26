"""Small, dependency-free adapters for OpenAI-compatible chat APIs."""
from __future__ import annotations

import json
import math
import urllib.error
import urllib.request
from urllib.parse import urlsplit
import ipaddress
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class ModelError(RuntimeError):
    """A model request failed (messages deliberately omit response bodies)."""


class ModelHTTPError(ModelError):
    def __init__(self, status_code):
        super().__init__(f'Model request failed with HTTP status {status_code}')
        self.status_code = status_code
        self.input_tokens = self.output_tokens = 0
        self.usage_estimated = True


class ProtocolError(ModelError):
    """The model returned a response outside the action protocol."""


class ServiceUnavailableError(ModelHTTPError):
    """Transient provider errors exhausted transport retries, not coding recovery."""
    def __init__(self, status_code):
        super().__init__(status_code)
        self.args = (f'Gemini service unavailable (HTTP {status_code}) after bounded retries; retry later. No provider switch was made.',)


@dataclass
class Action:
    name: str
    arguments: dict
    goal: str = ""


@dataclass
class ModelResponse:
    actions: list[Action]
    content: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    usage_estimated: bool = True


class ModelAdapter(ABC):
    @abstractmethod
    def generate(self, messages: list[dict], tools: list[dict] | None = None) -> ModelResponse:
        raise NotImplementedError

    def supports_native_tools(self) -> bool:
        return False

    def count_or_estimate_tokens(self, payload: Any) -> int:
        text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        return max(1, math.ceil(len(text) / 4)) if text else 0


def _decode_json(value: str) -> Any:
    if not isinstance(value, str):
        raise ProtocolError("JSON content must be a string")
    value = value.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if len(lines) < 3 or lines[-1].strip() != "```" or lines[0].strip() not in ("```", "```json"):
            raise ProtocolError("Invalid JSON fence")
        value = "\n".join(lines[1:-1])
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        raise ProtocolError("Invalid action JSON") from None


def _action(value: Any) -> Action:
    if not isinstance(value, dict):
        raise ProtocolError("Each action must be an object")
    if set(value) - {"action", "name", "arguments", "goal"}:
        raise ProtocolError("Unknown action fields")
    if "action" in value and "name" in value:
        raise ProtocolError("Ambiguous action name")
    name = value.get("action", value.get("name"))
    arguments = value.get("arguments")
    goal = value.get("goal", "")
    if not isinstance(name, str) or not name.strip() or not isinstance(arguments, dict) or not isinstance(goal, str):
        raise ProtocolError("Action requires a name, object arguments, and string goal")
    if name == "finish" and (not isinstance(arguments.get("summary"), str) or not isinstance(arguments.get("semantic_review"), str)):
        raise ProtocolError("Finish requires summary and semantic_review strings")
    return Action(name, arguments, goal)


class OpenAICompatibleAdapter(ModelAdapter):
    def __init__(self, model: str, base_url: str, api_key: str, native_tools: bool = False, timeout: float = 60, max_output_tokens: int = 2048):
        if not isinstance(model, str) or not model.strip():
            raise ValueError("An explicit model is required")
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError("A base URL is required")
        try:
            parsed = urlsplit(base_url)
            host = parsed.hostname
            parsed.port  # Validate malformed port declarations.
            loopback = host == "localhost"
            if host and not loopback:
                try:
                    loopback = ipaddress.ip_address(host).is_loopback
                except ValueError:
                    pass
            if not host or parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment or "?" in base_url or "#" in base_url or any(char.isspace() for char in base_url):
                raise ValueError
            if parsed.scheme != "https" and not (parsed.scheme == "http" and loopback):
                raise ValueError
        except (ValueError, TypeError):
            raise ValueError("Base URL must use HTTPS or loopback HTTP without userinfo, query, or fragment") from None
        if type(max_output_tokens) is not int or max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be a positive integer")
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be a positive finite number")
        if not isinstance(api_key, str):
            raise ValueError("API key must be a string")
        if any(ord(char) <= 32 or ord(char) == 127 for char in api_key):
            raise ValueError("API key contains invalid whitespace or control characters")
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.native_tools = native_tools
        self.timeout = timeout
        self.max_output_tokens = max_output_tokens

    def supports_native_tools(self) -> bool:
        return self.native_tools

    def prepare_payload(self, payload):
        return payload

    def _post(self, payload):
        endpoint = self.base_url if self.base_url.endswith("/chat/completions") else self.base_url + "/chat/completions"
        request = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers={"Authorization": "Bearer " + self.api_key, "Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw_body = response.read(2 * 1024 * 1024 + 1)
                if len(raw_body) > 2 * 1024 * 1024:
                    raise ModelError("Model response exceeded size limit")
                return raw_body.decode("utf-8")
        except urllib.error.HTTPError as exc:
            exc.close()
            raise ModelHTTPError(exc.code) from None
        except (urllib.error.URLError, OSError, TimeoutError, UnicodeError, ValueError):
            raise ModelError("Model request failed") from None
    def generate(self, messages: list[dict], tools: list[dict] | None = None) -> ModelResponse:
        request_messages = list(messages)
        payload = {"model": self.model, "messages": request_messages, "max_tokens": self.max_output_tokens}
        if self.native_tools:
            if tools:
                payload["tools"] = [tool if tool.get("type") == "function" else {"type": "function", "function": tool} for tool in tools]
        else:
            instruction = (
                'Return only a strict JSON object with an "actions" array. Each action has '
                '"action" (string), "arguments" (object), and "goal" (string). '
                'The finish action requires arguments "summary" and "semantic_review", both strings. '
                'Available tools: ' + json.dumps(tools or [], ensure_ascii=False)
            )
            request_messages.insert(0, {"role": "system", "content": instruction})
        payload = self.prepare_payload(payload)
        body = self._post(payload)
        result = _decode_json(body)
        try:
            message = result["choices"][0]["message"]
            content = message.get("content") or ""
            if not isinstance(content, str):
                raise ProtocolError("Model content must be a string")
            calls = message.get("tool_calls")
            if self.native_tools and calls:
                if not isinstance(calls, list):
                    raise ProtocolError("Tool calls must be a list")
                actions = []
                for call in calls:
                    function = call["function"]
                    arguments = _decode_json(function["arguments"])
                    actions.append(_action({"action": function["name"], "arguments": arguments}))
            else:
                decoded = _decode_json(content)
                if not isinstance(decoded, dict):
                    raise ProtocolError("Action response must be an object")
                if "actions" in decoded:
                    if set(decoded) != {"actions"} or not isinstance(decoded["actions"], list):
                        raise ProtocolError("Response requires an actions array")
                    actions = [_action(item) for item in decoded["actions"]]
                else:
                    actions = [_action(decoded)]
            if not actions:
                raise ProtocolError("Response contains no actions")
        except (KeyError, IndexError, TypeError, AttributeError):
            raise ProtocolError("Malformed model response") from None
        usage = result.get("usage")
        valid_usage = isinstance(usage, dict) and all(type(usage.get(key)) is int and usage[key] >= 0 for key in ("prompt_tokens", "completion_tokens"))
        return ModelResponse(actions, content,
                             usage["prompt_tokens"] if valid_usage else self.count_or_estimate_tokens(payload),
                             usage["completion_tokens"] if valid_usage else self.count_or_estimate_tokens(message),
                             not valid_usage)
