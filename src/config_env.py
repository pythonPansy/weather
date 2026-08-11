from __future__ import annotations

import os
import re
from typing import Any

_ENV_PLACEHOLDER = re.compile(r"^\$\{([A-Za-z_][A-Za-z0-9_]*)\}$")


def expand_env_vars(value: Any) -> Any:
    """Expand whole-string ``${VAR}`` placeholders from the environment.

    Only strings that are exactly ``${VAR}`` are replaced. Mid-string forms
    such as ``prefix-${VAR}`` are left unchanged.
    """
    if isinstance(value, dict):
        return {key: expand_env_vars(item) for key, item in value.items()}
    if isinstance(value, list):
        return [expand_env_vars(item) for item in value]
    if isinstance(value, str):
        match = _ENV_PLACEHOLDER.fullmatch(value)
        if match is None:
            return value
        name = match.group(1)
        expanded = os.environ.get(name)
        if expanded is None or expanded == "":
            raise ValueError(
                f"environment variable '{name}' is unset or empty "
                f"(needed for config placeholder '${{{name}}}')"
            )
        return expanded
    return value
