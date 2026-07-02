from typing import List, Tuple
from psycopg2 import sql
from datetime import date, datetime
import Utility.DBConnector as Connector
from Utility.ReturnValue import ReturnValue
from Utility.Exceptions import DatabaseException
from Business.Customer import Customer, BadCustomer
from Business.Order import Order, BadOrder
from Business.Dish import Dish, BadDish
from Business.OrderDish import OrderDish


# ---------------------------------- CRUD API: ----------------------------------
# Basic database functions


def create_tables() -> None:
    conn = None
    try:
        conn = Connector.DBConnector()
        conn.execute("CREATE TABLE Customers("
                     "cust_id INTEGER PRIMARY KEY NOT NULL,"
                     "name TEXT NOT NULL, "
                     "age INTEGER NOT NULL,"
                     "phone TEXT NOT NULL,"
                     "CHECK(age >= 18) ,"
                     "CHECK(age <= 120),"
                     "CHECK(LENGTH(phone) == 10),"
                     "CHECK(cust_id > 0))")

        conn.execute("CREATE TABLE Orders("
                     "order_id INTEGER PRIMARY KEY NOT NULL,"
                     "date TIMESTAMP NOT NULL, "
                     "delivery_fee DECIMAL NOT NULL,"
                     "delivery_address TEXT NOT NULL,"
                     "tip DECIMAL NOT NULL,"
                     "CHECK(delivery_fee >= 0) ,"
                     "CHECK(LENGTH(delivery_address) >= 5),"
                     "CHECK(tip >= 0),"
                     "CHECK(order_id > 0),"
                     "CHECK(date LIKE '____-__-__ __:__:__'))")

        conn.execute("CREATE TABLE Dish("
                     "dish_id INTEGER PRIMARY KEY NOT NULL,"
                     "name TEXT NOT NULL, "
                     "price DECIMAL NOT NULL,"
                     "is_active  NOT NULL,"
                     "CHECK(LENGTH(name) >= 4),"
                     "CHECK(price > 0),"
                     "CHECK(dish_id > 0))")

        conn.execute("CREATE TABLE Ordered("
                     "order_id INTEGER,"
                     "cust_id INTEGER, "
                     "FOREIGN KEY (order_id) REFERENCES Customers(order_id),"
                     "FOREIGN KEY (cust_id) REFERENCES Customers(cust_id),"
                     "PRIMARY KEY(order_id, cust_id))")

        conn.execute("CREATE TABLE MealContains("
                     "order_id INTEGER,"
                     "dish_id INTEGER, "
                     "amount INTEGER NOT NULL, "
                     "price_upon_order INTEGER NOT NULL, "
                     "FOREIGN KEY (order_id) REFERENCES Customers(order_id),"
                     "FOREIGN KEY (dish_id) REFERENCES Customers(dish_id),"
                     "PRIMARY KEY(order_id, dish_id),"
                     "CHECK(amount >= 0),"
                     "CHECK(price_upon_order > 0))")

        conn.execute("CREATE TABLE Rated("
                     "cust_id INTEGER,"
                     "dish_id INTEGER, "
                     "rating INTEGER NOT NULL, "
                     "FOREIGN KEY (cust_id) REFERENCES Customers(cust_id),"
                     "FOREIGN KEY (dish_id) REFERENCES Customers(dish_id),"
                     "PRIMARY KEY(cust_id, dish_id),"
                     "CHECK(rating >= 1),"
                     "CHECK(rating <= 5))")

    except DatabaseException.ConnectionInvalid as e:
        print(e)
    except DatabaseException.NOT_NULL_VIOLATION as e:
        print(e)
    except DatabaseException.CHECK_VIOLATION as e:
        print(e)
    except DatabaseException.UNIQUE_VIOLATION as e:
        print(e)
    except DatabaseException.FOREIGN_KEY_VIOLATION as e:
        print(e)
    except Exception as e:
        print(e)
    finally:
        # will happen any way after try termination or exception handling
        conn.close()




