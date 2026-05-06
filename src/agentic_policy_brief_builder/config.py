"""Application configuration loading utilities."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, get_args

from dotenv import load_dotenv

APP_ENV_VALUES = Literal["local", "test", "staging", "production"]

OPENAI_API_KEY = "OPENAI_API_KEY"
OPENAI_MODEL = "OPENAI_MODEL"
OPENAI_EMBEDDING_MODEL = "OPENAI_EMBEDDING_MODEL"
APP_ENV = "APP_ENV"
VECTOR_STORE_DIR = "VECTOR_STORE_DIR"

DEFAULT_OPENAI_MODEL = "gpt-5.5"
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_APP_ENV: APP_ENV_VALUES = "local"
DEFAULT_VECTOR_STORE_DIR = ".chroma"


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Typed application configuration values."""

    openai_api_key: str | None = None
    openai_model: str = DEFAULT_OPENAI_MODEL
    openai_embedding_model: str = DEFAULT_OPENAI_EMBEDDING_MODEL
    app_env: APP_ENV_VALUES = DEFAULT_APP_ENV
    vector_store_dir: Path = Path(DEFAULT_VECTOR_STORE_DIR)

    def __post_init__(self) -> None:
        if self.app_env not in get_args(APP_ENV_VALUES):
            allowed = ", ".join(get_args(APP_ENV_VALUES))
            msg = f"APP_ENV must be one of: {allowed}."
            raise ValueError(msg)

    @property
    def has_openai_api_key(self) -> bool:
        """Return whether the configuration includes a non-empty OpenAI API key."""

        return bool(self.openai_api_key and self.openai_api_key.strip())

    @property
    def missing_required_keys(self) -> tuple[str, ...]:
        """Return required configuration keys that are missing or blank."""

        missing: list[str] = []
        if not self.has_openai_api_key:
            missing.append(OPENAI_API_KEY)
        return tuple(missing)


def load_config(
    *,
    environ: Mapping[str, str] | None = None,
    streamlit_secrets: Mapping[str, Any] | None = None,
    env_file: str | Path | None = ".env",
) -> AppConfig:
    """Load typed app configuration from .env, environment, and Streamlit secrets.

    Environment variables take precedence over Streamlit secrets so deployment
    platforms can override checked-in app settings safely. Local ``.env`` loading
    is opt-out by passing ``env_file=None``.
    """

    if env_file is not None and environ is None:
        load_dotenv(dotenv_path=env_file, override=False)

    source_environ = os.environ if environ is None else environ

    return AppConfig(
        openai_api_key=_get_setting(OPENAI_API_KEY, source_environ, streamlit_secrets),
        openai_model=_get_setting(
            OPENAI_MODEL,
            source_environ,
            streamlit_secrets,
            default=DEFAULT_OPENAI_MODEL,
        ),
        openai_embedding_model=_get_setting(
            OPENAI_EMBEDDING_MODEL,
            source_environ,
            streamlit_secrets,
            default=DEFAULT_OPENAI_EMBEDDING_MODEL,
        ),
        app_env=_get_setting(APP_ENV, source_environ, streamlit_secrets, default=DEFAULT_APP_ENV),
        vector_store_dir=Path(
            _get_setting(
                VECTOR_STORE_DIR,
                source_environ,
                streamlit_secrets,
                default=DEFAULT_VECTOR_STORE_DIR,
            )
        ),
    )


def format_missing_config_message(config: AppConfig) -> str | None:
    """Return a user-facing message for missing required configuration."""

    missing_keys = config.missing_required_keys
    if not missing_keys:
        return None

    keys = ", ".join(missing_keys)
    return (
        f"Missing required configuration: {keys}. "
        "Set it in your environment, local .env file, or Streamlit secrets before "
        "generating policy briefs."
    )


def _get_setting(
    key: str,
    environ: Mapping[str, str],
    streamlit_secrets: Mapping[str, Any] | None,
    *,
    default: str | None = None,
) -> str | None:
    env_value = environ.get(key)
    if _has_value(env_value):
        return str(env_value)

    secret_value = _get_streamlit_secret(key, streamlit_secrets)
    if _has_value(secret_value):
        return str(secret_value)

    return default


def _get_streamlit_secret(key: str, streamlit_secrets: Mapping[str, Any] | None) -> Any | None:
    if streamlit_secrets is None:
        return None

    direct_value = _mapping_get(streamlit_secrets, key)
    if _has_value(direct_value):
        return direct_value

    lower_key = key.lower()
    direct_lower_value = _mapping_get(streamlit_secrets, lower_key)
    if _has_value(direct_lower_value):
        return direct_lower_value

    section_name, _, nested_name = lower_key.partition("_")
    section = _mapping_get(streamlit_secrets, section_name)
    if isinstance(section, Mapping):
        return _mapping_get(section, nested_name)

    return None


def _mapping_get(mapping: Mapping[str, Any], key: str) -> Any | None:
    try:
        return mapping.get(key)
    except Exception:
        return None


def _has_value(value: Any | None) -> bool:
    return value is not None and str(value).strip() != ""
