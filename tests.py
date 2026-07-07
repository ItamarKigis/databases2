import sys
from datetime import datetime
# Assuming your solution or business objects are in these modules
import Solution
from DBDefs import Customer, Order, ReturnValue


def run_max_avg_spending_test():
    print("--- Starting Test for get_customers_spent_max_avg_amount_money ---")

    # 1. Reset the database state
    try:
        Solution.drop_tables()
    except Exception:
        pass
    Solution.create_tables()

    # ==========================================
    # PHASE 1: Empty Database / No Orders
    # ==========================================
    print("\nPhase 1: Testing empty database...")
    result = Solution.get_customers_spent_max_avg_amount_money()
    assert result == [], f"Expected [] on empty DB, got {result}"
    print("✅ Phase 1 Passed: Correctly returned an empty list.")

    # ==========================================
    # PHASE 2: Single Winner
    # ==========================================
    print("\nPhase 2: Testing single winner...")

    # Create Customers (cust_id, full_name, age, phone)
    c1 = Customer(cust_id=1, full_name="Alice Smith", age=25, phone="0541234567")
    c2 = Customer(cust_id=2, full_name="Bob Jones", age=30, phone="0529876543")

    assert Solution.add_customer(c1) == ReturnValue.OK
    assert Solution.add_customer(c2) == ReturnValue.OK

    # Create Orders (order_id, date, delivery_fee, delivery_address, tip)
    # Remember: Total price = bill + delivery_fee + tip (Assuming view handles bill safely)
    o1 = Order(order_id=101, date=datetime(2026, 7, 7, 12, 0, 0), delivery_fee=15.0, delivery_address="Haifa Center 1",
               tip=10.0)
    o2 = Order(order_id=102, date=datetime(2026, 7, 7, 13, 0, 0), delivery_fee=10.0, delivery_address="Haifa Center 2",
               tip=5.0)
    o3 = Order(order_id=103, date=datetime(2026, 7, 7, 14, 0, 0), delivery_fee=20.0, delivery_address="Haifa Center 3",
               tip=20.0)

    assert Solution.add_order(o1) == ReturnValue.OK
    assert Solution.add_order(o2) == ReturnValue.OK
    assert Solution.add_order(o3) == ReturnValue.OK

    # Link orders to customers
    assert Solution.customer_placed_order(customer_id=1, order_id=101) == ReturnValue.OK
    assert Solution.customer_placed_order(customer_id=1, order_id=102) == ReturnValue.OK
    assert Solution.customer_placed_order(customer_id=2, order_id=103) == ReturnValue.OK

    # Scenario Pricing breakdown:
    # Alice (ID: 1) has 2 orders:
    #   - Order 101: Total = 25.0 (Assuming 0 bill for simplicity, or add items via order_contains_dish)
    #   - Order 102: Total = 15.0
    #   - Alice's Average = (25.0 + 15.0) / 2 = 20.0
    # Bob (ID: 2) has 1 order:
    #   - Order 103: Total = 40.0
    #   - Bob's Average = 40.0 / 1 = 40.0

    result = Solution.get_customers_spent_max_avg_amount_money()
    assert result == [2], f"Expected [2] (Bob spent more on avg), got {result}"
    print("✅ Phase 2 Passed: Bob uniquely returned as highest average spender.")

    # ==========================================
    # PHASE 3: Tie-Breaker Condition
    # ==========================================
    print("\nPhase 3: Testing a tie scenario...")

    # Let's give Alice a high-spending order to match Bob's 40.0 average.
    # Alice currently has a total of 40.0 over 2 orders.
    # If she places a 3rd order costing 80.0, her new total is 120.0 over 3 orders -> Avg = 40.0!
    o4 = Order(order_id=104, date=datetime(2026, 7, 7, 15, 0, 0), delivery_fee=50.0, delivery_address="Haifa Center 4",
               tip=30.0)
    assert Solution.add_order(o4) == ReturnValue.OK
    assert Solution.customer_placed_order(customer_id=1, order_id=104) == ReturnValue.OK

    # Both Alice (ID: 1) and Bob (ID: 2) now have an average order price of 40.0.
    # The requirement specifies that the list should be ordered by customer id in ascending order.
    result = Solution.get_customers_spent_max_avg_amount_money()
    assert result == [1, 2], f"Expected [1, 2] sorted ascending, got {result}"
    print("✅ Phase 3 Passed: Handled ties cleanly and returned sorted IDs.")

    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY! 🎉")


if __name__ == "__main__":
    run_max_avg_spending_test()