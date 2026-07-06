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
                     "CHECK(LENGTH(phone) = 10),"
                     "CHECK(cust_id > 0))")

        conn.execute("CREATE TABLE Orders("
                     "order_id INTEGER PRIMARY KEY NOT NULL,"
                     "date TIMESTAMP(0) NOT NULL, "
                     "delivery_fee DECIMAL NOT NULL,"
                     "delivery_address TEXT NOT NULL,"
                     "tip DECIMAL NOT NULL,"
                     "CHECK(delivery_fee >= 0) ,"
                     "CHECK(LENGTH(delivery_address) >= 5),"
                     "CHECK(tip >= 0),"
                     "CHECK(order_id > 0))")

        conn.execute("CREATE TABLE Dish("
                     "dish_id INTEGER PRIMARY KEY NOT NULL,"
                     "name TEXT NOT NULL, "
                     "price DECIMAL NOT NULL,"
                     "is_active DECIMAL NOT NULL," #YUVAL WILL FIX LATER
                     "CHECK(LENGTH(name) >= 4),"
                     "CHECK(price > 0),"
                     "CHECK(dish_id > 0))")

        conn.execute("CREATE TABLE Ordered("
                     "order_id INTEGER,"
                     "cust_id INTEGER, "
                     "FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,"
                     "FOREIGN KEY (cust_id) REFERENCES Customers(cust_id) ON DELETE CASCADE,"
                     "PRIMARY KEY(order_id, cust_id))")

        conn.execute("CREATE TABLE MealContains("
                     "order_id INTEGER,"
                     "dish_id INTEGER, "
                     "amount INTEGER NOT NULL, "
                     "price_upon_order INTEGER NOT NULL, "
                     "FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,"
                     "FOREIGN KEY (dish_id) REFERENCES Dish(dish_id),"
                     "PRIMARY KEY(order_id, dish_id),"
                     "CHECK(amount >= 0),"
                     "CHECK(price_upon_order > 0))")

        conn.execute("CREATE TABLE Rated("
                     "cust_id INTEGER,"
                     "dish_id INTEGER, "
                     "rating INTEGER NOT NULL, "
                     "FOREIGN KEY (cust_id) REFERENCES Customers(cust_id) ON DELETE CASCADE,"
                     "FOREIGN KEY (dish_id) REFERENCES Dish(dish_id),"
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
    conn = None
    try:
        conn = Connector.DBConnector()
        query = (sql.SQL("INSERT INTO Customers (cust_id, name, age, phone) "
                 "VALUES ({_id},{_name},{_age},{_phone})")
                 .format(_id=sql.Literal(customer.get_cust_id()),
                         _name=sql.Literal(customer.get_full_name()),
                         _age=sql.Literal(customer.get_age()),
                         _phone=sql.Literal(customer.get_phone())))
        conn.execute(query)
        return ReturnValue.OK

    except DatabaseException.NOT_NULL_VIOLATION:
        return ReturnValue.BAD_PARAMS
    except DatabaseException.CHECK_VIOLATION:
        return ReturnValue.BAD_PARAMS
    except DatabaseException.UNIQUE_VIOLATION:
        return ReturnValue.ALREADY_EXISTS
    except Exception as e:
        return ReturnValue.ERROR

    finally:
        if conn:
            conn.close()

def get_customer(customer_id: int) -> Customer:
    conn = None
    try:
        conn = Connector.DBConnector()
        query = (sql.SQL("SELECT cust_id, name, age, phone "
                        "FROM Customers WHERE cust_id = {_id};")
                 .format(_id=sql.Literal(customer_id)))
        res = conn.execute(query)

        if res is not None and len(res) > 0:
            res = res[1]
            ret_val = Customer()
            ret_val.set_cust_id(res["cust_id"][0])
            ret_val.set_full_name(res["name"][0])
            ret_val.set_age(res["age"][0])
            ret_val.set_phone(res["phone"][0])

            return ret_val
        else:
            return BadCustomer()
    except Exception as e:
        print(e)
        return BadCustomer()
    finally:
        if conn:
            conn.close()


def delete_customer(customer_id: int) -> ReturnValue:
    conn = None
    rows_effected = 0
    try:
        conn = Connector.DBConnector()
        query = (sql.SQL("DELETE FROM Customers WHERE cust_id={0}")
                 .format(sql.Literal(customer_id)))
        rows_effected, _ = conn.execute(query)

        if rows_effected == 0:
            return ReturnValue.NOT_EXISTS
        return ReturnValue.OK
    except DatabaseException as e:
        return ReturnValue.ERROR



def add_order(order: Order) -> ReturnValue:
    # implement
    conn = None
    try:
        conn = Connector.DBConnector()
        # add an order to the database
        query = (sql.SQL("INSERT INTO Orders (order_id, date, delivery_fee, delivery_address, tip) "
                 "VALUES ({_id},{_date},{_delivery_fee},{_delivery_address},{_tip})")
                 .format(_id=sql.Literal(order.get_order_id()),
                         _date=sql.Literal(order.get_date()),
                         _delivery_fee=sql.Literal(order.get_delivery_fee()),
                         _delivery_address=sql.Literal(order.get_delivery_address()),
                         _tip=sql.Literal(order.get_tip())))
        conn.execute(query)
        return ReturnValue.OK

    except DatabaseException.NOT_NULL_VIOLATION:
        return ReturnValue.BAD_PARAMS
    except DatabaseException.CHECK_VIOLATION:
        return ReturnValue.BAD_PARAMS
    except DatabaseException.UNIQUE_VIOLATION:
        return ReturnValue.ALREADY_EXISTS
    except Exception as e:
        return ReturnValue.ERROR
    finally:
        if conn:
            conn.close()


def get_order(order_id: int) -> Order:
    cone = None
    try:
        conn = Connector.DBConnector()
        query = (sql.SQL("SELECT order_id, date, delivery_fee, delivery_address, tip "
                        "FROM Orders WHERE order_id = {_id};")
                 .format(_id=sql.Literal(order_id)))
        res = conn.execute(query)

        if res is not None and len(res) > 0:
            res = res[1]
            ret_val = Order()
            ret_val.set_order_id(res["order_id"][0])
            ret_val.set_date(res["date"][0])
            ret_val.set_delivery_fee(res["delivery_fee"][0])
            ret_val.set_delivery_address(res["delivery_address"][0])
            ret_val.set_tip(res["tip"][0])

            return ret_val
        else:
            return BadOrder()
    except Exception as e:
        return BadOrder()
    finally:
        if conn:
            conn.close()


def delete_order(order_id: int) -> ReturnValue:
    conn = None
    rows_effected = 0
    try:
        conn = Connector.DBConnector()
        query = sql.SQL("DELETE FROM Orders WHERE order_id = {_id}").format(_id=sql.Literal(order_id))
        rows_effected, _ = conn.execute(query)
        return ReturnValue.OK
    except Exception as e:
        print(e)
        return ReturnValue.ERROR
    finally:
        if conn:
            conn.close()


def add_dish(dish: Dish) -> ReturnValue:
    conn = None
    try:
        conn = Connector.DBConnector()
        query = (sql.SQL("INSERT INTO Dish (dish_id, name, price, is_active) "
                 "VALUES ({_id},{_name},{_price},{_is_active})")
                 .format(_id=sql.Literal(dish.get_dish_id()),
                         _name=sql.Literal(dish.get_name()),
                         _price=sql.Literal(dish.get_price()),
                         _is_active=sql.Literal(dish.get_is_active())))
        conn.execute(query)
        return ReturnValue.OK

    except DatabaseException.NOT_NULL_VIOLATION:
        return ReturnValue.BAD_PARAMS
    except DatabaseException.CHECK_VIOLATION:
        return ReturnValue.BAD_PARAMS
    except DatabaseException.UNIQUE_VIOLATION:
        return ReturnValue.ALREADY_EXISTS
    except Exception as e:
        return ReturnValue.ERROR

    finally:
        if conn:
            conn.close()


def get_dish(dish_id: int) -> Dish:
    conn = None
    try:
        conn = Connector.DBConnector()
        query = (sql.SQL("SELECT dish_id, name, price, is_active "
                        "FROM Dish WHERE dish_id = {_id};")
                 .format(_id=sql.Literal(dish_id)))
        res = conn.execute(query)

        if res is not None and len(res) > 0:
            res = res[1]
            ret_val = Dish()
            ret_val.set_dish_id(res["dish_id"][0])
            ret_val.set_name(res["name"][0])
            ret_val.set_price(res["price"][0])
            ret_val.set_is_active(res["is_active"][0])

            return ret_val
        else:
            return BadDish()
    except Exception as e:
        print(e)
        return BadDish()
    finally:
        if conn:
            conn.close()


def update_dish_price(dish_id: int, price: float) -> ReturnValue:
    # TODO: implement
    pass


def update_dish_active_status(dish_id: int, is_active: bool) -> ReturnValue:
    conn = None
    try:
        conn = Connector.DBConnector()
        query = (sql.SQL("UPDATE Dish" \
                        " SET is_active = {_is_active}" \
                        " WHERE dish_id = {dish_id};").format(
                                        _is_active=sql.Literal(is_active),
                                        dish_id=sql.Literal(dish_id)))
        rows_effected, _ = conn.execute(query)
        if rows_effected == 0:
                return ReturnValue.NOT_EXISTS
        return ReturnValue.OK
    except Exception as e:
        return ReturnValue.ERROR
    finally:
        if conn:
            conn.close()


def customer_placed_order(customer_id: int, order_id: int) -> ReturnValue:



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


if __name__ == '__main__':
    create_tables()

    dish = Dish(10,"itamar",50, 1)
    dish = Dish(20,"itamar",50, 1)
    add_dish(dish)
    print(get_dish(20))
    clear_tables()
    drop_tables()