def clear_tables() -> None:
    conn = None
    try:
        conn = Connector.DBConnector()
        conn.execute("DELETE FROM Ordered;")
        conn.execute("DELETE FROM MealContains;")
        conn.execute("DELETE FROM Rated;")
        conn.execute("DELETE FROM Customers;")
        conn.execute("DELETE FROM Orders;")
        conn.execute("DELETE FROM Dish;")

    except Exception as e:
        print(e)
    finally:
        if conn:
            conn.close()

def drop_tables() -> None:
    conn = None
    try:
        conn = Connector.DBConnector()
        conn.execute("DROP TABLE IF EXISTS Ordered;")
        conn.execute("DROP TABLE IF EXISTS MealContains;")
        conn.execute("DROP TABLE IF EXISTS Rated;")
        conn.execute("DROP TABLE IF EXISTS Customers;")
        conn.execute("DROP TABLE IF EXISTS Orders;")
        conn.execute("DROP TABLE IF EXISTS Dish;")

    except Exception as e:
        print(e)
    finally:
        if conn:
            conn.close()

# CRUD API

def add_customer(customer: Customer) -> ReturnValue:
    # TODO: implement
    pass


def get_customer(customer_id: int) -> Customer:
    # TODO: implement
    pass


def delete_customer(customer_id: int) -> ReturnValue:
    # TODO: implement
    pass


def add_order(order: Order) -> ReturnValue:
    # TODO: implement
    pass


def get_order(order_id: int) -> Order:
    # TODO: implement
    pass


def delete_order(order_id: int) -> ReturnValue:
    # TODO: implement
    pass


def add_dish(dish: Dish) -> ReturnValue:
    # TODO: implement
    pass


def get_dish(dish_id: int) -> Dish:
    # TODO: implement
    pass


def update_dish_price(dish_id: int, price: float) -> ReturnValue:
    # TODO: implement
    pass


def update_dish_active_status(dish_id: int, is_active: bool) -> ReturnValue:
    # TODO: implement
    pass


def customer_placed_order(customer_id: int, order_id: int) -> ReturnValue:
    # TODO: implement
    pass


def get_customer_that_placed_order(order_id: int) -> Customer:
    # TODO: implement
    pass


def order_contains_dish(order_id: int, dish_id: int, amount: int) -> ReturnValue:
    # TODO: implement
    pass


def order_does_not_contain_dish(order_id: int, dish_id: int) -> ReturnValue:
    # TODO: implement
    pass


def get_all_order_items(order_id: int) -> List[OrderDish]:
    # TODO: implement
    pass


def customer_rated_dish(cust_id: int, dish_id: int, rating: int) -> ReturnValue:
    # TODO: implement
    pass


def customer_deleted_rating_on_dish(cust_id: int, dish_id: int) -> ReturnValue:
    # TODO: implement
    pass

def get_all_customer_ratings(cust_id: int) -> List[Tuple[int, int]]:
    # TODO: implement
    pass
# ---------------------------------- BASIC API: ----------------------------------

# Basic API


def get_order_total_price(order_id: int) -> float:
    # TODO: implement
    pass


def get_customers_spent_max_avg_amount_money() -> List[int]:
    # TODO: implement
    pass


def get_most_profitable_dish_in_period(start: datetime, end: datetime) -> Dish:
    # TODO: implement
    pass

def did_customer_order_top_rated_dishes(cust_id: int) -> bool:
    # TODO: implement
    pass


# ---------------------------------- ADVANCED API: ----------------------------------

# Advanced API


def get_customers_rated_but_not_ordered() -> List[int]:
    # TODO: implement
    pass


def get_non_worth_price_increase() -> List[int]:
    # TODO: implement
    pass


def get_cumulative_profit_per_month(year: int) -> List[Tuple[int, float]]:
    # TODO: implement
    pass


def get_potential_dish_recommendations(cust_id: int) -> List[int]:
    # TODO: implement
    pass
