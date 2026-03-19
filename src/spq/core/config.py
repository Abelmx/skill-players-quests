"""Configuration loading and management.

Resolution order (highest priority first):
  1. Environment variables  (SPQ_{PROVIDER}_*, SPQ_*)
  2. YAML config file       (configs/default.yaml)
  3. Hard-coded defaults
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from spq.core.models import ActivationMode, EvalConfig, ProviderConfig, SamplingParams


def _env(key: str) -> str | None:
    """Read an env var; treat empty string as unset."""
    val = os.environ.get(key)
    return val if val else None


def _env_float(key: str) -> float | None:
    val = _env(key)
    if val is None:
        return None
    try:
        return float(val)
    except ValueError:
        return None


def _env_int(key: str) -> int | None:
    val = _env(key)
    if val is None:
        return None
    try:
        return int(val)
    except ValueError:
        return None


def _resolve_sampling(provider_key: str) -> SamplingParams:
    """Build SamplingParams from env vars.

    Per-provider vars (SPQ_{PROVIDER}_TEMPERATURE) override
    global vars (SPQ_TEMPERATURE).
    """
    prefix = f"SPQ_{provider_key.upper()}_"
    return SamplingParams(
        temperature=_env_float(f"{prefix}TEMPERATURE") or _env_float("SPQ_TEMPERATURE"),
        top_p=_env_float(f"{prefix}TOP_P") or _env_float("SPQ_TOP_P"),
        max_tokens=_env_int(f"{prefix}MAX_TOKENS") or _env_int("SPQ_MAX_TOKENS"),
    )


def _resolve_provider(name: str, yaml_cfg: dict | None = None) -> ProviderConfig:
    """Build a ProviderConfig from env + YAML, env takes precedence.

    Supports both new `models: [...]` list and legacy `model: "..."` field.
    """
    yaml_cfg = yaml_cfg or {}
    prefix = f"SPQ_{name.upper()}_"

    api_key_env = _env(f"{prefix}API_KEY_ENV") or yaml_cfg.get("api_key_env", f"{prefix}API_KEY")
    base_url = _env(f"{prefix}BASE_URL") or yaml_cfg.get("base_url")

    raw_models = yaml_cfg.get("models", [])
    if isinstance(raw_models, str):
        raw_models = [raw_models]
    models: list[str] = raw_models
    if not models:
        single = _env(f"{prefix}MODEL") or yaml_cfg.get("model", "")
        if single:
            models = [single]

    return ProviderConfig(
        provider_type=name,
        api_key_env=api_key_env,
        models=models,
        base_url=base_url,
        sampling=_resolve_sampling(name),
    )


def load_config(path: Path | None = None) -> EvalConfig:
    """Load evaluation config from YAML file + env overrides."""
    if path is None:
        path = Path("configs/default.yaml")

    raw: dict = {}
    if path.exists():
        with open(path) as f:
            raw = yaml.safe_load(f) or {}

    providers: dict[str, ProviderConfig] = {}
    for name, cfg in raw.get("providers", {}).items():
        providers[name] = _resolve_provider(name, cfg)

    return EvalConfig(
        skills_dir=raw.get("skills_dir", "skills"),
        tasks_dir=raw.get("tasks_dir", "tasks"),
        activation_mode=ActivationMode(
            _env("SPQ_ACTIVATION_MODE") or raw.get("activation_mode", "catalog")
        ),
        max_turns=_env_int("SPQ_MAX_TURNS") or raw.get("max_turns", 10),
        bash_timeout=_env_int("SPQ_BASH_TIMEOUT") or raw.get("bash_timeout", 30),
        providers=providers,
    )
