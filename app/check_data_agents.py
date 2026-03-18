"""
Quick Data Agent Configuration Checker

Verifies that Data Agents are properly enabled and configured.
Run this BEFORE deploying to identify configuration issues.
"""

import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings


def check_data_agent_config():
    """Check if Data Agents are properly configured."""
    print("\n" + "="*80)
    print("🔍 Data Agent Configuration Check")
    print("="*80 + "\n")
    
    issues = []
    warnings = []
    
    # Check enable_data_agents flag
    print(f"1. enable_data_agents: {settings.enable_data_agents}")
    if not settings.enable_data_agents:
        issues.append("❌ ENABLE_DATA_AGENTS is False - Data Agents are DISABLED")
        print("   ❌ Data Agents are DISABLED")
        print("   💡 Set ENABLE_DATA_AGENTS=true in environment or .env file")
    else:
        print("   ✅ Data Agents are ENABLED")
    
    # Check AI Foundry endpoint
    print(f"\n2. ai_foundry_project_endpoint: {settings.ai_foundry_project_endpoint or 'NOT SET'}")
    if not settings.ai_foundry_project_endpoint:
        issues.append("❌ AI_FOUNDRY_PROJECT_ENDPOINT not configured")
        print("   ❌ AI Foundry endpoint not configured")
        print("   💡 Set AI_FOUNDRY_PROJECT_ENDPOINT in environment")
    else:
        print("   ✅ AI Foundry endpoint configured")
    
    # Check Fabric lakehouse ID
    print(f"\n3. fabric_lakehouse_id: {settings.fabric_lakehouse_id or 'NOT SET'}")
    if not settings.fabric_lakehouse_id:
        issues.append("❌ FABRIC_LAKEHOUSE_ID not configured")
        print("   ❌ Fabric lakehouse ID not configured")
        print("   💡 Set FABRIC_LAKEHOUSE_ID in environment")
    else:
        print("   ✅ Fabric lakehouse ID configured")
    
    # Check lakehouse name
    print(f"\n4. fabric_lakehouse_name: {settings.fabric_lakehouse_name}")
    if settings.fabric_lakehouse_name == "RetailData":
        warnings.append("⚠️ Using default lakehouse name 'RetailData'")
        print("   ⚠️ Using default name 'RetailData' - verify this matches your actual lakehouse")
    else:
        print("   ✅ Custom lakehouse name configured")
    
    # Check workspace ID
    print(f"\n5. fabric_workspace_id: {settings.fabric_workspace_id or 'NOT SET'}")
    if not settings.fabric_workspace_id:
        issues.append("❌ FABRIC_WORKSPACE_ID not configured")
        print("   ❌ Fabric workspace ID not configured")
    else:
        print("   ✅ Fabric workspace ID configured")
    
    # Summary
    print("\n" + "="*80)
    print("📊 Configuration Summary")
    print("="*80 + "\n")
    
    if not issues:
        print("✅ All required Data Agent settings are configured!")
        print("\n🎯 Next Steps:")
        print("   1. Run diagnostic_fabric_schema.py to verify Fabric tables exist")
        print("   2. Deploy updated code with enhanced prompts")
        print("   3. Test with churn analysis query")
        return True
    else:
        print("❌ Configuration Issues Found:\n")
        for issue in issues:
            print(f"   {issue}")
        
        if warnings:
            print("\n⚠️ Warnings:\n")
            for warning in warnings:
                print(f"   {warning}")
        
        print("\n🔧 Required Actions:")
        print("   1. Set missing environment variables (see .env.example)")
        print("   2. Update Azure App Service Configuration (App Settings)")
        print("   3. Re-run this check to verify")
        
        print("\n📝 Example Configuration:")
        print("   ENABLE_DATA_AGENTS=true")
        print("   AI_FOUNDRY_PROJECT_ENDPOINT=https://demosaifoundry9257402771.services.ai.azure.com")
        print("   FABRIC_LAKEHOUSE_ID=gnnfqtdugxjufbvicpl3lq3pry-27sz7dcjnoiudkp5nxvymivegm")
        print("   FABRIC_WORKSPACE_ID=8c9fe5d7-6b49-4191-a9fd-6deb8622a433")
        print("   FABRIC_LAKEHOUSE_NAME=GoldLakehouse")
        
        return False


def show_current_config():
    """Show current configuration values."""
    print("\n" + "="*80)
    print("⚙️ Current Configuration Values")
    print("="*80 + "\n")
    
    config_items = [
        ("ENABLE_DATA_AGENTS", settings.enable_data_agents),
        ("AI_FOUNDRY_PROJECT_ENDPOINT", settings.ai_foundry_project_endpoint),
        ("FABRIC_LAKEHOUSE_ID", settings.fabric_lakehouse_id),
        ("FABRIC_LAKEHOUSE_NAME", settings.fabric_lakehouse_name),
        ("FABRIC_WORKSPACE_ID", settings.fabric_workspace_id),
        ("AZURE_OPENAI_ENDPOINT", settings.azure_openai_endpoint),
        ("AZURE_OPENAI_DEPLOYMENT", settings.azure_openai_deployment),
    ]
    
    for key, value in config_items:
        # Truncate long values
        str_value = str(value) if value is not None else "NOT SET"
        if len(str_value) > 60:
            str_value = str_value[:57] + "..."
        
        print(f"  {key:<35} = {str_value}")


def check_agent_tool_config():
    """Check if agents are configured to use Data Agent tools."""
    print("\n" + "="*80)
    print("🤖 Agent Tool Configuration")
    print("="*80 + "\n")
    
    from agent_framework_manager import AgentFrameworkManager
    
    # Create manager (won't fail even if Data Agents disabled)
    manager = AgentFrameworkManager()
    
    # Check specialist profiles
    specialists_with_data_agents = []
    specialists_without_data_agents = []
    
    for specialist_name, profile in manager.specialist_profiles.items():
        tools = profile.get("tools", [])
        
        # Check if using Data Agent tools
        has_data_agent = any(
            isinstance(tool, dict) and tool.get("type") == "fabric_data_agent"
            for tool in tools
        )
        
        if has_data_agent:
            specialists_with_data_agents.append(specialist_name)
            print(f"  ✅ {specialist_name:<25} - Using Data Agents")
        else:
            specialists_without_data_agents.append(specialist_name)
            print(f"  ⚠️ {specialist_name:<25} - Using mock data tools")
    
    print(f"\n📊 Summary:")
    print(f"   Agents with Data Agents: {len(specialists_with_data_agents)}")
    print(f"   Agents with mock tools: {len(specialists_without_data_agents)}")
    
    if not settings.enable_data_agents:
        print("\n💡 Data Agents are DISABLED - all agents will use mock data tools")
        print("   Enable Data Agents to allow real Fabric queries")


if __name__ == "__main__":
    print("\n" + "🔎 Data Agent Configuration Diagnostic Tool" + "\n")
    
    # Show current config
    show_current_config()
    
    # Check configuration
    config_ok = check_data_agent_config()
    
    # Check agent tools if config is okay
    if config_ok:
        try:
            check_agent_tool_config()
        except Exception as e:
            print(f"\n⚠️ Could not check agent tool configuration: {e}")
    
    print("\n" + "="*80)
    print("✅ Diagnostic Complete")
    print("="*80 + "\n")
    
    if not config_ok:
        print("❌ Fix configuration issues before deploying\n")
        sys.exit(1)
    else:
        print("✅ Configuration looks good! Ready to deploy.\n")
        sys.exit(0)
