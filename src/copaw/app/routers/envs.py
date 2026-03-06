# -*- coding: utf-8 -*-
"""API endpoints for environment variable management."""
from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...envs import load_envs, save_envs, delete_env_var

router = APIRouter(prefix="/envs", tags=["envs"])

# Keywords that indicate a value is likely a credential and should be masked.
_SENSITIVE_KEY_KEYWORDS = (
    "key", "secret", "token", "password", "passwd",
    "credential", "auth", "webhook", "signing",
)


def _mask_env_value(key: str, value: str) -> str:
    """Return a partially-masked value for sensitive keys.

    The first 4 characters are kept to help the user recognise which
    credential is stored; the remainder is replaced with ``****``.
    """
    if not value:
        return value
    if any(kw in key.lower() for kw in _SENSITIVE_KEY_KEYWORDS):
        visible = min(4, len(value))
        return value[:visible] + "****"
    return value


def _is_masked_placeholder(value: str) -> bool:
    """Return True when *value* looks like a mask placeholder.

    The UI re-submits the masked value unchanged when the user has not
    edited a field; in that case the original stored value should be kept.
    """
    return value.endswith("****")


# ------------------------------------------------------------------
# Request / Response models
# ------------------------------------------------------------------


class EnvVar(BaseModel):
    """Single environment variable."""

    key: str = Field(..., description="Variable name")
    value: str = Field(..., description="Variable value (sensitive values are masked)")


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.get(
    "",
    response_model=List[EnvVar],
    summary="List all environment variables",
)
async def list_envs() -> List[EnvVar]:
    """Return all configured env vars (sensitive values are masked)."""
    envs = load_envs()
    return [EnvVar(key=k, value=_mask_env_value(k, v)) for k, v in sorted(envs.items())]


@router.put(
    "",
    response_model=List[EnvVar],
    summary="Batch save environment variables",
    description="Replace all environment variables with "
    "the provided dict. Keys not present are removed.",
)
async def batch_save_envs(
    body: Dict[str, str],
) -> List[EnvVar]:
    """Batch save – full replacement of all env vars."""
    # Validate keys
    for key in body:
        if not key.strip():
            raise HTTPException(
                400,
                detail="Key cannot be empty",
            )
    existing = load_envs()
    cleaned: Dict[str, str] = {}
    for k, v in body.items():
        k = k.strip()
        # When the UI re-submits a masked placeholder, preserve the original value.
        if _is_masked_placeholder(v) and k in existing:
            cleaned[k] = existing[k]
        else:
            cleaned[k] = v
    save_envs(cleaned)
    return [EnvVar(key=k, value=_mask_env_value(k, v)) for k, v in sorted(cleaned.items())]


@router.delete(
    "/{key}",
    response_model=List[EnvVar],
    summary="Delete an environment variable",
)
async def delete_env(key: str) -> List[EnvVar]:
    """Delete a single env var."""
    envs = load_envs()
    if key not in envs:
        raise HTTPException(
            404,
            detail=f"Env var '{key}' not found",
        )
    envs = delete_env_var(key)
    return [EnvVar(key=k, value=_mask_env_value(k, v)) for k, v in sorted(envs.items())]
