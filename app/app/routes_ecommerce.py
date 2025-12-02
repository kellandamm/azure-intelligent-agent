"""
E-Commerce routes for Agent-Powered Shopping Demo.
Integrates with Fabric SQL Database for products, cart, and orders.
"""
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging
from utils.db_connection import DatabaseConnection
from utils.auth import get_current_user
from config import settings
from app.agents_shopping import get_product_discovery_agent, get_shopping_assistant_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ecommerce", tags=["ecommerce"])


# ============================================================================
# Pydantic Models
# ============================================================================

class Product(BaseModel):
    """Product model from Fabric SQL."""
    ProductID: int
    ProductName: str
    CategoryID: int
    CategoryName: Optional[str] = None
    Price: float
    StockQuantity: int
    Description: Optional[str] = None
    SKU: Optional[str] = None
    IsActive: bool = True


class ProductFilter(BaseModel):
    """Product filtering parameters."""
    category: Optional[str] = None
    search: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    in_stock_only: bool = True
    limit: int = Field(default=20, le=100)
    offset: int = Field(default=0, ge=0)


class CartItem(BaseModel):
    """Shopping cart item."""
    product_id: int
    quantity: int = Field(gt=0)
    unit_price: Optional[float] = None


class CartResponse(BaseModel):
    """Cart response with items and total."""
    items: List[Dict[str, Any]]
    total_items: int
    total_amount: float
    user_id: Optional[str] = None


class OrderCreate(BaseModel):
    """Order creation request."""
    customer_id: Optional[int] = None
    shipping_address: str
    shipping_city: str
    shipping_state: str
    shipping_zip: str
    shipping_country: str = "USA"
    payment_method: str


class OrderResponse(BaseModel):
    """Order response."""
    OrderID: int
    OrderDate: datetime
    OrderStatus: str
    TotalAmount: float
    ShippingAddress: str


# ============================================================================
# Database Helper
# ============================================================================

def get_db() -> DatabaseConnection:
    """Get database connection for e-commerce operations."""
    # E-commerce uses direct database connection for product catalog
    # Authentication is only required for user-specific operations (orders)
    if not settings.sql_server or not settings.sql_database:
        raise HTTPException(
            status_code=503, 
            detail="Database not configured"
        )
    
    from utils.db_connection import build_connection_string
    conn_string = build_connection_string(
        server=settings.sql_server,
        database=settings.sql_database,
        username=settings.sql_username,
        password=settings.sql_password,
        driver=settings.sql_driver,
        use_azure_auth=settings.sql_use_azure_auth,
        encrypt=settings.sql_encrypt,
        trust_server_cert=settings.sql_trust_server_cert
    )
    use_token = settings.sql_use_azure_auth
    return DatabaseConnection(conn_string, use_access_token=use_token)


# ============================================================================
# Product Endpoints
# ============================================================================

@router.get("/products", response_model=List[Product])
async def get_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: bool = True,
    limit: int = 20,
    offset: int = 0
):
    """
    Get product catalog from Fabric SQL Database.
    Supports filtering by category, search term, price range, and stock status.
    """
    try:
        db = get_db()
        
        # Build dynamic query
        query = """
            SELECT 
                p.ProductID, 
                p.ProductName, 
                p.CategoryID,
                c.CategoryName,
                p.Price, 
                p.StockQuantity, 
                p.Description, 
                p.SKU,
                p.IsActive
            FROM dbo.Products p
            INNER JOIN dbo.Categories c ON p.CategoryID = c.CategoryID
            WHERE p.IsActive = 1
        """
        params = []
        
        # Add filters
        if category:
            query += " AND c.CategoryName LIKE ?"
            params.append(f"%{category}%")
        
        if search:
            query += " AND (p.ProductName LIKE ? OR p.Description LIKE ?)"
            params.append(f"%{search}%")
            params.append(f"%{search}%")
        
        if min_price is not None:
            query += " AND p.Price >= ?"
            params.append(min_price)
        
        if max_price is not None:
            query += " AND p.Price <= ?"
            params.append(max_price)
        
        if in_stock:
            query += " AND p.StockQuantity > 0"
        
        # Add pagination
        query += " ORDER BY p.ProductName OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.append(offset)
        params.append(limit)
        
        # Execute query
        results = db.execute_query(query, tuple(params) if params else None)
        
        if not results:
            return []
        
        products = [Product(**row) for row in results]
        logger.info(f"Retrieved {len(products)} products")
        return products
        
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch products: {str(e)}")


