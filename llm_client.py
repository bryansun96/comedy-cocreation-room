import json
import re
import time
from typing import Any

import requests

from contracts import LLMJSONResponse, LLMResponseMeta


class LLMClientError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.model = model
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = 120

    def _repair_json_content(self, raw_content: str) -> dict[str, Any] | None:
        url = f"{self._base_url}/chat/completions"
        payload = {
            "model": self.model,
            "max_tokens": 4000,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You repair malformed JSON. Return strict JSON only. "
                        "Do not explain. Preserve the original structure and values as much as possible."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "请把下面内容修复成合法 JSON，仅返回修复后的 JSON，不要解释：\n\n"
                        f"{raw_content[:12000]}"
                    ),
                },
            ],
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self._timeout)
            if response.status_code >= 400:
                return None
            repaired_json = response.json()
            repaired_content = _extract_message_content(repaired_json)
            repaired = _parse_json_content(repaired_content)
            return repaired if isinstance(repaired, dict) else None
        except Exception:
            return None

    def generate_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> LLMJSONResponse:
        started_at = time.perf_counter()
        url = f"{self._base_url}/chat/completions"
        payload = {
            "model": self.model,
            "max_tokens": 4000,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self._timeout)
        except requests.exceptions.RequestException as exc:
            raise LLMClientError(_build_connection_message(self._base_url, exc)) from exc

        if response.status_code == 401:
            raise LLMClientError("调用模型失败：鉴权失败，请检查 API Key。")
        if response.status_code == 403:
            raise LLMClientError("调用模型失败：当前 token 没有权限访问该模型或接口。")
        if response.status_code == 404:
            raise LLMClientError(_build_not_found_message(self._base_url, self.model, response.text))
        if response.status_code == 429:
            raise LLMClientError("调用模型失败：触发限流，请稍后重试。")
        if response.status_code >= 400:
            raise LLMClientError(_build_status_message(self._base_url, self.model, response))

        try:
            response_json = response.json()
        except ValueError as exc:
            raise LLMClientError(f"调用模型失败：服务返回了非 JSON 响应。原始内容：{response.text[:500]}") from exc

        try:
            content = _extract_message_content(response_json)
            parsed = _parse_json_content(content)
        except (TypeError, ValueError, KeyError, IndexError) as exc:
            repaired = self._repair_json_content(content if 'content' in locals() else response.text)
            if repaired is not None:
                parsed = repaired
            else:
                raise LLMClientError(_build_parse_error_message(response_json, exc)) from exc

        if not isinstance(parsed, dict):
            raise LLMClientError("模型返回的 JSON 顶层结构不是对象。")
        return {
            "data": parsed,
            "meta": _build_response_meta(response_json, self.model, started_at),
        }


ClaudeClient = LLMClient


def _extract_message_content(response_json: dict[str, Any]) -> str:
    choices = response_json.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("No choices in response")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise ValueError("No message object in response")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Empty content in response")
    return content


def _build_response_meta(response_json: dict[str, Any], requested_model: str, started_at: float) -> LLMResponseMeta:
    usage = response_json.get("usage") if isinstance(response_json.get("usage"), dict) else {}
    choices = response_json.get("choices") if isinstance(response_json.get("choices"), list) else []
    finish_reason = None
    if choices and isinstance(choices[0], dict):
        finish_reason = choices[0].get("finish_reason")
    usage_payload = {
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
    }
    return {
        "requested_model": requested_model,
        "actual_model": response_json.get("model"),
        "stop_reason": finish_reason,
        "usage": {k: v for k, v in usage_payload.items() if isinstance(v, int)},
        "duration_seconds": round(time.perf_counter() - started_at, 2),
    }


def _build_connection_message(base_url: str, exc: Exception) -> str:
    return (
        "调用模型失败：无法连接到服务。"
        f" 当前 Base URL = {base_url or '未填写'}。"
        " 请确认网络是否可达，Base URL 是否正确。"
        f" 原始错误：{exc}"
    )


