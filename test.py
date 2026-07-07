import unittest
from datetime import datetime

# Adjust these imports based on your actual folder structure
from Business.Customer import Customer, BadCustomer
from Business.Dish import Dish, BadDish
from Business.Order import Order, BadOrder
from Utility.ReturnValue import ReturnValue
import Solution


# ==============================================================================
# SUITE 1: CRUD API (Standard Flow)
# ==============================================================================
class Test1_CRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Solution.drop_tables()
        Solution.create_tables()

    @classmethod
    def tearDownClass(cls):
        Solution.drop_tables()

    def setUp(self):
        Solution.clear_tables()

    def test_customer_crud(self):
        cust = Customer(cust_id=1, full_name="Alice", age=25, phone="0501234567")
        self.assertEqual(Solution.add_customer(cust), ReturnValue.OK)
        self.assertEqual(Solution.add_customer(cust), ReturnValue.ALREADY_EXISTS)

        fetched = Solution.get_customer(1)
        self.assertEqual(fetched.get_full_name(), "Alice")
        self.assertIsInstance(Solution.get_customer(999), BadCustomer)

        self.assertEqual(Solution.delete_customer(1), ReturnValue.OK)
        self.assertEqual(Solution.delete_customer(1), ReturnValue.NOT_EXISTS)

    def test_dish_crud(self):
        dish = Dish(dish_id=1, name="Pasta", price=45.5, is_active=True)
        self.assertEqual(Solution.add_dish(dish), ReturnValue.OK)
        self.assertEqual(Solution.add_dish(dish), ReturnValue.ALREADY_EXISTS)

        self.assertEqual(Solution.update_dish_price(1, 60.0), ReturnValue.OK)
        self.assertEqual(Solution.get_dish(1).get_price(), 60.0)

        self.assertEqual(Solution.update_dish_active_status(1, False), ReturnValue.OK)
        self.assertEqual(Solution.get_dish(1).get_is_active(), False)
        # Cannot update price of inactive dish
        self.assertEqual(Solution.update_dish_price(1, 70.0), ReturnValue.NOT_EXISTS)

    def test_order_crud(self):
        order = Order(order_id=1, date=datetime.now(), delivery_fee=15.0, delivery_address="Haifa St. 10", tip=5.0)
        self.assertEqual(Solution.add_order(order), ReturnValue.OK)
        self.assertEqual(Solution.add_order(order), ReturnValue.ALREADY_EXISTS)

        fetched = Solution.get_order(1)
        self.assertEqual(fetched.get_delivery_address(), "Haifa St. 10")

        self.assertEqual(Solution.delete_order(1), ReturnValue.OK)
        self.assertIsInstance(Solution.get_order(1), BadOrder)

    def test_customer_order_relations(self):
        Solution.add_customer(Customer(cust_id=10, full_name="Dan", age=28, phone="0500000000"))
        Solution.add_order(
            Order(order_id=20, date=datetime.now(), delivery_fee=10.0, delivery_address="Tel Aviv", tip=0.0))

        self.assertEqual(Solution.customer_placed_order(10, 20), ReturnValue.OK)
        self.assertEqual(Solution.get_customer_that_placed_order(20).get_full_name(), "Dan")

        Solution.add_customer(Customer(cust_id=11, full_name="Eli", age=30, phone="0511111111"))
        self.assertEqual(Solution.customer_placed_order(11, 20), ReturnValue.ALREADY_EXISTS)

    def test_order_dish_relations(self):
        Solution.add_dish(Dish(dish_id=100, name="Pizza", price=50.0, is_active=True))
        Solution.add_order(
            Order(order_id=200, date=datetime.now(), delivery_fee=12.0, delivery_address="Jerusalem", tip=10.0))

        self.assertEqual(Solution.order_contains_dish(200, 100, 2), ReturnValue.OK)
        self.assertEqual(Solution.order_contains_dish(200, 100, 1), ReturnValue.ALREADY_EXISTS)

        items = Solution.get_all_order_items(200)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].get_dish_id(), 100)

        self.assertEqual(Solution.order_does_not_contain_dish(200, 100), ReturnValue.OK)
        self.assertEqual(len(Solution.get_all_order_items(200)), 0)

    def test_customer_ratings(self):
        Solution.add_customer(Customer(cust_id=1, full_name="Fiona", age=25, phone="0501234567"))
        Solution.add_dish(Dish(dish_id=1, name="Salad", price=30.0, is_active=True))
        Solution.add_dish(Dish(dish_id=2, name="Soup", price=20.0, is_active=True))

        self.assertEqual(Solution.customer_rated_dish(1, 1, 5), ReturnValue.OK)
        self.assertEqual(Solution.customer_rated_dish(1, 2, 4), ReturnValue.OK)
        self.assertEqual(Solution.customer_rated_dish(1, 1, 3), ReturnValue.ALREADY_EXISTS)

        ratings = Solution.get_all_customer_ratings(1)
        self.assertEqual(len(ratings), 2)
        self.assertEqual(Solution.customer_deleted_rating_on_dish(1, 1), ReturnValue.OK)


