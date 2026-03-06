# -*- coding: utf-8 -*-
# Patch sqlite3 with pysqlite3-binary before any chromadb import.
# Ubuntu 20.04 ships sqlite3 3.31.1, but chromadb requires >= 3.35.0.
# pysqlite3-binary bundles a recent sqlite3 (>= 3.35) without needing root.
try:
    import pysqlite3 as _pysqlite3  # noqa: F401
    import sys as _sys

    _sys.modules["sqlite3"] = _sys.modules.pop("pysqlite3")
except ImportError:
    pass  # pysqlite3-binary not installed; let chromadb raise its own error

import logging
import os
import time

from .utils.logging import setup_logger

# Fallback before we can safely read canonical constant definitions.
LOG_LEVEL_ENV = "COPAW_LOG_LEVEL"

_bootstrap_err: Exception | None = None
try:
    # Load persisted env vars before importing modules that read env-backed
    # constants at import time (e.g., WORKING_DIR).
    from .envs import load_envs_into_environ

    load_envs_into_environ()
except Exception as exc:
    # Best effort: package import should not fail if env bootstrap fails.
    _bootstrap_err = exc

_t0 = time.perf_counter()
setup_logger(os.environ.get(LOG_LEVEL_ENV, "info"))
if _bootstrap_err is not None:
    logging.getLogger(__name__).warning(
        "copaw: failed to load persisted envs on init: %s",
        _bootstrap_err,
    )
logging.getLogger(__name__).debug(
    "%.3fs package init",
    time.perf_counter() - _t0,
)
