"""
Sales Intelligence Agent Demo
Demonstrates Fabric integration for sales data analysis.
"""
import os
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FabricTool, ListSortOrder

from config import settings
from utils.logging_config import logger


async def run_sales_intelligence_demo(query: str = "What are the top 5 products by revenue?"):
    """
    Run sales intelligence demo with Fabric integration.
    
    Args:
        query: The sales question to ask
    
    Returns:
        Dict with response and metadata
    """
    try:
        logger.info(f"🛒 Starting Sales Intelligence Demo")
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
                    "response": "Unable to query sales data without Fabric connection."
                }
            
            # Create Fabric tool
            fabric_tool = FabricTool(connection_id=settings.fabric_connection_id)
            
            # Create Sales Intelligence Agent
            agent = project_client.agents.create_agent(
                model=settings.model_deployment_name,
                name="sales-intelligence-agent",
                instructions="""You are a Sales Intelligence Agent with access to sales data in Microsoft Fabric.
                
                Your capabilities:
                - Query sales transactions and revenue data
                - Analyze product performance and trends
                - Provide customer insights and segmentation
                - Calculate key sales metrics (AOV, LTV, conversion rates)
                - Identify top performers and growth opportunities
                
                When answering questions:
                1. Use the Fabric tool to query the data
                2. Provide clear, data-driven insights
                3. Include specific numbers and percentages
                4. Highlight trends and patterns
                5. Offer actionable recommendations
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
            
            logger.info("✅ Sales intelligence analysis complete")
            
            return {
                "success": True,
                "query": query,
                "response": response_text,
                "agent_id": agent.id,
                "thread_id": thread.id,
                "run_id": run.id,
                "fabric_endpoint": settings.fabric_sales_agent_endpoint
            }
    
    except Exception as e:
        logger.error(f"❌ Sales intelligence demo failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Example queries for testing
EXAMPLE_QUERIES = [
    "What are the top 5 products by revenue this quarter?",
    "Show me sales trends over the last 6 months",
    "Which customers have the highest lifetime value?",
    "What is the average order value by region?",
    "Identify products with declining sales",
    "What are the best performing product categories?",
    "Show me year-over-year growth by product line",
    "Which sales channels are most profitable?",
]


if __name__ == "__main__":
    import asyncio
    
    # Run demo with example query
    result = asyncio.run(run_sales_intelligence_demo(EXAMPLE_QUERIES[0]))
    
    print("\n" + "="*60)
    print("SALES INTELLIGENCE DEMO RESULTS")
    print("="*60)
    print(f"\nQuery: {result.get('query', 'N/A')}")
    print(f"\nResponse:\n{result.get('response', 'No response')}")
    print(f"\nAgent ID: {result.get('agent_id', 'N/A')}")
    print("="*60)
