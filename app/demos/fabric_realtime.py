"""
Real-time Operations Agent Demo
Demonstrates Fabric integration for operational monitoring.
"""
import os
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FabricTool, ListSortOrder

from config import settings
from utils.logging_config import logger


async def run_realtime_ops_demo(query: str = "What is the current system health status?"):
    """
    Run real-time operations demo with Fabric integration.
    
    Args:
        query: The operational question to ask
    
    Returns:
        Dict with response and metadata
    """
    try:
        logger.info(f"⚡ Starting Real-time Operations Demo")
        logger.info(f"📝 Query: {query}")
        
        # Initialize project client
        credential = DefaultAzureCredential()
        project_client = AIProjectClient(
            endpoint=settings.project_endpoint,
            credential=credential
        )
        
        with project_client:
            # Check if Fabric connection is configured
            if not settings.fabric_connection_id or "{" in settings.fabric_connection_id:
                logger.warning("⚠️  Fabric connection not configured. Using mock response.")
                return {
                    "success": False,
                    "message": "Fabric connection not configured. Please set FABRIC_CONNECTION_ID in .env",
                    "response": "Unable to query operational data without Fabric connection."
                }
            
            # Create Fabric tool
            fabric_tool = FabricTool(connection_id=settings.fabric_connection_id)
            
            # Create Real-time Operations Agent
            agent = project_client.agents.create_agent(
                model=settings.model_deployment_name,
                name="realtime-ops-agent",
                instructions="""You are a Real-time Operations Agent with access to operational data in Microsoft Fabric.
                
                Your capabilities:
                - Monitor system health and performance metrics
                - Query real-time operational data and KPIs
                - Analyze alerts and incidents
                - Track SLA compliance and uptime
                - Identify performance bottlenecks
                - Provide operational insights and recommendations
                
                When answering questions:
                1. Use the Fabric tool to query real-time data
                2. Provide current status and recent trends
                3. Highlight any critical issues or anomalies
                4. Include specific metrics (response times, error rates, etc.)
                5. Recommend actions for improvement
                6. Use urgency indicators (🟢 Normal, 🟡 Warning, 🔴 Critical)
                """,
                tools=fabric_tool.definitions,
                headers={"x-ms-enable-preview": "true"}
            )
            
            logger.info(f"✅ Created agent: {agent.id}")
            
            # Create conversation thread
            thread = project_client.agents.threads.create()
            logger.info(f"📝 Created thread: {thread.id}")
            
            # Send query
            project_client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=query
            )
            
            # Run agent
            logger.info("🤖 Running agent...")
            run = project_client.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=agent.id
            )
            
            # Check status
            if run.status == "failed":
                logger.error(f"❌ Run failed: {run.last_error}")
                return {
                    "success": False,
                    "error": str(run.last_error),
                    "agent_id": agent.id,
                    "thread_id": thread.id
                }
            
            # Get response
            messages = project_client.agents.messages.list(
                thread_id=thread.id,
                order=ListSortOrder.ASCENDING
            )
            
            response_text = ""
            for message in messages:
                if message.run_id == run.id and message.text_messages:
                    response_text = message.text_messages[-1].text.value
                    break
            
            logger.info("✅ Real-time operations analysis complete")
            
            return {
                "success": True,
                "query": query,
                "response": response_text,
                "agent_id": agent.id,
                "thread_id": thread.id,
                "run_id": run.id,
                "fabric_endpoint": settings.fabric_realtime_agent_endpoint
            }
    
    except Exception as e:
        logger.error(f"❌ Real-time ops demo failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Example queries for testing
EXAMPLE_QUERIES = [
    "What is the current system health status?",
    "Show me recent alerts and incidents",
    "What is the current error rate?",
    "Are there any performance degradations?",
    "What is the average response time?",
    "Show me active incidents requiring attention",
    "What are the top errors in the last hour?",
    "Is the system meeting SLA targets?",
    "Show me resource utilization trends",
]


if __name__ == "__main__":
    import asyncio
    
    # Run demo with example query
    result = asyncio.run(run_realtime_ops_demo(EXAMPLE_QUERIES[0]))
    
    print("\n" + "="*60)
    print("REAL-TIME OPERATIONS DEMO RESULTS")
    print("="*60)
    print(f"\nQuery: {result.get('query', 'N/A')}")
    print(f"\nResponse:\n{result.get('response', 'No response')}")
    print(f"\nAgent ID: {result.get('agent_id', 'N/A')}")
    print("="*60)
