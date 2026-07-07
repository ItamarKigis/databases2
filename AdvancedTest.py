import unittest
from datetime import datetime, timedelta

# Adjust these imports based on your actual folder structure
from Business.Customer import Customer, BadCustomer
from Business.Dish import Dish, BadDish
from Business.Order import Order, BadOrder
from Utility.ReturnValue import ReturnValue
import Solution


# ==============================================================================
# SUITE 1: Strict Boundary Constraints
# ==============================================================================
class Test1_BoundaryConstraints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Solution.drop_tables()
        Solution.create_tables()

    @classmethod
    def tearDownClass(cls):
        Solution.drop_tables()

    def setUp(self):
        Solution.clear_tables()

    def test_customer_age_and_phone_boundaries(self):
        # Age should be between 18 and 120
        self.assertEqual(Solution.add_customer(Customer(1, "A", 17, "0501234567")), ReturnValue.BAD_PARAMS)
        self.assertEqual(Solution.add_customer(Customer(2, "B", 18, "0501234567")), ReturnValue.OK)
        self.assertEqual(Solution.add_customer(Customer(3, "C", 120, "0501234567")), ReturnValue.OK)
        self.assertEqual(Solution.add_customer(Customer(4, "D", 121, "0501234567")), ReturnValue.BAD_PARAMS)

        # Phone exactly 10 chars
        self.assertEqual(Solution.add_customer(Customer(5, "E", 25, "050123456")), ReturnValue.BAD_PARAMS)
        self.assertEqual(Solution.add_customer(Customer(6, "F", 25, "05012345678")), ReturnValue.BAD_PARAMS)

    def test_dish_name_and_price_boundaries(self):
        # Name at least 4 chars, Price positive
        self.assertEqual(Solution.add_dish(Dish(1, "Pie", 10.0, True)), ReturnValue.BAD_PARAMS)
        self.assertEqual(Solution.add_dish(Dish(2, "Soup", 10.0, True)), ReturnValue.OK)
        self.assertEqual(Solution.add_dish(Dish(3, "Cake", 0.0, True)), ReturnValue.BAD_PARAMS)
        self.assertEqual(Solution.add_dish(Dish(4, "Cake", -5.0, True)), ReturnValue.BAD_PARAMS)

    def test_order_address_and_microsecond_handling(self):
        # Address at least 5 chars, Delivery fee >= 0, Tip >= 0
        now = datetime.now()
        # This address is only 4 chars, should fail
        self.assertEqual(Solution.add_order(Order(1, now, 10.0, "1234", 5.0)), ReturnValue.BAD_PARAMS)
        self.assertEqual(Solution.add_order(Order(2, now, -1.0, "12345", 5.0)), ReturnValue.BAD_PARAMS)
        self.assertEqual(Solution.add_order(Order(3, now, 10.0, "12345", -1.0)), ReturnValue.BAD_PARAMS)

        # Microseconds should be handled/truncated without failing
        time_with_micro = datetime(2023, 5, 5, 12, 30, 15, 999999)
        self.assertEqual(Solution.add_order(Order(4, time_with_micro, 10.0, "Valid Address", 5.0)), ReturnValue.OK)


# ==============================================================================
# SUITE 2: Business Logic & Historical Data
# ==============================================================================
class Test2_BusinessLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Solution.drop_tables()
        Solution.create_tables()

    @classmethod
    def tearDownClass(cls):
        Solution.drop_tables()

    def setUp(self):
        Solution.clear_tables()

    def test_inactive_dish_protections(self):
        Solution.add_dish(Dish(1, "Pasta", 40.0, False))
        Solution.add_order(Order(1, datetime.now(), 10.0, "Valid Address", 5.0))

        # Cannot add inactive dish to order
        self.assertEqual(Solution.order_contains_dish(1, 1, 2), ReturnValue.NOT_EXISTS)

        # Cannot update price of inactive dish
        self.assertEqual(Solution.update_dish_price(1, 50.0), ReturnValue.NOT_EXISTS)

    def test_historical_pricing_retention(self):
        # Add dish at 50.0
        Solution.add_dish(Dish(1, "Steak", 50.0, True))

        # Order 1 gets the dish at 50.0
        Solution.add_order(Order(1, datetime.now(), 0.0, "Valid Address", 0.0))
        Solution.order_contains_dish(1, 1, 2)  # Total = 100.0

        # Update price to 100.0
        Solution.update_dish_price(1, 100.0)

        # Order 2 gets the dish at 100.0
        Solution.add_order(Order(2, datetime.now(), 0.0, "Valid Address", 0.0))
        Solution.order_contains_dish(2, 1, 2)  # Total = 200.0

        # Assert historic prices are used in get_order_total_price
        self.assertEqual(Solution.get_order_total_price(1), 100.0)
        self.assertEqual(Solution.get_order_total_price(2), 200.0)

    def test_empty_order_total_price(self):
        # Order without any dishes should return delivery_fee + tip
        Solution.add_order(Order(1, datetime.now(), 15.5, "Valid Address", 10.5))
        self.assertEqual(Solution.get_order_total_price(1), 26.0)


