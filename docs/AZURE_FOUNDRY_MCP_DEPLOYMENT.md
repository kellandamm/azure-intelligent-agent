# Azure AI Foundry + MCP Server Deployment Guide

## Overview

This guide explains how to deploy the application using **Azure AI Foundry agents** with an **MCP (Model Context Protocol) server** architecture instead of the Agent Framework.

## Architecture

- **Main App**: FastAPI application using Azure AI Foundry native agents
- **MCP Server**: Centralized function calling service (internal only)
- **Deployment**: Azure Container Apps (reuses existing infrastructure)

## Prerequisites

1. Azure AI Foundry project with agents created
2. Existing Container Apps environment (configure your environment name)
3. Azure Container Registry (configure your ACR name)

## Deployment Options

### Option 1: Reuse Existing Infrastructure (Recommended)

Uses your existing Container Apps environment and Container Registry.

**Bicep Template**: `bicep/main-foundry-mcp.bicep`

**Cost**: ~$30/month (only 2 new container apps)

### Option 2: New Infrastructure

Creates new resource group with all new resources.

**Cost**: ~$80/month

## Quick Deployment

1. **Create agents in Azure AI Foundry portal** (ai.azure.com)
2. **Configure environment**:
   ```powershell
   cd <your-repo-path>
   azd env new production
   azd env set AZURE_LOCATION eastus2
   azd env set PROJECT_ENDPOINT "<your-foundry-endpoint>"
   azd env set PROJECT_CONNECTION_STRING "<your-connection-string>"
   azd env set FABRIC_ORCHESTRATOR_AGENT_ID "<agent-id>"
   # ... set other agent IDs
   ```

3. **Deploy**:
   ```powershell
   azd up
   ```

## Key Files

- `app/app/azure_foundry_agent_manager.py` - Azure AI Foundry agent manager
- `app/mcp_server_app.py` - MCP server for function calling
- `app/app/config.py` - Configuration with MCP settings
- `app/Dockerfile.mcp` - MCP server container definition
- `bicep/main-foundry-mcp.bicep` - Infrastructure template

## Configuration

Add to your `.env` or Azure App Settings:

```env
# Azure AI Foundry
PROJECT_ENDPOINT=https://your-project.services.ai.azure.com/api/projects/your-project
PROJECT_CONNECTION_STRING=your-connection-string

# MCP Server
ENABLE_MCP=true
MCP_SERVER_HOST=mcp-server
MCP_SERVER_PORT=3000

# Agent IDs (from Azure AI Foundry portal)
FABRIC_ORCHESTRATOR_AGENT_ID=asst_xxxxx
FABRIC_SALES_AGENT_ID=asst_xxxxx
FABRIC_REALTIME_AGENT_ID=asst_xxxxx
```

## Benefits vs Agent Framework

1. ✅ Native Azure AI Foundry integration
2. ✅ Centralized function calling via MCP
3. ✅ Better scalability and monitoring
4. ✅ Simplified agent management
5. ✅ Lower latency for tool execution

## Migration

See the agentsdemos folder for complete migration guide from Agent Framework to Azure AI Foundry + MCP.

## Monitoring

- Application Insights (reused from existing)
- Container App logs: `azd logs`
- Azure Portal: Monitor both container apps

## Troubleshooting

### MCP Server Not Responding
- Check internal DNS resolution
- Verify MCP container is running
- Check logs: `azd logs mcp-server`

### Agents Not Working
- Verify agent IDs in configuration
- Check PROJECT_CONNECTION_STRING is set
- Ensure agents exist in Azure AI Foundry portal
