# App runtime update

## Goals

- Support `sql`, `fabric`, and `auto` analytics modes.
- Support `standard` and `foundry` chat backend modes.
- Prevent startup/runtime failures when Foundry is disabled.
- Make optional environment variables required only for the modes that actually use them.

## Recommended runtime pattern

1. Load configuration through a single runtime config object.
2. Normalize invalid values back to safe defaults.
3. Initialize Foundry clients only when `CHAT_BACKEND_MODE=foundry` and required settings are present.
4. Fall back to `standard` mode if Foundry settings are incomplete.
5. Support backend reload/reinitialize on mode changes.

## Suggested files

- `app/config_runtime.py`
- `app/agent_manager.py`
- `.env.example`

## Expected behavior

- `ANALYTICS_MODE=sql`: app uses SQL live analytics.
- `ANALYTICS_MODE=fabric`: app uses Fabric reporting path.
- `ANALYTICS_MODE=auto`: app prefers Fabric and can fall back to SQL.
- `CHAT_BACKEND_MODE=standard`: no Foundry client required.
- `CHAT_BACKEND_MODE=foundry`: initialize Foundry client only when required settings exist.

## Smoke tests

- Start app with base settings only.
- Switch to `CHAT_BACKEND_MODE=foundry` with missing settings and confirm safe fallback.
- Switch to `CHAT_BACKEND_MODE=foundry` with full settings and confirm client initialization.
- Confirm `USE_FOUNDRY_AGENTS=false` does not break standard mode.