# ==============================================================================
# SUITE 3: Basic API Edge Cases
# ==============================================================================
class Test3_BasicAPIEdgeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Solution.drop_tables()
        Solution.create_tables()

    @classmethod
    def tearDownClass(cls):
        Solution.drop_tables()

    def setUp(self):
        Solution.clear_tables()

    def test_most_profitable_dish_strict_time_bounds(self):
        Solution.add_dish(Dish(1, "Dish A", 100.0, True))
        Solution.add_dish(Dish(2, "Dish B", 200.0, True))

        t1 = datetime(2024, 1, 1, 10, 0, 0)
        t2 = datetime(2024, 1, 1, 12, 0, 0)
        t3 = datetime(2024, 1, 1, 14, 0, 0)

        # Order exactly on start boundary
        Solution.add_order(Order(1, t1, 0.0, "Valid Address", 0.0))
        Solution.order_contains_dish(1, 1, 1)

        # Order exactly on end boundary
        Solution.add_order(Order(2, t3, 0.0, "Valid Address", 0.0))
        Solution.order_contains_dish(2, 2, 1)

        # Both should be included if query is inclusive. Dish 2 revenue (200) > Dish 1 (100)
        profitable = Solution.get_most_profitable_dish_in_period(t1, t3)
        self.assertEqual(profitable.get_dish_id(), 2)

        # If period is just t2 to t2, no orders exist -> BadDish
        self.assertIsInstance(Solution.get_most_profitable_dish_in_period(t2, t2), BadDish)

    def test_max_avg_spending_with_zero_totals(self):
        # Testing customers whose orders amount to exactly 0
        Solution.add_customer(Customer(1, "A", 20, "0500000001"))
        Solution.add_customer(Customer(2, "B", 20, "0500000002"))

        Solution.add_order(Order(1, datetime.now(), 0.0, "Valid Address", 0.0))
        Solution.customer_placed_order(1, 1)

        Solution.add_order(Order(2, datetime.now(), 0.0, "Valid Address", 0.0))
        Solution.customer_placed_order(2, 2)

        # Both average 0.0
        result = Solution.get_customers_spent_max_avg_amount_money()
        self.assertEqual(result, [1, 2])