# ==============================================================================
# SUITE 2: Constraints & Cascading Operations
# ==============================================================================
class Test2_ConstraintsAndCascades(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Solution.drop_tables()
        Solution.create_tables()

    @classmethod
    def tearDownClass(cls):
        Solution.drop_tables()

    def setUp(self):
        Solution.clear_tables()

    def test_customer_constraints(self):
        self.assertEqual(Solution.add_customer(Customer(cust_id=1, full_name="A", age=17, phone="0501234567")),
                         ReturnValue.BAD_PARAMS)
        self.assertEqual(Solution.add_customer(Customer(cust_id=2, full_name="B", age=121, phone="0501234567")),
                         ReturnValue.BAD_PARAMS)
        self.assertEqual(Solution.add_customer(Customer(cust_id=3, full_name="C", age=25, phone="050123456")),
                         ReturnValue.BAD_PARAMS)

    def test_dish_constraints(self):
        self.assertEqual(Solution.add_dish(Dish(dish_id=1, name="Pie", price=10.0, is_active=True)),
                         ReturnValue.BAD_PARAMS)
        self.assertEqual(Solution.add_dish(Dish(dish_id=2, name="Cake", price=0.0, is_active=True)),
                         ReturnValue.BAD_PARAMS)

    def test_order_constraints(self):
        self.assertEqual(Solution.add_order(
            Order(order_id=1, date=datetime.now(), delivery_fee=-1.0, delivery_address="Haifa 10", tip=5.0)),
                         ReturnValue.BAD_PARAMS)
        self.assertEqual(Solution.add_order(
            Order(order_id=2, date=datetime.now(), delivery_fee=10.0, delivery_address="Tel", tip=5.0)),
                         ReturnValue.BAD_PARAMS)

    def test_cascading_deletes(self):
        Solution.add_customer(Customer(cust_id=100, full_name="Test User", age=25, phone="0501234567"))
        Solution.add_dish(Dish(dish_id=200, name="Burger", price=50.0, is_active=True))
        Solution.add_order(
            Order(order_id=300, date=datetime.now(), delivery_fee=10.0, delivery_address="Haifa 10", tip=5.0))

        Solution.customer_placed_order(100, 300)
        Solution.order_contains_dish(300, 200, 2)
        Solution.customer_rated_dish(100, 200, 5)

        Solution.delete_customer(100)

        # Deleting customer should set cust_id to NULL in Orders, but order remains
        self.assertNotIsInstance(Solution.get_order(300), BadOrder)
        self.assertIsInstance(Solution.get_customer_that_placed_order(300), BadCustomer)
        # Deleting customer cascades to Customer_Ratings
        self.assertEqual(len(Solution.get_all_customer_ratings(100)), 0)

        # Deleting order cascades to Order_Items
        Solution.delete_order(300)
        self.assertEqual(len(Solution.get_all_order_items(300)), 0)


# ==============================================================================
# SUITE 3: Basic API (Standard Flow)
# ==============================================================================
class Test3_BasicAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Solution.drop_tables()
        Solution.create_tables()

    @classmethod
    def tearDownClass(cls):
        Solution.drop_tables()

    def setUp(self):
        Solution.clear_tables()
        # Seed standard data
        Solution.add_customer(Customer(cust_id=1, full_name="John", age=25, phone="0501234567"))
        Solution.add_dish(Dish(dish_id=1, name="Pizza Margherita", price=50.0, is_active=True))
        Solution.add_order(
            Order(order_id=1, date=datetime(2023, 1, 15, 12, 0, 0), delivery_fee=15.0, delivery_address="123 Main St",
                  tip=10.0))
        Solution.customer_placed_order(1, 1)
        Solution.order_contains_dish(1, 1, 2)

    def test_get_order_total_price(self):
        # 15(fee) + 10(tip) + (50.0 * 2)(dish) = 125.0
        self.assertEqual(Solution.get_order_total_price(1), 125.0)

    def test_get_customers_spent_max_avg_amount_money(self):
        max_spenders = Solution.get_customers_spent_max_avg_amount_money()
        self.assertEqual(len(max_spenders), 1)
        self.assertEqual(max_spenders[0], 1)

    def test_get_most_profitable_dish_in_period(self):
        profitable_dish = Solution.get_most_profitable_dish_in_period(datetime(2023, 1, 1), datetime(2023, 3, 1))
        self.assertEqual(profitable_dish.get_dish_id(), 1)


# ==============================================================================
# SUITE 4: Advanced API (Standard Flow)
# ==============================================================================
class Test4_AdvancedAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Solution.drop_tables()
        Solution.create_tables()

    @classmethod
    def tearDownClass(cls):
        Solution.drop_tables()

    def setUp(self):
        Solution.clear_tables()

    def test_get_non_worth_price_increase(self):
        """Test based exactly on the example in the homework PDF."""
        # Active dish with ID 1 currently costs 50 shekels.
        Solution.add_dish(Dish(dish_id=1, name="Fancy Dish", price=50.0, is_active=True))

        # Create Historical Orders with old price 40
        Solution.update_dish_price(1, 40.0)
        Solution.add_order(Order(order_id=3, date=datetime.now(), delivery_fee=0, delivery_address="Addr 3", tip=0))
        Solution.add_order(Order(order_id=4, date=datetime.now(), delivery_fee=0, delivery_address="Addr 4", tip=0))
        Solution.order_contains_dish(3, 1, 2)  # amount 2, price 40
        Solution.order_contains_dish(4, 1, 2)  # amount 2, price 40
        # Historical avg profit per order = ((2+2)/2) * 40 = 80

        # Create Current Orders with new price 50
        Solution.update_dish_price(1, 50.0)
        Solution.add_order(Order(order_id=1, date=datetime.now(), delivery_fee=0, delivery_address="Addr 1", tip=0))
        Solution.add_order(Order(order_id=2, date=datetime.now(), delivery_fee=0, delivery_address="Addr 2", tip=0))
        Solution.order_contains_dish(1, 1, 1)  # amount 1, price 50
        Solution.order_contains_dish(2, 1, 2)  # amount 2, price 50
        # Current avg profit per order = ((1+2)/2) * 50 = 75

        # 75 < 80, so Dish 1 should be returned
        result = Solution.get_non_worth_price_increase()
        self.assertIn(1, result)

    def test_get_potential_dish_recommendations(self):
        """Test based exactly on the transitive closure example in the homework PDF."""
        # Add 4 customers
        for i in range(1, 5):
            Solution.add_customer(Customer(cust_id=i, full_name=f"Cust {i}", age=20, phone="0500000000"))
        # Add 7 dishes
        for i in range(1, 8):
            Solution.add_dish(Dish(dish_id=i, name=f"Dish {i}00", price=10.0, is_active=True))

        # Cust 1 rated and ordered 1, 2, 3 (rating >= 4)
        Solution.add_order(Order(order_id=1, date=datetime.now(), delivery_fee=0, delivery_address="Address", tip=0))
        Solution.customer_placed_order(1, 1)
        for d in [1, 2, 3]:
            Solution.order_contains_dish(1, d, 1)
            Solution.customer_rated_dish(1, d, 5)

        # Cust 2 rated dishes 1, 4 (rating >= 4)
        Solution.customer_rated_dish(2, 1, 4)
        Solution.customer_rated_dish(2, 4, 4)

        # Cust 3 rated dishes 4, 5, 7 (rating >= 4)
        Solution.customer_rated_dish(3, 4, 5)
        Solution.customer_rated_dish(3, 5, 5)
        Solution.customer_rated_dish(3, 7, 5)

        # Cust 4 rated dish 6 (rating >= 4) - Isolated
        Solution.customer_rated_dish(4, 6, 4)

        # Expected Similar Users to Cust 1:
        # Cust 2 (via Dish 1)
        # Cust 3 (via Cust 2 and Dish 4)
        # Dishes rated >= 4 by similar users: 1, 4, 5, 7
        # Cust 1 already ordered 1 (and 2, 3). So recommendations: 4, 5, 7.
        recs = Solution.get_potential_dish_recommendations(1)
        self.assertEqual(sorted(recs), [4, 5, 7])

    def test_get_cumulative_profit_per_month(self):
        # Changed "Add" (3 chars) to "123 Main St" (11 chars) to pass your DB constraints!
        Solution.add_order(
            Order(order_id=1, date=datetime(2023, 1, 15, 12, 0, 0), delivery_fee=15.0, delivery_address="123 Main St",
                  tip=10.0))
        Solution.add_order(
            Order(order_id=2, date=datetime(2023, 2, 20, 18, 30, 0), delivery_fee=10.0, delivery_address="123 Main St",
                  tip=5.0))

        results = Solution.get_cumulative_profit_per_month(2023)
        profit_dict = {month: profit for month, profit in results}

        self.assertEqual(profit_dict.get(1, 0), 25.0)
        self.assertEqual(profit_dict.get(2, 0), 40.0)  # 25 + 15
        self.assertEqual(profit_dict.get(12, 0), 40.0)  # Maintains till year-end

# ==============================================================================
# SUITE 5: Basic API (Edge Cases)
# ==============================================================================
class Test5_BasicAPIEdgeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Solution.drop_tables()
        Solution.create_tables()

    @classmethod
    def tearDownClass(cls):
        Solution.drop_tables()

    def setUp(self):
        Solution.clear_tables()

    def test_max_avg_spending_ties_and_null_customers(self):
        c1 = Customer(cust_id=1, full_name="A", age=20, phone="0500000001")
        c2 = Customer(cust_id=2, full_name="B", age=20, phone="0500000002")
        Solution.add_customer(c1)
        Solution.add_customer(c2)

        Solution.add_order(
            Order(order_id=1, date=datetime.now(), delivery_fee=10.0, delivery_address="Address X", tip=0.0))

        Solution.customer_placed_order(1, 1)

        Solution.add_order(
            Order(order_id=2, date=datetime.now(), delivery_fee=10.0, delivery_address="Address Y", tip=0.0))
        Solution.customer_placed_order(2, 2)

        # Huge order unassigned to customer (should be ignored in calculation)
        Solution.add_order(
            Order(order_id=4, date=datetime.now(), delivery_fee=1000.0, delivery_address="Null Island", tip=0.0))

        result = Solution.get_customers_spent_max_avg_amount_money()
        self.assertEqual(result, [1, 2])  # Both tie for 10.0 average

    def test_profitable_dish_ties_and_historical_pricing(self):
        Solution.add_dish(Dish(dish_id=10, name="Steak", price=100.0, is_active=True))
        Solution.add_dish(Dish(dish_id=20, name="Fries", price=50.0, is_active=True))

        Solution.update_dish_price(10, 20.0)
        Solution.update_dish_price(20, 20.0)

        Solution.add_order(
            Order(order_id=1, date=datetime(2023, 6, 1, 12, 0, 0), delivery_fee=0.0, delivery_address="Address A",
                  tip=0.0))
        Solution.order_contains_dish(1, 10, 1)
        Solution.order_contains_dish(1, 20, 1)

        # Update prices drastically, should not affect historical calculation
        Solution.update_dish_price(10, 999.0)
        Solution.update_dish_price(20, 1.0)

        profitable = Solution.get_most_profitable_dish_in_period(datetime(2023, 5, 1), datetime(2023, 7, 1))
        # Both generated 20.0 revenue. Tie breaks to lower ID -> 10
        self.assertEqual(profitable.get_dish_id(), 10)

    def test_top_rated_dishes_unrated_tiebreakers(self):
        """Unrated dishes get 3.0 rating. Lower ID breaks ties."""
        for i in range(1, 7):
            Solution.add_dish(Dish(dish_id=i, name=f"Dish {i}", price=10.0, is_active=True))

        Solution.add_customer(Customer(cust_id=1, full_name="A", age=20, phone="0500000001"))
        Solution.add_customer(Customer(cust_id=2, full_name="B", age=20, phone="0500000002"))

        # Top 5 dishes by ID tiebreaker: 1, 2, 3, 4, 5
        Solution.add_order(
            Order(order_id=1, date=datetime.now(), delivery_fee=0.0, delivery_address="Address A", tip=0.0))
        Solution.customer_placed_order(1, 1)
        Solution.order_contains_dish(1, 6, 1)  # Customer 1 orders Dish 6 (NOT in top 5)

        Solution.add_order(
            Order(order_id=2, date=datetime.now(), delivery_fee=0.0, delivery_address="Address B", tip=0.0))
        Solution.customer_placed_order(2, 2)
        Solution.order_contains_dish(2, 5, 1)  # Customer 2 orders Dish 5 (IN top 5)

        self.assertFalse(Solution.did_customer_order_top_rated_dishes(1))
        self.assertTrue(Solution.did_customer_order_top_rated_dishes(2))


# ==============================================================================
# SUITE 6: Advanced API (Edge Cases)
# ==============================================================================
class Test6_AdvancedAPIEdgeCases(unittest.TestCase):
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
        """Test default 3.0 rating and tiebreakers for bottom 5 dishes."""
        Solution.add_customer(Customer(cust_id=1, full_name="A", age=20, phone="0500000000"))

        for i in range(1, 7):
            Solution.add_dish(Dish(dish_id=i, name=f"Dish {i}00", price=10.0, is_active=True))

        # Give dishes 1 through 5 a rating of 1 to firmly cement them as the bottom 5.
        for i in range(1, 6):
            Solution.customer_rated_dish(1, i, 1)
            # We must also 'order' them so Customer 1 isn't flagged for them
            Solution.add_order(
                Order(order_id=i, date=datetime.now(), delivery_fee=0, delivery_address="ValidAddr", tip=0))
            Solution.customer_placed_order(1, i)
            Solution.order_contains_dish(i, i, 1)

        # NOW Dish 6 gets a 2. Since 2.0 > 1.0, Dish 6 is the 6th worst dish (NOT in bottom 5).
        Solution.customer_rated_dish(1, 6, 2)

        # Customer 1 rated Dish 6 poorly, but because it's not in the bottom 5, it should return 0.
        self.assertEqual(len(Solution.get_customers_rated_but_not_ordered()), 0)

    def test_cumulative_profit_year_with_no_orders(self):
        """Ensures all 12 months return 0.0 if the year has no orders."""
        results = Solution.get_cumulative_profit_per_month(2026)
        self.assertEqual(len(results), 12)
        for month, profit in results:
            self.assertEqual(profit, 0.0)


# ==============================================================================
# SUITE 7: Deep Transitive Closure & Graph Simulation (Advanced API)
# ==============================================================================
class Test7_DeepTransitiveClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Solution.drop_tables()
        Solution.create_tables()

    @classmethod
    def tearDownClass(cls):
        Solution.drop_tables()

    def setUp(self):
        Solution.clear_tables()

    def test_long_chain_of_similar_customers(self):
        """
        Builds a chain: C1 ~ C2 ~ C3 ~ C4 ~ C5.
        C5 highly rates a dish. C1 should get it as a recommendation.
        """
        # Create 6 Customers
        for i in range(1, 7):
            Solution.add_customer(Customer(cust_id=i, full_name=f"User {i}", age=25, phone="0500000000"))

        # Create 10 Dishes
        for i in range(1, 11):
            Solution.add_dish(Dish(dish_id=i, name=f"Dish {i}00", price=10.0, is_active=True))

        # Create orders so they can rate the dishes
        for i in range(1, 7):
            Solution.add_order(
                Order(order_id=i, date=datetime.now(), delivery_fee=0, delivery_address="ValidAddr", tip=0))
            Solution.customer_placed_order(i, i)

        # The Chain Links (Rating >= 4 on the same dish creates similarity)
        # Link 1: C1 and C2 both rate Dish 1 with a 5
        Solution.order_contains_dish(1, 1, 1);
        Solution.customer_rated_dish(1, 1, 5)
        Solution.order_contains_dish(2, 1, 1);
        Solution.customer_rated_dish(2, 1, 5)

        # Link 2: C2 and C3 both rate Dish 2 with a 5
        Solution.order_contains_dish(2, 2, 1);
        Solution.customer_rated_dish(2, 2, 5)
        Solution.order_contains_dish(3, 2, 1);
        Solution.customer_rated_dish(3, 2, 5)

        # Link 3: C3 and C4 both rate Dish 3 with a 5
        Solution.order_contains_dish(3, 3, 1);
        Solution.customer_rated_dish(3, 3, 5)
        Solution.order_contains_dish(4, 3, 1);
        Solution.customer_rated_dish(4, 3, 5)

        # Link 4: C4 and C5 both rate Dish 4 with a 5
        Solution.order_contains_dish(4, 4, 1);
        Solution.customer_rated_dish(4, 4, 5)
        Solution.order_contains_dish(5, 4, 1);
        Solution.customer_rated_dish(5, 4, 5)

        # The Target: C5 highly rates Dish 10.
        Solution.order_contains_dish(5, 10, 1)
        Solution.customer_rated_dish(5, 10, 5)

        # The Noise: C6 (unconnected) highly rates Dish 9.
        Solution.order_contains_dish(6, 9, 1)
        Solution.customer_rated_dish(6, 9, 5)

        # Execute
        recs = Solution.get_potential_dish_recommendations(1)

        # Assertions
        self.assertIn(10, recs, "C1 should receive Dish 10 via the deep transitive chain.")
        self.assertNotIn(9, recs, "C1 should NOT receive Dish 9 because C6 is not in the similarity graph.")
        self.assertNotIn(1, recs, "C1 should NOT receive Dish 1 because they already ordered it.")


# ==============================================================================
# SUITE 8: Multi-Stage Price History (Advanced API)
# ==============================================================================
class Test8_ComplexPriceIncreases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Solution.drop_tables()
        Solution.create_tables()

    @classmethod
    def tearDownClass(cls):
        Solution.drop_tables()

    def setUp(self):
        Solution.clear_tables()

    def test_price_fluctuations_and_inactive_dishes(self):
        # Dish 1: Price goes 10 -> 20. Profit goes down. Should be flagged.
        Solution.add_dish(Dish(dish_id=1, name="Dish 100", price=10.0, is_active=True))
        Solution.add_order(Order(order_id=1, date=datetime.now(), delivery_fee=0, delivery_address="Addr 1", tip=0))
        Solution.order_contains_dish(1, 1, 10)  # 10 items @ 10 = 100 profit

        Solution.update_dish_price(1, 20.0)
        Solution.add_order(Order(order_id=2, date=datetime.now(), delivery_fee=0, delivery_address="Addr 2", tip=0))
        Solution.order_contains_dish(2, 1, 2)  # 2 items @ 20 = 40 profit

        # Dish 2: Price goes 10 -> 20 -> 30. Profit dips at 20, but skyrockets at 30.
        # Should NOT be flagged because CURRENT price (30) profit > old prices.
        Solution.add_dish(Dish(dish_id=2, name="Dish 200", price=10.0, is_active=True))
        Solution.add_order(Order(order_id=3, date=datetime.now(), delivery_fee=0, delivery_address="Addr 3", tip=0))
        Solution.order_contains_dish(3, 2, 10)  # 10 items @ 10 = 100 profit

        Solution.update_dish_price(2, 20.0)
        Solution.add_order(Order(order_id=4, date=datetime.now(), delivery_fee=0, delivery_address="Addr 4", tip=0))
        Solution.order_contains_dish(4, 2, 2)  # 2 items @ 20 = 40 profit (dip)

        Solution.update_dish_price(2, 30.0)
        Solution.add_order(Order(order_id=5, date=datetime.now(), delivery_fee=0, delivery_address="Addr 5", tip=0))
        Solution.order_contains_dish(5, 2, 10)  # 10 items @ 30 = 300 profit (recovery)

        # Dish 3: Price goes 10 -> 20. Profit goes down. BUT dish is marked inactive.
        # Should NOT be flagged because the assignment says "active dishes only".
        Solution.add_dish(Dish(dish_id=3, name="Dish 300", price=10.0, is_active=True))
        Solution.add_order(Order(order_id=6, date=datetime.now(), delivery_fee=0, delivery_address="Addr 6", tip=0))
        Solution.order_contains_dish(6, 3, 10)

        Solution.update_dish_price(3, 20.0)
        Solution.add_order(Order(order_id=7, date=datetime.now(), delivery_fee=0, delivery_address="Addr 7", tip=0))
        Solution.order_contains_dish(7, 3, 2)
        Solution.update_dish_active_status(3, False)

        result = Solution.get_non_worth_price_increase()

        self.assertIn(1, result, "Dish 1 should be returned. Current price yields lower profit.")
        self.assertNotIn(2, result, "Dish 2 should NOT be returned. Current price yields higher profit.")
        self.assertNotIn(3, result, "Dish 3 should NOT be returned. It is inactive.")


# ==============================================================================
# SUITE 9: Time-Series Data Gaps & Cumulative Profits
# ==============================================================================
class Test9_TimeSeriesProfits(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Solution.drop_tables()
        Solution.create_tables()

    @classmethod
    def tearDownClass(cls):
        Solution.drop_tables()

    def setUp(self):
        Solution.clear_tables()

    def test_profit_gaps_and_year_isolation(self):
        """
        Tests if the running total correctly carries over empty months
        and explicitly ignores orders from previous/future years.
        """
        # Order in Dec of previous year (Should be IGNORED)
        Solution.add_order(
            Order(order_id=1, date=datetime(2022, 12, 31, 23, 59, 59), delivery_fee=100.0, delivery_address="ValidAddr",
                  tip=0))

        # Order in Feb of current year
        Solution.add_order(
            Order(order_id=2, date=datetime(2023, 2, 15, 12, 0, 0), delivery_fee=20.0, delivery_address="ValidAddr",
                  tip=5.0))

        # Order in May of current year (Pure tip and delivery, no items)
        Solution.add_order(
            Order(order_id=3, date=datetime(2023, 5, 10, 12, 0, 0), delivery_fee=10.0, delivery_address="ValidAddr",
                  tip=40.0))

        results = Solution.get_cumulative_profit_per_month(2023)
        profit_dict = {month: profit for month, profit in results}

        self.assertEqual(profit_dict.get(1, -1), 0.0, "Jan should be 0.")
        self.assertEqual(profit_dict.get(2, -1), 25.0, "Feb should be 25.")
        self.assertEqual(profit_dict.get(3, -1), 25.0, "Mar should carry over Feb's 25.")
        self.assertEqual(profit_dict.get(4, -1), 25.0, "Apr should carry over Feb's 25.")
        self.assertEqual(profit_dict.get(5, -1), 75.0, "May adds 50. Total should be 75.")
        self.assertEqual(profit_dict.get(12, -1), 75.0, "Dec should carry over May's 75.")


# ==============================================================================
# SUITE 10: Dynamic Rank Shuffling
# ==============================================================================
class Test10_DynamicRankShuffling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Solution.drop_tables()
        Solution.create_tables()

    @classmethod
    def tearDownClass(cls):
        Solution.drop_tables()

    def setUp(self):
        Solution.clear_tables()

    def test_dynamic_top_5_shifting(self):
        """
        Customer orders a mediocre dish. Is not in Top 5 -> Returns False.
        Then, new ratings come in that propel that dish into the Top 5.
        Checking again should -> Return True.
        """
        for i in range(1, 11):
            Solution.add_dish(Dish(dish_id=i, name=f"Dish {i}00", price=10.0, is_active=True))

        Solution.add_customer(Customer(cust_id=1, full_name="A", age=25, phone="0500000000"))
        Solution.add_customer(Customer(cust_id=2, full_name="B", age=25, phone="0500000000"))

        # Cust 1 orders Dish 10
        Solution.add_order(Order(order_id=1, date=datetime.now(), delivery_fee=0, delivery_address="ValidAddr", tip=0))
        Solution.customer_placed_order(1, 1)
        Solution.order_contains_dish(1, 10, 1)

        # Currently all dishes are unrated (3.0). Tiebreakers put IDs 1-5 in Top 5.
        # Dish 10 is NOT in Top 5.
        self.assertFalse(Solution.did_customer_order_top_rated_dishes(1), "Dish 10 should not be in Top 5 yet.")

        # Now, Cust 2 rates Dish 10 perfectly. Average rating becomes 5.0.
        # Dish 10 shoots to #1.
        Solution.add_order(Order(order_id=2, date=datetime.now(), delivery_fee=0, delivery_address="ValidAddr", tip=0))
        Solution.customer_placed_order(2, 2)
        Solution.order_contains_dish(2, 10, 1)
        Solution.customer_rated_dish(2, 10, 5)

        # Checking again.
        self.assertTrue(Solution.did_customer_order_top_rated_dishes(1), "Dish 10 is now #1, should return True.")


if __name__ == '__main__':
    unittest.main()