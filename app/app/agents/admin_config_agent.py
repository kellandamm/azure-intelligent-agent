"""
Admin Configuration Agent - Manages agents, app settings, and infrastructure via natural language
"""
from typing import Dict, Any, List, Optional
import json
import os
import yaml
from pathlib import Path
from datetime import datetime

from agent_framework.azure import AzureOpenAIChatClient
from agent_framework._types import ChatMessage, TextContent
from azure.identity import DefaultAzureCredential

from config import settings
from utils.db_connection import DatabaseConnection
from utils.logging_config import logger


class AdminConfigAgent:
    """Agent for managing system configurations via natural language"""
    
    CONFIG_PATHS = {
        "agents": "agent_configs.json",
        "app": "config/app_config.json",
        "infrastructure": "infrastructure/config.yaml",
    }
    
    def __init__(self, user_id: str, db: DatabaseConnection):
        self.user_id = user_id
        self.db = db
        
        # Initialize LLM client for intent parsing
        self.credential = DefaultAzureCredential()
        self.llm_client = AzureOpenAIChatClient(
            endpoint=settings.azure_openai_endpoint,
            deployment_name=settings.azure_openai_deployment,
            credential=self.credential,
            api_version=settings.azure_openai_api_version,
        )
    
    async def process_request(self, request: str) -> Dict[str, Any]:
        """
        Process natural language configuration requests
        
        Examples:
        # Agent Management
        - "Update SalesAssistant's display name to 'Sales Expert'"
        - "Add web_search tool to AnalyticsAssistant agent"
        - "Disable the FinancialAdvisor agent"
        
        # App Configuration
        - "Change the max request timeout to 120 seconds"
        - "Enable debug logging"
        - "Update the API rate limit to 1000 requests per hour"
        
        # Infrastructure
        - "Scale the web app to 3 instances"
        - "Update the database tier to P2"
        - "Enable auto-scaling with min 2 and max 10 instances"
        """
        try:
            intent = await self._parse_intent_with_ai(request)
            logger.info(f"Parsed intent: {intent}")
            
            # Route to appropriate handler
            if intent.get("category") == "agent":
                return await self._handle_agent_config(intent)
            elif intent.get("category") == "app":
                return await self._handle_app_config(intent)
            elif intent.get("category") == "infrastructure":
                return await self._handle_infrastructure_config(intent)
            elif intent.get("category") == "list":
                return await self._list_configurations(intent.get("target"))
            else:
                return {
                    "success": False,
                    "message": "I couldn't determine the configuration category. Please specify: agent, app, or infrastructure."
                }
        except Exception as e:
            logger.error(f"Error processing config request: {e}")
            return {
                "success": False,
                "message": f"Error processing request: {str(e)}"
            }
    
    async def _parse_intent_with_ai(self, request: str) -> Dict[str, Any]:
        """Use LLM to parse natural language intent with proper structure"""
        
        system_prompt = """You are a configuration parser. Analyze the user's request and extract:
1. category: "agent", "app", "infrastructure", or "list"
2. action: "update", "add", "remove", "enable", "disable", "scale", "list"
3. target: the specific component being modified (agent name like "sales", "analytics", "financial", etc.)
4. parameters: key-value pairs of changes

Return ONLY valid JSON with these fields."""
        
        user_prompt = f"""Parse this configuration request:
"{request}"

Return JSON with: category, action, target, parameters

Examples:
- "Update SalesAssistant to focus on Azure" -> {{"category": "agent", "action": "update", "target": "sales", "parameters": {{"prompt_modification": "focus on Azure"}}}}
- "Disable analytics agent" -> {{"category": "agent", "action": "disable", "target": "analytics", "parameters": {{}}}}
- "List all agents" -> {{"category": "list", "action": "list", "target": "agents", "parameters": {{}}}}
"""
        
        try:
            messages = [
                ChatMessage(role="system", content=[TextContent(text=system_prompt)]),
                ChatMessage(role="user", content=[TextContent(text=user_prompt)])
            ]
            
            response = await self.llm_client.get_chat_completion(
                messages=messages,
                response_format={"type": "json_object"}
            )
            
            # Extract text from response
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if isinstance(content, list):
                    text = "".join([c.text for c in content if hasattr(c, 'text')])
                else:
                    text = str(content)
                
                return json.loads(text)
        except Exception as e:
            logger.warning(f"AI parsing failed, using fallback: {e}")
        
        # Fallback to keyword parsing
        return self._fallback_parse(request)
    
    def _fallback_parse(self, request: str) -> Dict[str, Any]:
        """Fallback parser using keywords"""
        request_lower = request.lower()
        
        intent = {
            "category": None,
            "action": None,
            "target": None,
            "parameters": {}
        }
        
        # Determine category
        agent_keywords = ["agent", "sales", "analytics", "financial", "operations", "support", "techexpert", "businessintel", "deepdive"]
        app_keywords = ["app", "application", "timeout", "logging", "rate limit", "config"]
        infra_keywords = ["infrastructure", "scale", "database", "instances", "tier", "azure"]
        
        if any(word in request_lower for word in agent_keywords):
            intent["category"] = "agent"
            # Try to extract agent target
            for keyword in ["sales", "analytics", "financial", "operations", "support"]:
                if keyword in request_lower:
                    intent["target"] = keyword
                    break
        elif any(word in request_lower for word in app_keywords):
            intent["category"] = "app"
            intent["target"] = "application"
        elif any(word in request_lower for word in infra_keywords):
            intent["category"] = "infrastructure"
            intent["target"] = "azure_resources"
        elif "list" in request_lower or "show" in request_lower:
            intent["category"] = "list"
            if "agent" in request_lower:
                intent["target"] = "agents"
        
        # Determine action
        if "update" in request_lower or "change" in request_lower or "modify" in request_lower:
            intent["action"] = "update"
        elif "add" in request_lower:
            intent["action"] = "add"
        elif "remove" in request_lower or "delete" in request_lower:
            intent["action"] = "remove"
        elif "enable" in request_lower or "turn on" in request_lower or "activate" in request_lower:
            intent["action"] = "enable"
        elif "disable" in request_lower or "turn off" in request_lower or "deactivate" in request_lower:
            intent["action"] = "disable"
        elif "scale" in request_lower:
            intent["action"] = "scale"
        elif "list" in request_lower or "show" in request_lower:
            intent["action"] = "list"
        
        return intent
    
    # ==================== AGENT CONFIGURATION ====================
    
    async def _handle_agent_config(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent configuration changes"""
        if intent["action"] == "update":
            return await self._update_agent_config(
                intent["target"],
                intent.get("parameters", {})
            )
        elif intent["action"] == "add":
            tool_name = intent.get("parameters", {}).get("tool_name")
            if tool_name:
                return await self._add_tool_to_agent(intent["target"], tool_name)
            return {"success": False, "message": "No tool specified to add"}
        elif intent["action"] in ["enable", "disable"]:
            return await self._toggle_agent(
                intent["target"],
                intent["action"] == "enable"
            )
        else:
            return {"success": False, "message": f"Unknown action: {intent['action']}"}
    
    async def _update_agent_config(
        self,
        agent_key: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update agent configuration"""
        try:
            configs = self._load_agent_configs()
            
            if agent_key not in configs:
                return {
                    "success": False,
                    "message": f"Agent '{agent_key}' not found. Available agents: {', '.join(configs.keys())}"
                }
            
            old_config = configs[agent_key].copy()
            
            # Apply updates
            for key, value in updates.items():
                if key in ["display_name", "prompt", "model", "tools", "is_active"]:
                    configs[agent_key][key] = value
                elif key == "prompt_modification":
                    # Append to existing prompt
                    current_prompt = configs[agent_key].get("prompt", "")
                    configs[agent_key]["prompt"] = f"{current_prompt}\n\nAdditional focus: {value}"
            
            # Save changes
            self._save_agent_configs(configs)
            
            # Log change
            self._log_configuration_change(
                category="agent",
                target=agent_key,
                old_config=old_config,
                new_config=configs[agent_key],
                change_summary=f"Updated agent: {', '.join(updates.keys())}"
            )
            
            return {
                "success": True,
                "message": f"✅ Successfully updated agent '{agent_key}'",
                "changes": updates,
                "new_config": configs[agent_key]
            }
            
        except Exception as e:
            logger.error(f"Error updating agent config: {e}")
            return {
                "success": False,
                "message": f"Error updating agent: {str(e)}"
            }
    
    async def _toggle_agent(self, agent_key: str, enabled: bool) -> Dict[str, Any]:
        """Enable or disable an agent"""
        return await self._update_agent_config(
            agent_key,
            {"is_active": enabled}
        )
    
    async def _add_tool_to_agent(self, agent_key: str, tool_name: str) -> Dict[str, Any]:
        """Add a tool to an agent"""
        try:
            configs = self._load_agent_configs()
            
            if agent_key not in configs:
                return {"success": False, "message": f"Agent '{agent_key}' not found"}
            
            current_tools = configs[agent_key].get("tools", [])
            
            if tool_name in current_tools:
                return {
                    "success": False,
                    "message": f"Tool '{tool_name}' already exists on {agent_key}"
                }
            
            old_config = configs[agent_key].copy()
            configs[agent_key]["tools"] = current_tools + [tool_name]
            
            self._save_agent_configs(configs)
            
            self._log_configuration_change(
                category="agent",
                target=agent_key,
                old_config=old_config,
                new_config=configs[agent_key],
                change_summary=f"Added tool '{tool_name}'"
            )
            
            return {
                "success": True,
                "message": f"✅ Added {tool_name} to {agent_key}",
                "tools": configs[agent_key]["tools"]
            }
            
        except Exception as e:
            logger.error(f"Error adding tool: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    # ==================== APP CONFIGURATION ====================
    
    async def _handle_app_config(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle application configuration changes"""
        try:
            config_path = Path(self.CONFIG_PATHS["app"])
            
            if not config_path.exists():
                # Create default config
                default_config = self._get_default_app_config()
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            old_config = config.copy()
            
            # Apply changes based on parameters
            params = intent.get("parameters", {})
            
            if "timeout" in params:
                config["request_timeout"] = int(params["timeout"])
            if "debug" in params:
                config["logging"]["level"] = "DEBUG" if params["debug"] else "INFO"
            if "rate_limit" in params:
                config["rate_limiting"]["requests_per_hour"] = int(params["rate_limit"])
            if "max_tokens" in params:
                config["llm"]["max_tokens"] = int(params["max_tokens"])
            if "temperature" in params:
                config["llm"]["temperature"] = float(params["temperature"])
            
            # Save updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self._log_configuration_change(
                category="app",
                target="application",
                old_config=old_config,
                new_config=config,
                change_summary=f"Updated app config: {', '.join(params.keys())}"
            )
            
            return {
                "success": True,
                "message": "✅ Application configuration updated successfully",
                "changes": params,
                "new_config": config,
                "note": "⚠️ Restart the application for changes to take effect"
            }
            
        except Exception as e:
            logger.error(f"Error updating app config: {e}")
            return {
                "success": False,
                "message": f"Error updating app config: {str(e)}"
            }
    
    def _get_default_app_config(self) -> Dict[str, Any]:
        """Get default app configuration"""
        return {
            "request_timeout": 60,
            "logging": {
                "level": "INFO",
                "format": "json"
            },
            "rate_limiting": {
                "enabled": True,
                "requests_per_hour": 1000,
                "requests_per_minute": 100
            },
            "llm": {
                "default_model": "gpt-4o",
                "max_tokens": 4000,
                "temperature": 0.7,
                "timeout": 30
            },
            "security": {
                "require_auth": True,
                "session_timeout": 3600,
                "max_login_attempts": 5
            }
        }
    
    # ==================== INFRASTRUCTURE CONFIGURATION ====================
    
    async def _handle_infrastructure_config(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle infrastructure configuration changes"""
        try:
            config_path = Path(self.CONFIG_PATHS["infrastructure"])
            
            if not config_path.exists():
                # Create default infrastructure config
                default_config = self._get_default_infrastructure_config()
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, 'w') as f:
                    yaml.dump(default_config, f, default_flow_style=False)
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            old_config = config.copy()
            params = intent.get("parameters", {})
            
            # Apply infrastructure changes
            if intent["action"] == "scale":
                if "instances" in params:
                    config["app_service"]["sku"]["capacity"] = int(params["instances"])
                if "min_instances" in params:
                    config["app_service"]["auto_scaling"]["min_instances"] = int(params["min_instances"])
                if "max_instances" in params:
                    config["app_service"]["auto_scaling"]["max_instances"] = int(params["max_instances"])
            
            if "database_tier" in params:
                config["database"]["sku"]["tier"] = params["database_tier"]
            
            if "enable_auto_scaling" in params:
                config["app_service"]["auto_scaling"]["enabled"] = params["enable_auto_scaling"]
            
            # Save updated config
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            self._log_configuration_change(
                category="infrastructure",
                target="azure_resources",
                old_config=old_config,
                new_config=config,
                change_summary=f"Updated infrastructure: {', '.join(params.keys())}"
            )
            
            # Generate deployment command
            deployment_cmd = self._generate_deployment_command(config)
            
            return {
                "success": True,
                "message": "✅ Infrastructure configuration updated",
                "changes": params,
                "new_config": config,
                "deployment_command": deployment_cmd,
                "note": "⚠️ Run the deployment command to apply changes to Azure"
            }
            
        except Exception as e:
            logger.error(f"Error updating infrastructure: {e}")
            return {
                "success": False,
                "message": f"Error updating infrastructure: {str(e)}"
            }
    
    def _get_default_infrastructure_config(self) -> Dict[str, Any]:
        """Get default infrastructure configuration"""
        return {
            "app_service": {
                "name": "agentsdemo-webapp",
                "sku": {
                    "name": "P1v2",
                    "tier": "PremiumV2",
                    "capacity": 1
                },
                "auto_scaling": {
                    "enabled": False,
                    "min_instances": 1,
                    "max_instances": 5,
                    "rules": [
                        {
                            "metric": "CpuPercentage",
                            "threshold": 70,
                            "scale_action": "increase",
                            "scale_by": 1
                        }
                    ]
                }
            },
            "database": {
                "name": "agentsdemo-db",
                "sku": {
                    "name": "Standard",
                    "tier": "S1"
                }
            },
            "storage": {
                "name": "agentsdemo-storage",
                "sku": "Standard_LRS"
            }
        }
    
    def _generate_deployment_command(self, config: Dict[str, Any]) -> str:
        """Generate Azure CLI deployment command"""
        sku = config["app_service"]["sku"]
        app_name = config["app_service"]["name"]
        
        commands = [
            "# Apply infrastructure changes",
            f"az webapp update \\",
            f"  --resource-group agentsdemos-rg \\",
            f"  --name {app_name} \\",
            f"  --set sku.name={sku['name']} sku.capacity={sku['capacity']}"
        ]
        
        if config["app_service"]["auto_scaling"]["enabled"]:
            min_inst = config["app_service"]["auto_scaling"]["min_instances"]
            max_inst = config["app_service"]["auto_scaling"]["max_instances"]
            commands.append("")
            commands.append("# Configure auto-scaling")
            commands.append(f"az monitor autoscale create \\")
            commands.append(f"  --resource-group agentsdemos-rg \\")
            commands.append(f"  --resource-type Microsoft.Web/sites \\")
            commands.append(f"  --resource {app_name} \\")
            commands.append(f"  --min-count {min_inst} \\")
            commands.append(f"  --max-count {max_inst}")
        
        return "\n".join(commands)
    
    # ==================== LISTING & UTILITIES ====================
    
    async def _list_configurations(self, target: Optional[str] = None) -> Dict[str, Any]:
        """List current configurations"""
        result = {
            "success": True,
            "configurations": {}
        }
        
        if not target or target == "agents":
            result["configurations"]["agents"] = self._load_agent_configs()
        
        if not target or target == "app":
            try:
                config_path = Path(self.CONFIG_PATHS["app"])
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        result["configurations"]["app"] = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load app config: {e}")
        
        if not target or target == "infrastructure":
            try:
                config_path = Path(self.CONFIG_PATHS["infrastructure"])
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        result["configurations"]["infrastructure"] = yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Could not load infrastructure config: {e}")
        
        return result
    
    def _load_agent_configs(self) -> Dict[str, Any]:
        """Load agent configurations from file."""
        config_path = self.CONFIG_PATHS["agents"]
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
        
        # Load defaults if no config file exists
        from agent_framework_manager import AgentFrameworkManager
        manager = AgentFrameworkManager()
        configs = {}
        
        for key, profile in manager.specialist_profiles.items():
            configs[key] = {
                "agent_key": key,
                "display_name": profile.get("display_name", key.title()),
                "prompt": profile.get("prompt", ""),
                "tools": [],
                "is_active": True,
                "model": "gpt-4o",
            }
        
        return configs
    
    def _save_agent_configs(self, configs: Dict[str, Any]) -> None:
        """Save agent configurations to file."""
        config_path = self.CONFIG_PATHS["agents"]
        with open(config_path, "w") as f:
            json.dump(configs, f, indent=2)
    
    def _log_configuration_change(
        self,
        category: str,
        target: str,
        old_config: Dict[str, Any],
        new_config: Dict[str, Any],
        change_summary: str
    ):
        """Log configuration changes to database"""
        try:
            query = """
            INSERT INTO configuration_changes 
            (category, target, changed_by, old_config, new_config, change_summary, timestamp, rollback_available)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(
                query,
                (
                    category,
                    target,
                    self.user_id,
                    json.dumps(old_config),
                    json.dumps(new_config),
                    change_summary,
                    datetime.utcnow().isoformat(),
                    True
                )
            )
            logger.info(f"Logged configuration change: {change_summary}")
        except Exception as e:
            logger.error(f"Error logging configuration change: {e}")