# ==============================================================================
# SUITE 4: Advanced API - Bottom 5 Dishes & Recommendations
# ==============================================================================
class Test4_AdvancedAPI_Complex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Solution.drop_tables()
        Solution.create_tables()

    @classmethod
    def tearDownClass(cls):
        Solution.drop_tables()

    def setUp(self):
        Solution.clear_tables()

    def test_get_customers_rated_but_not_ordered_tiebreakers(self):
        Solution.add_customer(Customer(1, "A", 20, "0500000001"))

        # Add 6 dishes.
        for i in range(1, 7):
            Solution.add_dish(Dish(i, f"Dish {i}00", 10.0, True))

        # We need to define the bottom 5.
        # Dish 1-4 get a rating of 1.
        for i in range(1, 5):
            Solution.customer_rated_dish(1, i, 1)
            # Customer 1 ordered these, so they shouldn't show up in the final output
            Solution.add_order(Order(i, datetime.now(), 0.0, "ValidAddr", 0.0))
            Solution.customer_placed_order(1, i)
            Solution.order_contains_dish(i, i, 1)

        # Dish 5 gets a rating of 2. (Avg 2.0).
        Solution.customer_rated_dish(1, 5, 2)
        # Dish 5 is NOT ordered by Customer 1.

        # Dish 6 is unrated (Avg 3.0).

        # Bottom 5 dishes are: 1, 2, 3, 4, 5.
        # Dish 5 is in the bottom 5, Customer 1 rated it < 3, and NEVER ordered it.
        result = Solution.get_customers_rated_but_not_ordered()
        self.assertEqual(result, [1])

    def test_deep_transitive_graph_cycles(self):
        # A ~ B, B ~ C, C ~ A (Cycle). D is isolated.
        for i in range(1, 5):
            Solution.add_customer(Customer(i, f"User {i}", 25, "0500000000"))
            Solution.add_dish(Dish(i, f"Dish {i}00", 10.0, True))
            Solution.add_order(Order(i, datetime.now(), 0.0, "ValidAddr", 0.0))
            Solution.customer_placed_order(i, i)

        # Link A & B via Dish 1
        Solution.order_contains_dish(1, 1, 1);
        Solution.customer_rated_dish(1, 1, 5)
        Solution.order_contains_dish(2, 1, 1);
        Solution.customer_rated_dish(2, 1, 5)

        # Link B & C via Dish 2
        Solution.order_contains_dish(2, 2, 1);
        Solution.customer_rated_dish(2, 2, 5)
        Solution.order_contains_dish(3, 2, 1);
        Solution.customer_rated_dish(3, 2, 5)

        # Link C & A via Dish 3 (Cycle)
        Solution.order_contains_dish(3, 3, 1);
        Solution.customer_rated_dish(3, 3, 5)
        Solution.order_contains_dish(1, 3, 1);
        Solution.customer_rated_dish(1, 3, 5)

        # D rates Dish 4 perfectly, but is isolated
        Solution.order_contains_dish(4, 4, 1);
        Solution.customer_rated_dish(4, 4, 5)

        # C highly rates Dish 4, making it a target for A
        Solution.order_contains_dish(3, 4, 1);
        Solution.customer_rated_dish(3, 4, 4)

        recs = Solution.get_potential_dish_recommendations(1)

        # A should get Dish 4 (via C, and C is reachable via B or directly).
        self.assertIn(4, recs)
        # D is isolated, but Dish 4 was rated by C.

    def test_cumulative_profit_multi_year_isolation(self):
        # Test that profits do not leak between years
        Solution.add_order(Order(1, datetime(2024, 11, 1, 12, 0, 0), 100.0, "ValidAddr", 0.0))
        Solution.add_order(Order(2, datetime(2025, 2, 1, 12, 0, 0), 50.0, "ValidAddr", 0.0))
        Solution.add_order(Order(3, datetime(2026, 1, 1, 12, 0, 0), 200.0, "ValidAddr", 0.0))

        results_2025 = Solution.get_cumulative_profit_per_month(2025)
        profit_dict = {month: profit for month, profit in results_2025}

        # Jan should be 0, not 100
        self.assertEqual(profit_dict.get(1, -1), 0.0)
        # Feb through Dec should be 50.0
        self.assertEqual(profit_dict.get(2, -1), 50.0)
        self.assertEqual(profit_dict.get(12, -1), 50.0)


