from dataclasses import dataclass
import os
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).with_name(".env"))
except ImportError:
    pass


@dataclass(frozen=True)
class RuntimeConfig:
    base_url: str
    api_key: str
    model: str


ENV_KEYS = {
    "base_url": (
        "DEEPSEEK_BASE_URL",
        "ANTHROPIC_BASE_URL",
        "CC_SWITCH_BASE_URL",
    ),
    "api_key": (
        "DEEPSEEK_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "CC_SWITCH_API_KEY",
    ),
    "model": (
        "DEEPSEEK_MODEL",
        "ANTHROPIC_MODEL",
        "ANTHROPIC_DEFAULT_SONNET_MODEL",
        "CC_SWITCH_MODEL",
    ),
}
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-pro"


def _read_secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value).strip()


def _read_first(names: tuple[str, ...]) -> str:
    for name in names:
        value = _read_secret(name) or os.getenv(name, "").strip()
        if value:
            return value
    return ""


def _normalize_base_url(base_url: str) -> str:
    cleaned = base_url.strip().rstrip("/")
    if not cleaned:
        return ""
    parsed = urlparse(cleaned)
    if parsed.path.rstrip("/"):
        return cleaned
    return cleaned


def get_runtime_defaults() -> RuntimeConfig:
    model = _read_first(ENV_KEYS["model"]) or DEFAULT_MODEL
    return RuntimeConfig(
        base_url=_normalize_base_url(_read_first(ENV_KEYS["base_url"]) or DEFAULT_BASE_URL),
        api_key=_read_first(ENV_KEYS["api_key"]),
        model=model,
    )


def build_runtime_config(base_url: str, api_key: str, model: str) -> RuntimeConfig:
    defaults = get_runtime_defaults()
    return RuntimeConfig(
        base_url=_normalize_base_url(base_url or defaults.base_url),
        api_key=(api_key or defaults.api_key).strip(),
        model=(model or defaults.model).strip(),
    )


def get_missing_runtime_fields(config: RuntimeConfig) -> list[str]:
    missing_fields: list[str] = []
    if not config.base_url:
        missing_fields.append("Base URL")
    if not config.api_key:
        missing_fields.append("API Key")
    if not config.model:
        missing_fields.append("Model")
    return missing_fields
