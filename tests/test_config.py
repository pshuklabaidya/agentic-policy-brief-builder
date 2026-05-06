from pathlib import Path

from agentic_policy_brief_builder.config import (
    DEFAULT_OPENAI_EMBEDDING_MODEL,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_VECTOR_STORE_DIR,
    OPENAI_API_KEY,
    AppConfig,
    format_missing_config_message,
    load_config,
)


def test_load_config_reports_missing_api_key_with_defaults() -> None:
    config = load_config(environ={}, env_file=None)

    assert config.openai_api_key is None
    assert config.openai_model == DEFAULT_OPENAI_MODEL
    assert config.openai_embedding_model == DEFAULT_OPENAI_EMBEDDING_MODEL
    assert config.app_env == "local"
    assert config.vector_store_dir == Path(DEFAULT_VECTOR_STORE_DIR)
    assert config.missing_required_keys == (OPENAI_API_KEY,)
    assert "Missing required configuration: OPENAI_API_KEY" in format_missing_config_message(config)


def test_load_config_reads_environment_values_before_streamlit_secrets() -> None:
    config = load_config(
        environ={
            "OPENAI_API_KEY": "env-key",
            "OPENAI_MODEL": "gpt-env",
            "OPENAI_EMBEDDING_MODEL": "embedding-env",
            "APP_ENV": "test",
            "VECTOR_STORE_DIR": "tmp/vector-store",
        },
        streamlit_secrets={
            "OPENAI_API_KEY": "secret-key",
            "OPENAI_MODEL": "gpt-secret",
        },
        env_file=None,
    )

    assert config.openai_api_key == "env-key"
    assert config.openai_model == "gpt-env"
    assert config.openai_embedding_model == "embedding-env"
    assert config.app_env == "test"
    assert config.vector_store_dir == Path("tmp/vector-store")
    assert config.missing_required_keys == ()
    assert format_missing_config_message(config) is None


def test_load_config_reads_streamlit_secrets_when_environment_is_missing() -> None:
    config = load_config(
        environ={},
        streamlit_secrets={
            "openai": {
                "api_key": "secret-key",
                "model": "gpt-secret",
                "embedding_model": "embedding-secret",
            },
            "APP_ENV": "staging",
            "VECTOR_STORE_DIR": "secret-vector-store",
        },
        env_file=None,
    )

    assert config.openai_api_key == "secret-key"
    assert config.openai_model == "gpt-secret"
    assert config.openai_embedding_model == "embedding-secret"
    assert config.app_env == "staging"
    assert config.vector_store_dir == Path("secret-vector-store")


def test_load_config_reads_local_env_file(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OPENAI_API_KEY=dotenv-key\n"
        "OPENAI_MODEL=gpt-dotenv\n"
        "OPENAI_EMBEDDING_MODEL=embedding-dotenv\n"
        "APP_ENV=test\n"
        "VECTOR_STORE_DIR=dotenv-vector-store\n"
    )
    for key in (
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "OPENAI_EMBEDDING_MODEL",
        "APP_ENV",
        "VECTOR_STORE_DIR",
    ):
        monkeypatch.delenv(key, raising=False)

    config = load_config(env_file=env_file)

    assert config.openai_api_key == "dotenv-key"
    assert config.openai_model == "gpt-dotenv"
    assert config.openai_embedding_model == "embedding-dotenv"
    assert config.app_env == "test"
    assert config.vector_store_dir == Path("dotenv-vector-store")


def test_app_config_treats_blank_api_key_as_missing() -> None:
    config = AppConfig(openai_api_key="   ")

    assert not config.has_openai_api_key
    assert config.missing_required_keys == (OPENAI_API_KEY,)