# ==============================================================================
# SUITE 5: Advanced API - Worth Price Increases Math Check
# ==============================================================================
class Test5_AdvancedAPI_PriceMath(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Solution.drop_tables()
        Solution.create_tables()

    @classmethod
    def tearDownClass(cls):
        Solution.drop_tables()

    def setUp(self):
        Solution.clear_tables()

    def test_complex_price_fluctuations(self):
        Solution.add_dish(Dish(1, "Test Dish", 10.0, True))

        # Era 1: Price = 10. Avg amount = 5. Avg Profit = 50.
        Solution.add_order(Order(1, datetime.now(), 0.0, "ValidAddr", 0.0))
        Solution.order_contains_dish(1, 1, 5)

        # Era 2: Price = 20. Avg amount = 2. Avg Profit = 40.
        Solution.update_dish_price(1, 20.0)
        Solution.add_order(Order(2, datetime.now(), 0.0, "ValidAddr", 0.0))
        Solution.order_contains_dish(2, 1, 2)

        # Era 3: Price = 30. Avg amount = 1.5. Avg Profit = 45.
        Solution.update_dish_price(1, 30.0)
        Solution.add_order(Order(3, datetime.now(), 0.0, "ValidAddr", 0.0))
        Solution.add_order(Order(4, datetime.now(), 0.0, "ValidAddr", 0.0))
        Solution.order_contains_dish(3, 1, 1)
        Solution.order_contains_dish(4, 1, 2)

        # Check at Era 3 (Current price 30, Avg Profit 45):
        # Is there a lower price with HIGHER avg profit?
        # Price 10 had Avg Profit 50. 45 < 50.
        # Therefore, Dish 1 SHOULD be returned.
        result = Solution.get_non_worth_price_increase()
        self.assertIn(1, result)

        # Era 4: Price = 40. Avg amount = 2. Avg profit = 80.
        Solution.update_dish_price(1, 40.0)
        Solution.add_order(Order(5, datetime.now(), 0.0, "ValidAddr", 0.0))
        Solution.order_contains_dish(5, 1, 2)

        # Check at Era 4 (Current price 40, Avg Profit 80):
        # No lower price had an avg profit > 80. Should NOT be returned.
        result = Solution.get_non_worth_price_increase()
        self.assertNotIn(1, result)


class TestExtremeEdgeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Solution.drop_tables()
        Solution.create_tables()

    @classmethod
    def tearDownClass(cls):
        Solution.drop_tables()

    def setUp(self):
        Solution.clear_tables()

    # ==========================================================================
    # 1. THE "GHOST DATA" AND DELETION CASCADE TESTS
    # ==========================================================================
    def test_rating_resurrection_and_deletion(self):
        Solution.add_customer(Customer(1, "Ghoster", 25, "0500000000"))
        Solution.add_dish(Dish(1, "Spooky Soup", 15.0, True))

        # Customer rates dish
        self.assertEqual(Solution.customer_rated_dish(1, 1, 5), ReturnValue.OK)
        self.assertEqual(Solution.customer_rated_dish(1, 1, 4), ReturnValue.ALREADY_EXISTS)

        # Customer deletes rating
        self.assertEqual(Solution.customer_deleted_rating_on_dish(1, 1), ReturnValue.OK)

        # Deleting again should fail
        self.assertEqual(Solution.customer_deleted_rating_on_dish(1, 1), ReturnValue.NOT_EXISTS)

        # Customer rates it again with a new score
        self.assertEqual(Solution.customer_rated_dish(1, 1, 2), ReturnValue.OK)

        # Verify the new rating stuck
        ratings = Solution.get_all_customer_ratings(1)
        self.assertEqual(len(ratings), 1)
        self.assertEqual(ratings[0], (1, 2))

    def test_average_spending_after_order_deletion(self):
        Solution.add_customer(Customer(1, "Big Spender", 30, "0500000001"))
        Solution.add_customer(Customer(2, "Small Spender", 30, "0500000002"))

        # Big spender makes a huge order
        Solution.add_order(Order(1, datetime.now(), 100.0, "ValidAddr", 50.0))
        Solution.customer_placed_order(1, 1)

        # Small spender makes a tiny order
        Solution.add_order(Order(2, datetime.now(), 5.0, "ValidAddr", 0.0))
        Solution.customer_placed_order(2, 2)

        # Currently, Big Spender is max
        self.assertEqual(Solution.get_customers_spent_max_avg_amount_money(), [1])

        # Delete the big order
        Solution.delete_order(1)

        # Now Small Spender should be the max average, because Big Spender has no orders
        self.assertEqual(Solution.get_customers_spent_max_avg_amount_money(), [2])

    # ==========================================================================
    # 2. THE "ZERO VALUE" ANOMALIES
    # ==========================================================================
    def test_zero_amount_dish_in_order(self):
        # The API documentation says amount < 0 is BAD_PARAMS.
        # Therefore, amount == 0 is technically legal.
        Solution.add_customer(Customer(1, "Zeroes", 20, "0500000000"))
        Solution.add_dish(Dish(1, "Airr", 50.0, True))

        Solution.add_order(Order(1, datetime.now(), 10.0, "ValidAddr", 5.0))
        self.assertEqual(Solution.order_contains_dish(1, 1, 0), ReturnValue.OK)

        # Total price should be 10 (fee) + 5 (tip) + (0 * 50) (dishes) = 15.0
        self.assertEqual(Solution.get_order_total_price(1), 15.0)

    # ==========================================================================
    # 3. ABSOLUTE EQUALITY AND TIEBREAKER STRESS TEST
    # ==========================================================================
    def test_universal_tiebreakers_for_top_and_bottom_dishes(self):
        Solution.add_customer(Customer(1, "Neutral", 25, "0500000000"))

        # Add 10 dishes, NO RATINGS. Average rating for ALL is 3.0.
        for i in range(1, 11):
            Solution.add_dish(Dish(i, f"Dish {i}00", 10.0, True))

        # Because all are 3.0, the "Top 5" by ID tiebreaker are: 1, 2, 3, 4, 5
        # The "Bottom 5" by ID tiebreaker are ALSO: 1, 2, 3, 4, 5

        # Customer 1 orders Dish 6. Is it in the Top 5? No.
        Solution.add_order(Order(1, datetime.now(), 0.0, "ValidAddr", 0.0))
        Solution.customer_placed_order(1, 1)
        Solution.order_contains_dish(1, 6, 1)
        self.assertFalse(Solution.did_customer_order_top_rated_dishes(1))

        # Customer 1 leaves a rating of 2 on Dish 5.
        # Dish 5 was in the bottom 5. Customer 1 rated it < 3.
        # BUT Customer 1 HAS ordered Dish 5? No, they only ordered 6.
        Solution.customer_rated_dish(1, 5, 2)

        # Should return Customer 1 because they rated Dish 5 (bottom 5) with a 2, but never ordered it.
        self.assertEqual(Solution.get_customers_rated_but_not_ordered(), [1])

    # ==========================================================================
    # 4. ISOLATED NETWORK CLUSTERS (TRANSITIVE CLOSURE)
    # ==========================================================================
    def test_isolated_recommendation_clusters(self):
        # We will build two entirely separate groups of friends who never overlap.
        for i in range(1, 7):
            Solution.add_customer(Customer(i, f"User {i}", 25, "0500000000"))
            Solution.add_dish(Dish(i, f"Dish {i}00", 10.0, True))
            Solution.add_order(Order(i, datetime.now(), 0.0, "ValidAddr", 0.0))
            Solution.customer_placed_order(i, i)

        # CLUSTER A: Users 1, 2, 3.
        # Connected via Dish 1 and Dish 2.
        Solution.order_contains_dish(1, 1, 1);
        Solution.customer_rated_dish(1, 1, 5)
        Solution.order_contains_dish(2, 1, 1);
        Solution.customer_rated_dish(2, 1, 5)

        Solution.order_contains_dish(2, 2, 1);
        Solution.customer_rated_dish(2, 2, 5)
        Solution.order_contains_dish(3, 2, 1);
        Solution.customer_rated_dish(3, 2, 5)

        # User 3 highly rates Dish 6 (Target for Cluster A)
        Solution.order_contains_dish(3, 6, 1);
        Solution.customer_rated_dish(3, 6, 5)

        # CLUSTER B: Users 4, 5.
        # Connected via Dish 4.
        Solution.order_contains_dish(4, 4, 1);
        Solution.customer_rated_dish(4, 4, 5)
        Solution.order_contains_dish(5, 4, 1);
        Solution.customer_rated_dish(5, 4, 5)

        # User 5 highly rates Dish 7 (Target for Cluster B)
        Solution.add_dish(Dish(7, "Dish 700", 10.0, True))
        Solution.add_order(Order(7, datetime.now(), 0.0, "ValidAddr", 0.0))
        Solution.customer_placed_order(5, 7)  # User 5 makes order 7
        Solution.order_contains_dish(7, 7, 1);
        Solution.customer_rated_dish(5, 7, 5)

        # Execution for User 1 (In Cluster A)
        recs_user1 = Solution.get_potential_dish_recommendations(1)

        # They should get Dish 6 (from User 3 in their cluster)
        self.assertIn(6, recs_user1)

        # They MUST NOT get Dish 7 (from User 5 in the isolated cluster)
        self.assertNotIn(7, recs_user1)

    # ==========================================================================
    # 5. CONFLICTING MULTI-ITEM ORDERS AND REVENUES
    # ==========================================================================
    def test_revenue_logic_over_quantity(self):
        # "revenue is amount * price... a dish sold many times at a low price
        # can lose to a dish sold fewer times at a higher price."
        Solution.add_dish(Dish(1, "Cheap Dish", 10.0, True))
        Solution.add_dish(Dish(2, "Expensive Dish", 100.0, True))

        t_start = datetime(2025, 1, 1)
        t_end = datetime(2025, 1, 31)

        # Cheap dish sold 9 times -> Total revenue 90.0
        Solution.add_order(Order(1, datetime(2025, 1, 10), 0.0, "ValidAddr", 0.0))
        Solution.order_contains_dish(1, 1, 9)

        # Expensive dish sold 1 time -> Total revenue 100.0
        Solution.add_order(Order(2, datetime(2025, 1, 15), 0.0, "ValidAddr", 0.0))
        Solution.order_contains_dish(2, 2, 1)

        profitable = Solution.get_most_profitable_dish_in_period(t_start, t_end)
        self.assertEqual(profitable.get_dish_id(), 2)

if __name__ == '__main__':
    unittest.main()