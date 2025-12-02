"""
Test script to verify Row-Level Security (RLS) implementation
"""

import sys

sys.path.insert(0, "c:\\code\\agentsdemos")

from app.agent_tools import FabricDataTools


def test_rls_filtering():
    """Test that RLS filtering works correctly for different users"""

    print("=" * 80)
    print("Row-Level Security (RLS) Test")
    print("=" * 80)

    # Test 1: West user accessing their own data
    print("\n1. West User - Accessing Own Data")
    print("-" * 80)
    west_context = {
        "username": "west_user",
        "region": "West",
        "data_scope": ["West"],
        "roles": ["sales_viewer"],
    }
    result = FabricDataTools.get_sales_summary(user_context=west_context)
    print(f"✅ Region: {result.get('region')}")
    print(f"✅ Revenue: ${result.get('total_revenue'):,.2f}")
    print(f"✅ Expected: West region data only")
    assert result.get("region") == "West", "Should return West region data"
    assert result.get("total_revenue") == 3890000.00, "Should return West revenue"

    # Test 2: East user accessing their own data
    print("\n2. East User - Accessing Own Data")
    print("-" * 80)
    east_context = {
        "username": "east_user",
        "region": "East",
        "data_scope": ["East"],
        "roles": ["sales_viewer"],
    }
    result = FabricDataTools.get_sales_summary(user_context=east_context)
    print(f"✅ Region: {result.get('region')}")
    print(f"✅ Revenue: ${result.get('total_revenue'):,.2f}")
    print(f"✅ Expected: East region data only")
    assert result.get("region") == "East", "Should return East region data"
    assert result.get("total_revenue") == 5250000.00, "Should return East revenue"

    # Test 3: Admin user (no region restriction)
    print("\n3. Admin User - Accessing All Data")
    print("-" * 80)
    admin_context = None  # No user context = admin
    result = FabricDataTools.get_sales_summary(user_context=admin_context)
    print(f"✅ Total Revenue: ${result.get('total_revenue'):,.2f}")
    print(f"✅ Regions: {result.get('regions_included')}")
    print(f"✅ Expected: Aggregated data across all regions")
    assert result.get("total_revenue") == 13260000.00, "Should return total revenue"

    # Test 4: Test customer demographics RLS
    print("\n4. West User - Customer Demographics")
    print("-" * 80)
    result = FabricDataTools.get_customer_demographics(user_context=west_context)
    print(f"✅ Region: {result.get('region')}")
    print(f"✅ Total Customers: {result.get('total_customers'):,}")
    print(f"✅ Expected: West region customers only")
    assert result.get("region") == "West", "Should return West region"
    assert result.get("total_customers") == 2800, "Should return West customer count"

    # Test 5: Test inventory status RLS
    print("\n5. East User - Inventory Status")
    print("-" * 80)
    result = FabricDataTools.get_inventory_status(user_context=east_context)
    print(f"✅ Region: {result.get('region')}")
    print(f"✅ Total SKUs: {result.get('total_sku_count')}")
    print(f"✅ In Stock: {result.get('in_stock')}")
    print(f"✅ Expected: East region inventory only")
    assert result.get("region") == "East", "Should return East region"
    assert result.get("total_sku_count") == 242, "Should return East SKU count"

    # Test 6: Test performance metrics RLS
    print("\n6. Central User - Performance Metrics")
    print("-" * 80)
    central_context = {
        "username": "central_user",
        "region": "Central",
        "data_scope": ["Central"],
        "roles": ["sales_viewer"],
    }
    result = FabricDataTools.get_performance_metrics(
        metric_type="sales", user_context=central_context
    )
    print(f"✅ Region: {result.get('region')}")
    print(f"✅ Conversion Rate: {result.get('conversion_rate')}%")
    print(f"✅ Win Rate: {result.get('win_rate')}%")
    print(f"✅ Expected: Central region metrics only")
    assert result.get("region") == "Central", "Should return Central region"
    assert result.get("conversion_rate") == 3.2, "Should return Central conversion rate"

    print("\n" + "=" * 80)
    print("✅ ALL RLS TESTS PASSED!")
    print("=" * 80)
    print("\nSummary:")
    print("- West user can only see West data ✅")
    print("- East user can only see East data ✅")
    print("- Central user can only see Central data ✅")
    print("- Admin user can see all aggregated data ✅")
    print("- RLS filtering works across all tool functions ✅")


if __name__ == "__main__":
    try:
        test_rls_filtering()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
