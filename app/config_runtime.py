import os
from dataclasses import dataclass


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {'1', 'true', 'yes', 'y', 'on'}


@dataclass
class AppRuntimeConfig:
    analytics_mode: str
    chat_backend_mode: str
    use_foundry_agents: bool
    foundry_project_endpoint: str
    fabric_project_connection_name: str
    foundry_model_deployment_name: str


def load_runtime_config() -> AppRuntimeConfig:
    analytics_mode = os.getenv('ANALYTICS_MODE', 'sql').strip().lower()
    if analytics_mode not in {'sql', 'fabric', 'auto'}:
        analytics_mode = 'sql'

    chat_backend_mode = os.getenv('CHAT_BACKEND_MODE', 'standard').strip().lower()
    if chat_backend_mode not in {'standard', 'foundry'}:
        chat_backend_mode = 'standard'

    use_foundry_agents = _as_bool(os.getenv('USE_FOUNDRY_AGENTS'), False)

    if chat_backend_mode == 'foundry' and not use_foundry_agents:
        use_foundry_agents = True

    return AppRuntimeConfig(
        analytics_mode=analytics_mode,
        chat_backend_mode=chat_backend_mode,
        use_foundry_agents=use_foundry_agents,
        foundry_project_endpoint=os.getenv('FOUNDRY_PROJECT_ENDPOINT', os.getenv('PROJECT_ENDPOINT', '')).strip(),
        fabric_project_connection_name=os.getenv('FABRIC_PROJECT_CONNECTION_NAME', '').strip(),
        foundry_model_deployment_name=os.getenv('FOUNDRY_MODEL_DEPLOYMENT_NAME', '').strip(),
    )