def _build_not_found_message(base_url: str, model: str, raw_text: str) -> str:
    return (
        "调用模型失败：接口地址或模型不存在。"
        f" 当前 Base URL = {base_url or '未填写'}，Model = {model or '未填写'}。"
        f" 上游返回：{raw_text[:500]}"
    )


def _build_status_message(base_url: str, model: str, response: requests.Response) -> str:
    response_text = response.text or ""
    prefix = f"调用模型失败：HTTP {response.status_code}。"
    details = [f"当前 Base URL = {base_url or '未填写'}", f"Model = {model or '未填写'}"]

    lowered = response_text.lower()
    if "invalid api key" in lowered or "authentication" in lowered or "unauthorized" in lowered:
        hint = "鉴权失败，请检查 DEEPSEEK_API_KEY 是否正确。"
    elif "not found" in lowered or "unknown" in lowered or "model" in lowered:
        hint = "模型名称或路径可能不存在，请检查 DEEPSEEK_MODEL 和 DEEPSEEK_BASE_URL。"
    else:
        hint = "请根据返回内容检查 API 配置。"

    return f"{prefix}{'；'.join(details)}。{hint} 上游返回：{response_text[:500]}"


def _build_parse_error_message(response_json: dict[str, Any], exc: Exception) -> str:
    model = response_json.get("model") or "未知"
    finish_reason = "未知"
    choices = response_json.get("choices")
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        finish_reason = choices[0].get("finish_reason") or "未知"
    return (
        "模型返回内容无法解析为 JSON。"
        f" 实际返回 model = {model}，finish_reason = {finish_reason}。"
        " 模型可能未按要求输出 JSON，或输出被截断。"
        f" 解析错误：{exc}"
    )


_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)


def _normalize_json_candidate(text: str) -> str:
    normalized_chars: list[str] = []
    in_string = False
    delimiter = '"'
    i = 0
    length = len(text)

    while i < length:
        char = text[i]

        if not in_string:
            if char in {'"', '“', '”'}:
                in_string = True
                delimiter = char
                normalized_chars.append('"')
            else:
                normalized_chars.append(char)
            i += 1
            continue

        if char == "\\":
            normalized_chars.append(char)
            if i + 1 < length:
                normalized_chars.append(text[i + 1])
                i += 2
            else:
                i += 1
            continue

        if delimiter == '"':
            if char == '"':
                in_string = False
                normalized_chars.append('"')
            else:
                normalized_chars.append(char)
            i += 1
            continue

        if char in {'“', '”'} and _looks_like_string_end(text, i + 1):
            in_string = False
            normalized_chars.append('"')
        else:
            normalized_chars.append(char)
        i += 1

    return ''.join(normalized_chars)


def _looks_like_string_end(text: str, index: int) -> bool:
    while index < len(text) and text[index].isspace():
        index += 1
    return index >= len(text) or text[index] in {',', '}', ']', ':'}


def _parse_json_content(content: str) -> Any:
    text = content.strip()
    if not text:
        raise ValueError("Empty response")

    candidates = [text]
    fence_match = _JSON_FENCE_RE.match(text)
    if fence_match:
        candidates.insert(0, fence_match.group(1).strip())

    object_start = text.find("{")
    object_end = text.rfind("}")
    if object_start != -1 and object_end != -1 and object_end > object_start:
        candidates.append(text[object_start : object_end + 1])

    array_start = text.find("[")
    array_end = text.rfind("]")
    if array_start != -1 and array_end != -1 and array_end > array_start:
        candidates.append(text[array_start : array_end + 1])

    for candidate in candidates:
        normalized = _normalize_json_candidate(candidate)
        try:
            return json.loads(normalized)
        except json.JSONDecodeError:
            continue

    raise ValueError("No valid JSON payload found")
