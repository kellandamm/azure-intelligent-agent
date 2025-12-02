"""
AI Shopping Agents for E-Commerce Demo.
Powered by Azure OpenAI for intelligent product discovery and recommendations.
"""
from typing import List, Dict, Any, Optional
import logging
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from config import settings
from utils.db_connection import DatabaseConnection

logger = logging.getLogger(__name__)


class ProductDiscoveryAgent:
    """
    AI Agent for natural language product search and discovery.
    Translates user queries into database searches and provides recommendations.
    """
    
    def __init__(self):
        """Initialize the product discovery agent with Azure OpenAI."""
        # Use DefaultAzureCredential for managed identity / Azure CLI auth
        from azure.identity import DefaultAzureCredential
        
        self.client = ChatCompletionsClient(
            endpoint=settings.azure_openai_endpoint,
            credential=DefaultAzureCredential()
        )
        self.model = settings.azure_openai_deployment
        
        self.system_prompt = """You are an expert shopping assistant helping customers find products.

Your role:
1. Understand customer needs from natural language queries
2. Extract search criteria (category, price range, features)
3. Provide personalized product recommendations
4. Answer product questions with detailed information

You have access to a product catalog with:
- Categories: Electronics, Clothing, Home & Garden, Sports & Outdoors, Books, Toys & Games, Health & Beauty, Food & Beverage, Automotive, Office Supplies
- Products with names, descriptions, prices, and stock quantities

When a customer asks about products:
1. Identify the category or search terms
2. Extract price constraints if mentioned
3. Note any specific features or requirements
4. Provide relevant, helpful responses

Be conversational, helpful, and focus on customer satisfaction."""
    
    def parse_query(self, user_query: str) -> Dict[str, Any]:
        """
        Parse natural language query into search parameters using AI.
        
        Args:
            user_query: Customer's natural language question/request
            
        Returns:
            Dictionary with search_terms, category, min_price, max_price
        """
        try:
            parse_prompt = f"""Analyze this customer query and extract search parameters:
"{user_query}"

Return ONLY a JSON object with these fields (set to null if not mentioned):
{{
    "search_terms": "key words to search for",
    "category": "product category name (Electronics, Clothing, etc.)",
    "min_price": numeric value or null,
    "max_price": numeric value or null,
    "intent": "browse|search|compare|recommend"
}}

Examples:
- "Show me laptops under $1000" → {{"search_terms": "laptop", "category": "Electronics", "max_price": 1000, "intent": "search"}}
- "Looking for running shoes" → {{"search_terms": "running shoes", "category": "Sports & Outdoors", "intent": "search"}}
- "What's on sale in electronics?" → {{"category": "Electronics", "intent": "browse"}}

JSON:"""
            
            response = self.client.complete(
                messages=[
                    SystemMessage(content="You extract search parameters from queries. Respond ONLY with valid JSON."),
                    UserMessage(content=parse_prompt)
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            result_text = result_text.strip()
            
            params = json.loads(result_text)
            logger.info(f"Parsed query: {params}")
            return params
            
        except Exception as e:
            logger.error(f"Error parsing query: {e}")
            # Fallback: simple keyword extraction
            return {
                "search_terms": user_query,
                "category": None,
                "min_price": None,
                "max_price": None,
                "intent": "search"
            }
    
    def search_products(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search products in Fabric SQL database based on parsed parameters.
        
        Args:
            query_params: Dictionary with search_terms, category, price filters
            
        Returns:
            List of matching products
        """
        try:
            db = DatabaseConnection(
                settings.database_connection_string,
                use_access_token=settings.sql_use_azure_auth
            )
            
            # Build query
            sql = """
                SELECT TOP 10
                    p.ProductID, p.ProductName, p.Price, p.StockQuantity,
                    p.Description, p.SKU, c.CategoryName
                FROM dbo.Products p
                INNER JOIN dbo.Categories c ON p.CategoryID = c.CategoryID
                WHERE p.IsActive = 1
            """
            params = []
            
            # Add filters
            if query_params.get("search_terms"):
                sql += " AND (p.ProductName LIKE ? OR p.Description LIKE ?)"
                search_term = f"%{query_params['search_terms']}%"
                params.extend([search_term, search_term])
            
            if query_params.get("category"):
                sql += " AND c.CategoryName LIKE ?"
                params.append(f"%{query_params['category']}%")
            
            if query_params.get("min_price"):
                sql += " AND p.Price >= ?"
                params.append(query_params["min_price"])
            
            if query_params.get("max_price"):
                sql += " AND p.Price <= ?"
                params.append(query_params["max_price"])
            
            sql += " AND p.StockQuantity > 0 ORDER BY p.ProductName"
            
            results = db.execute_query(sql, tuple(params) if params else None)
            return results or []
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    def generate_response(self, user_query: str, products: List[Dict[str, Any]]) -> str:
        """
        Generate natural language response about found products.
        
        Args:
            user_query: Original customer query
            products: List of matching products
            
        Returns:
            Conversational response with product recommendations
        """
        try:
            if not products:
                return "I couldn't find any products matching your criteria. Could you try different search terms or check out our featured products?"
            
            # Format products for the AI
            products_text = "\n".join([
                f"- {p['ProductName']} (${p['Price']:.2f}) - {p['Description'][:100] if p.get('Description') else 'No description'} [Stock: {p['StockQuantity']}]"
                for p in products[:5]  # Limit to top 5
            ])
            
            prompt = f"""Customer asked: "{user_query}"

Found {len(products)} matching products:
{products_text}

Provide a helpful, conversational response that:
1. Acknowledges their request
2. Highlights 2-3 best matches with key features
3. Mentions price ranges
4. Offers to help with more details or comparisons

Keep it concise (3-4 sentences) and friendly."""
            
            response = self.client.complete(
                messages=[
                    SystemMessage(content=self.system_prompt),
                    UserMessage(content=prompt)
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Fallback response
            product_names = [p["ProductName"] for p in products[:3]]
            return f"I found {len(products)} products for you: {', '.join(product_names)}. Would you like more details about any of these?"
    
    async def answer_query(self, user_query: str) -> Dict[str, Any]:
        """
        Main method: Answer customer query with product recommendations.
        
        Args:
            user_query: Customer's natural language question
            
        Returns:
            Dictionary with response text and matching products
        """
        try:
            logger.info(f"Product Discovery Agent processing: {user_query}")
            
            # Step 1: Parse query
            query_params = self.parse_query(user_query)
            
            # Step 2: Search products
            products = self.search_products(query_params)
            
            # Step 3: Generate response
            response_text = self.generate_response(user_query, products)
            
            return {
                "response": response_text,
                "products": products[:5],  # Top 5 results
                "total_found": len(products),
                "query_params": query_params
            }
            
        except Exception as e:
            logger.error(f"Error in ProductDiscoveryAgent: {e}")
            return {
                "response": "I'm having trouble searching right now. Please try again or browse our catalog directly.",
                "products": [],
                "total_found": 0,
                "error": str(e)
            }


class ShoppingAssistantAgent:
    """
    AI Agent for general shopping assistance and product questions.
    Provides detailed information, comparisons, and recommendations.
    """
    
    def __init__(self):
        """Initialize the shopping assistant agent."""
        # Use DefaultAzureCredential for managed identity / Azure CLI auth
        from azure.identity import DefaultAzureCredential
        
        self.client = ChatCompletionsClient(
            endpoint=settings.azure_openai_endpoint,
            credential=DefaultAzureCredential()
        )
        self.model = settings.azure_openai_deployment
        
        self.system_prompt = """You are a knowledgeable shopping assistant helping customers with their purchases.

Your capabilities:
1. Answer product questions (features, specifications, comparisons)
2. Provide buying advice and recommendations
3. Explain product details and benefits
4. Help with size, compatibility, and suitability questions
5. Assist with order-related questions

Guidelines:
- Be helpful, friendly, and informative
- Provide accurate information based on product data
- Ask clarifying questions when needed
- Recommend alternatives when appropriate
- Focus on customer satisfaction

You have access to product information from our catalog."""
    
    def get_product_details(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Fetch detailed product information."""
        try:
            db = DatabaseConnection(
                settings.database_connection_string,
                use_access_token=settings.sql_use_azure_auth
            )
            
            query = """
                SELECT 
                    p.ProductID, p.ProductName, p.Price, p.StockQuantity,
                    p.Description, p.SKU, c.CategoryName
                FROM dbo.Products p
                INNER JOIN dbo.Categories c ON p.CategoryID = c.CategoryID
                WHERE p.ProductID = ?
            """
            
            results = db.execute_query(query, (product_id,))
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"Error fetching product details: {e}")
            return None
    
    async def answer_question(self, question: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Answer customer question about products or shopping.
        
        Args:
            question: Customer's question
            context: Optional context (e.g., specific product data)
            
        Returns:
            AI-generated answer
        """
        try:
            logger.info(f"Shopping Assistant answering: {question}")
            
            # Build context for AI
            context_text = ""
            if context:
                if "product" in context:
                    p = context["product"]
                    context_text = f"\nProduct: {p.get('ProductName')} - ${p.get('Price')} - {p.get('Description', 'No description')}"
                
                if "cart" in context:
                    cart = context["cart"]
                    context_text += f"\nCart: {cart.get('total_items', 0)} items, Total: ${cart.get('total_amount', 0):.2f}"
            
            prompt = f"""Customer question: "{question}"
{context_text}

Provide a helpful, accurate answer. Be concise but complete."""
            
            response = self.client.complete(
                messages=[
                    SystemMessage(content=self.system_prompt),
                    UserMessage(content=prompt)
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error in ShoppingAssistantAgent: {e}")
            return "I'm having trouble processing your question right now. Could you please rephrase or try again?"
    
    async def compare_products(self, product_ids: List[int]) -> str:
        """
        Compare multiple products and provide recommendations.
        
        Args:
            product_ids: List of product IDs to compare
            
        Returns:
            Comparison summary
        """
        try:
            if len(product_ids) < 2:
                return "Please provide at least 2 products to compare."
            
            # Fetch products
            products = [self.get_product_details(pid) for pid in product_ids]
            products = [p for p in products if p]  # Filter out None
            
            if len(products) < 2:
                return "I couldn't find enough products to compare."
            
            # Format for AI
            products_text = "\n\n".join([
                f"Product {i+1}: {p['ProductName']}\n- Price: ${p['Price']:.2f}\n- Stock: {p['StockQuantity']}\n- Description: {p.get('Description', 'N/A')}"
                for i, p in enumerate(products)
            ])
            
            prompt = f"""Compare these products and provide recommendations:

{products_text}

Provide:
1. Key differences
2. Best value
3. Best for specific needs
4. Recommendation based on typical customer preferences

Be concise but thorough."""
            
            response = self.client.complete(
                messages=[
                    SystemMessage(content=self.system_prompt),
                    UserMessage(content=prompt)
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=700
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error comparing products: {e}")
            return "I'm having trouble comparing those products. Please try again."


# ============================================================================
# Agent Factory
# ============================================================================

def get_product_discovery_agent() -> ProductDiscoveryAgent:
    """Get singleton instance of product discovery agent."""
    return ProductDiscoveryAgent()


def get_shopping_assistant_agent() -> ShoppingAssistantAgent:
    """Get singleton instance of shopping assistant agent."""
    return ShoppingAssistantAgent()
