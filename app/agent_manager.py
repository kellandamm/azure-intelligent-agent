from dataclasses import asdict
from config_runtime import load_runtime_config, AppRuntimeConfig


class AgentManager:
    def __init__(self):
        self.config = load_runtime_config()
        self.client = None
        self.backend = 'standard'
        self._initialize()

    def _initialize(self):
        self.client = None
        self.backend = self.config.chat_backend_mode

        if self.backend == 'foundry' and self.config.use_foundry_agents:
            if not self.config.foundry_project_endpoint or not self.config.fabric_project_connection_name:
                self.backend = 'standard'
                return
            self.client = {
                'project_endpoint': self.config.foundry_project_endpoint,
                'fabric_connection': self.config.fabric_project_connection_name,
                'deployment_name': self.config.foundry_model_deployment_name,
            }

    def reload(self):
        self.config = load_runtime_config()
        self._initialize()
        return self.status()

    def set_chat_backend_mode(self, mode: str):
        mode = (mode or 'standard').strip().lower()
        if mode not in {'standard', 'foundry'}:
            raise ValueError('Invalid mode')
        import os
        os.environ['CHAT_BACKEND_MODE'] = mode
        if mode == 'foundry':
            os.environ['USE_FOUNDRY_AGENTS'] = 'true'
        self.config = load_runtime_config()
        self._initialize()
        return self.status()

    def status(self):
        return {
            'analytics_mode': self.config.analytics_mode,
            'chat_backend_mode': self.backend,
            'use_foundry_agents': self.config.use_foundry_agents,
            'foundry_client_initialized': self.client is not None,
            'config': asdict(self.config),
        }
