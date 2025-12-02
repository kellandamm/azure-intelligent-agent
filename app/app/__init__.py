"""Lightweight package shim that exposes existing top-level modules under the
`app.*` package namespace so code can import `app.rls_middleware`, etc. This
avoids duplicating files while making imports package-qualified which is more
robust in multi-process environments.
"""
from __future__ import annotations

import importlib
import sys
from types import ModuleType

# List of top-level module names to expose under app.<module>
_MODULES = [
    "rls_middleware",
    "powerbi_integration",
    "agent_framework_manager",
    "routes_auth",
    "routes_admin_agents",
    "agent_tools",
    "chart_generator",
    "purview_integration",
]

for _m in _MODULES:
    try:
        # Import the original top-level module (e.g. rls_middleware)
        _orig = importlib.import_module(_m)
    except Exception:
        # If the original module cannot be imported at package import time,
        # don't fail here — leave Python to raise a clear ImportError later
        # when the application actually needs it.
        continue

    _name = f"{__name__}.{_m}"
    _mod = ModuleType(_name)
    # copy attributes to the new module object
    _mod.__dict__.update(_orig.__dict__)
    # register the synthetic submodule in sys.modules so normal imports work
    sys.modules[_name] = _mod
    # expose as attribute on the package (optional convenience)
    globals()[_m] = _mod