@router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: int):
    """Get a single product by ID."""
    try:
        db = get_db()
        
        query = """
            SELECT 
                p.ProductID, 
                p.ProductName, 
                p.CategoryID,
                c.CategoryName,
                p.Price, 
                p.StockQuantity, 
                p.Description, 
                p.SKU,
                p.IsActive
            FROM dbo.Products p
            INNER JOIN dbo.Categories c ON p.CategoryID = c.CategoryID
            WHERE p.ProductID = ?
        """
        
        results = db.execute_query(query, (product_id,))
        
        if not results or len(results) == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return Product(**results[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch product: {str(e)}")


@router.get("/categories")
async def get_categories():
    """Get all product categories."""
    try:
        db = get_db()
        
        query = """
            SELECT 
                CategoryID, 
                CategoryName, 
                Description,
                (SELECT COUNT(*) FROM dbo.Products WHERE CategoryID = c.CategoryID AND IsActive = 1) as ProductCount
            FROM dbo.Categories c
            ORDER BY CategoryName
        """
        
        results = db.execute_query(query)
        return results or []
        
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch categories: {str(e)}")


# ============================================================================
# Shopping Cart Endpoints (Session-based)
# ============================================================================

# In-memory cart storage (replace with Redis/database for production)
cart_storage: Dict[str, List[CartItem]] = {}


async def get_user_from_token(request: Request, authorization: Optional[str] = Header(None)) -> str:
    """Extract user ID from JWT token or return guest."""
    if not authorization:
        return "guest"  # Allow guest shopping
    
    try:
        # Use the auth manager from request state
        from fastapi.security import HTTPBearer
        from fastapi.security.http import HTTPAuthorizationCredentials
        
        if not hasattr(request.app.state, 'auth_manager') or request.app.state.auth_manager is None:
            return "guest"
        
        auth_manager = request.app.state.auth_manager
        token = authorization.replace("Bearer ", "")
        user_data = auth_manager.verify_jwt_token(token)
        
        if user_data:
            return str(user_data.get("user_id", "guest"))
        return "guest"
    except:
        return "guest"


@router.get("/cart", response_model=CartResponse)
async def get_cart(user_id: str = Depends(get_user_from_token)):
    """Get user's shopping cart."""
    try:
        cart_items = cart_storage.get(user_id, [])
        
        if not cart_items:
            return CartResponse(items=[], total_items=0, total_amount=0.0, user_id=user_id)
        
        # Fetch product details for cart items
        db = get_db()
        product_ids = [item.product_id for item in cart_items]
        placeholders = ",".join(["?" for _ in product_ids])
        
        query = f"""
            SELECT ProductID, ProductName, Price, StockQuantity, SKU
            FROM dbo.Products
            WHERE ProductID IN ({placeholders})
        """
        
        products = db.execute_query(query, tuple(product_ids))
        product_dict = {p["ProductID"]: p for p in products} if products else {}
        
        # Build cart response
        cart_response_items = []
        total_amount = 0.0
        total_items = 0
        
        for item in cart_items:
            product = product_dict.get(item.product_id)
            if product:
                item_total = product["Price"] * item.quantity
                cart_response_items.append({
                    "product_id": item.product_id,
                    "product_name": product["ProductName"],
                    "quantity": item.quantity,
                    "unit_price": product["Price"],
                    "item_total": item_total,
                    "sku": product["SKU"],
                    "available_stock": product["StockQuantity"]
                })
                total_amount += item_total
                total_items += item.quantity
        
        return CartResponse(
            items=cart_response_items,
            total_items=total_items,
            total_amount=total_amount,
            user_id=user_id
        )
        
    except Exception as e:
        logger.error(f"Error fetching cart: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch cart: {str(e)}")


@router.post("/cart/add")
async def add_to_cart(
    cart_item: CartItem,
    user_id: str = Depends(get_user_from_token)
):
    """Add item to cart with stock validation."""
    try:
        # Validate product exists and has stock
        db = get_db()
        query = "SELECT ProductID, ProductName, Price, StockQuantity FROM dbo.Products WHERE ProductID = ? AND IsActive = 1"
        results = db.execute_query(query, (cart_item.product_id,))
        
        if not results:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product = results[0]
        
        # Check stock availability
        if product["StockQuantity"] < cart_item.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock. Only {product['StockQuantity']} available"
            )
        
        # Add to cart
        if user_id not in cart_storage:
            cart_storage[user_id] = []
        
        # Check if product already in cart
        existing_item = next((item for item in cart_storage[user_id] if item.product_id == cart_item.product_id), None)
        
        if existing_item:
            new_quantity = existing_item.quantity + cart_item.quantity
            if product["StockQuantity"] < new_quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot add {cart_item.quantity} more. Only {product['StockQuantity']} available"
                )
            existing_item.quantity = new_quantity
        else:
            cart_storage[user_id].append(cart_item)
        
        logger.info(f"Added {cart_item.quantity}x product {cart_item.product_id} to cart for user {user_id}")
        
        return {
            "message": "Item added to cart",
            "product_name": product["ProductName"],
            "quantity": cart_item.quantity
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add to cart: {str(e)}")


@router.put("/cart/update")
async def update_cart_item(
    cart_item: CartItem,
    user_id: str = Depends(get_user_from_token)
):
    """Update cart item quantity."""
    try:
        if user_id not in cart_storage:
            raise HTTPException(status_code=404, detail="Cart not found")
        
        existing_item = next((item for item in cart_storage[user_id] if item.product_id == cart_item.product_id), None)
        
        if not existing_item:
            raise HTTPException(status_code=404, detail="Item not in cart")
        
        # Validate stock
        db = get_db()
        query = "SELECT StockQuantity FROM dbo.Products WHERE ProductID = ?"
        results = db.execute_query(query, (cart_item.product_id,))
        
        if not results or results[0]["StockQuantity"] < cart_item.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        
        existing_item.quantity = cart_item.quantity
        
        return {"message": "Cart updated", "quantity": cart_item.quantity}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cart: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update cart: {str(e)}")


@router.delete("/cart/remove/{product_id}")
async def remove_from_cart(
    product_id: int,
    user_id: str = Depends(get_user_from_token)
):
    """Remove item from cart."""
    try:
        if user_id not in cart_storage:
            raise HTTPException(status_code=404, detail="Cart not found")
        
        cart_storage[user_id] = [item for item in cart_storage[user_id] if item.product_id != product_id]
        
        return {"message": "Item removed from cart"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from cart: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove from cart: {str(e)}")


@router.delete("/cart/clear")
async def clear_cart(user_id: str = Depends(get_user_from_token)):
    """Clear entire cart."""
    try:
        if user_id in cart_storage:
            cart_storage[user_id] = []
        
        return {"message": "Cart cleared"}
        
    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cart: {str(e)}")


# ============================================================================
# Order Endpoints
# ============================================================================

@router.post("/orders", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    user_id: str = Depends(get_user_from_token)
):
    """Create order from cart (authenticated users only)."""
    try:
        if user_id == "guest":
            raise HTTPException(status_code=401, detail="Please log in to place an order")
        
        # Get cart
        cart_items = cart_storage.get(user_id, [])
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        db = get_db()
        
        # Calculate total and validate stock
        total_amount = 0.0
        order_items = []
        
        for item in cart_items:
            query = "SELECT ProductID, Price, StockQuantity FROM dbo.Products WHERE ProductID = ?"
            results = db.execute_query(query, (item.product_id,))
            
            if not results:
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
            
            product = results[0]
            
            if product["StockQuantity"] < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for product {item.product_id}"
                )
            
            item_total = product["Price"] * item.quantity
            total_amount += item_total
            order_items.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": product["Price"]
            })
        
        # Create order in database
        insert_order = """
            INSERT INTO dbo.Orders (
                CustomerID, OrderDate, OrderStatus, TotalAmount,
                ShippingAddress, ShippingCity, ShippingState, ShippingZipCode, ShippingCountry,
                PaymentMethod
            )
            OUTPUT INSERTED.OrderID, INSERTED.OrderDate, INSERTED.OrderStatus, INSERTED.TotalAmount, INSERTED.ShippingAddress
            VALUES (?, GETUTCDATE(), 'Pending', ?, ?, ?, ?, ?, ?, ?)
        """
        
        # Use customer_id from request or default to user_id as int
        customer_id = order_data.customer_id or int(user_id) if user_id.isdigit() else 1
        
        order_result = db.execute_query(
            insert_order,
            (
                customer_id,
                total_amount,
                order_data.shipping_address,
                order_data.shipping_city,
                order_data.shipping_state,
                order_data.shipping_zip,
                order_data.shipping_country,
                order_data.payment_method
            )
        )
        
        if not order_result:
            raise HTTPException(status_code=500, detail="Failed to create order")
        
        order = order_result[0]
        order_id = order["OrderID"]
        
        # Insert order items
        for item in order_items:
            insert_item = """
                INSERT INTO dbo.OrderItems (OrderID, ProductID, Quantity, UnitPrice)
                VALUES (?, ?, ?, ?)
            """
            db.execute_query(
                insert_item,
                (order_id, item["product_id"], item["quantity"], item["unit_price"]),
                fetch=False
            )
            
            # Update product stock
            update_stock = """
                UPDATE dbo.Products 
                SET StockQuantity = StockQuantity - ?
                WHERE ProductID = ?
            """
            db.execute_query(
                update_stock,
                (item["quantity"], item["product_id"]),
                fetch=False
            )
        
        # Clear cart
        cart_storage[user_id] = []
        
        logger.info(f"Order {order_id} created for user {user_id} - Total: ${total_amount:.2f}")
        
        return OrderResponse(
            OrderID=order_id,
            OrderDate=order["OrderDate"],
            OrderStatus=order["OrderStatus"],
            TotalAmount=order["TotalAmount"],
            ShippingAddress=order["ShippingAddress"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@router.get("/orders", response_model=List[OrderResponse])
async def get_orders(user_id: str = Depends(get_user_from_token)):
    """Get user's order history."""
    try:
        if user_id == "guest":
            raise HTTPException(status_code=401, detail="Please log in to view orders")
        
        db = get_db()
        
        customer_id = int(user_id) if user_id.isdigit() else 1
        
        query = """
            SELECT OrderID, OrderDate, OrderStatus, TotalAmount, ShippingAddress
            FROM dbo.Orders
            WHERE CustomerID = ?
            ORDER BY OrderDate DESC
        """
        
        results = db.execute_query(query, (customer_id,))
        
        if not results:
            return []
        
        return [OrderResponse(**order) for order in results]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")


@router.get("/orders/{order_id}", response_model=Dict[str, Any])
async def get_order_details(
    order_id: int,
    user_id: str = Depends(get_user_from_token)
):
    """Get detailed order information including items."""
    try:
        if user_id == "guest":
            raise HTTPException(status_code=401, detail="Please log in to view order details")
        
        db = get_db()
        
        # Get order
        order_query = """
            SELECT OrderID, OrderDate, OrderStatus, TotalAmount,
                   ShippingAddress, ShippingCity, ShippingState, ShippingZipCode, ShippingCountry,
                   PaymentMethod
            FROM dbo.Orders
            WHERE OrderID = ?
        """
        
        order_results = db.execute_query(order_query, (order_id,))
        
        if not order_results:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order = order_results[0]
        
        # Get order items
        items_query = """
            SELECT 
                oi.ProductID, p.ProductName, oi.Quantity, oi.UnitPrice,
                oi.Discount, oi.LineTotal, p.SKU
            FROM dbo.OrderItems oi
            INNER JOIN dbo.Products p ON oi.ProductID = p.ProductID
            WHERE oi.OrderID = ?
        """
        
        items = db.execute_query(items_query, (order_id,))
        
        return {
            **order,
            "items": items or []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch order details: {str(e)}")


# ============================================================================
# AI Shopping Agent Endpoints
# ============================================================================

class AgentQuery(BaseModel):
    """Agent query request."""
    query: str
    context: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Agent response."""
    response: str
    products: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/agent/search", response_model=AgentResponse)
async def agent_product_search(query: AgentQuery):
    """
    AI-powered product search using natural language.
    
    Example queries:
    - "Show me laptops under $1000"
    - "I need running shoes for trail running"
    - "What electronics are on sale?"
    """
    try:
        agent = get_product_discovery_agent()
        result = await agent.answer_query(query.query)
        
        return AgentResponse(
            response=result["response"],
            products=result.get("products"),
            metadata={
                "total_found": result.get("total_found", 0),
                "query_params": result.get("query_params")
            }
        )
        
    except Exception as e:
        logger.error(f"Error in agent search: {e}")
        raise HTTPException(status_code=500, detail=f"Agent search failed: {str(e)}")


@router.post("/agent/ask", response_model=AgentResponse)
async def agent_ask_question(query: AgentQuery):
    """
    Ask the shopping assistant any product or shopping-related question.
    
    Example questions:
    - "What's the difference between these products?"
    - "Is this laptop good for gaming?"
    - "What payment methods do you accept?"
    """
    try:
        agent = get_shopping_assistant_agent()
        answer = await agent.answer_question(query.query, query.context)
        
        return AgentResponse(
            response=answer,
            products=None,
            metadata={"type": "general_assistance"}
        )
        
    except Exception as e:
        logger.error(f"Error in agent ask: {e}")
        raise HTTPException(status_code=500, detail=f"Agent question failed: {str(e)}")


@router.post("/agent/compare")
async def agent_compare_products(product_ids: List[int]):
    """
    AI-powered product comparison.
    Provide 2-5 product IDs to get detailed comparison and recommendations.
    """
    try:
        if len(product_ids) < 2 or len(product_ids) > 5:
            raise HTTPException(
                status_code=400,
                detail="Please provide 2-5 product IDs for comparison"
            )
        
        agent = get_shopping_assistant_agent()
        comparison = await agent.compare_products(product_ids)
        
        return {
            "comparison": comparison,
            "product_ids": product_ids
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in agent compare: {e}")
        raise HTTPException(status_code=500, detail=f"Product comparison failed: {str(e)}")

