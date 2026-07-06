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
                     "is_active BOOLEAN NOT NULL," #YUVAL WILL FIX LATER
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


        query = (sql.SQL("""
                    CREATE VIEW customerOrderedDishes AS
                    SELECT DISTINCT
                    Ordered.cust_id,
                    MealContains.dish_id
                    FROM 
                    Ordered
                    INNER JOIN 
                    MealContains     
                    ON 
                    Ordered.order_id = MealContains.order_id;
                    """))
        conn.execute(query)

        query = (sql.SQL("CREATE VIEW OrderView AS"
            " SELECT order_id, SUM(amount*price_upon_order) AS bill"
            " FROM MealContains"
            " GROUP BY order_id"))
        conn.execute(query)

        #for 4.4.2
        query = (sql.SQL("CREATE VIEW DishNotWorthCandidates AS SELECT DISTINCT dish_id FROM "
                         "(SELECT Dish.dish_id FROM Dish INNER JOIN MealContains ON Dish.dish_id = MealContains.dish_id WHERE Dish.price = MealContains.price_upon_order)"
                         "INTERSECT "
                         "(SELECT Dish.dish_id FROM Dish INNER JOIN MealContains ON Dish.dish_id = MealContains.dish_id WHERE Dish.price > MealContains.price_upon_order)"
                         "INTERSECT "
                         "(SELECT dish_id FROM Dish WHERE is_active = True)"))
        conn.execute(query)
        #for 4.4.2
        query = (sql.SQL("""CREATE VIEW avgPerPriceTable AS
                         (SELECT MealContains.dish_id, price_upon_order,price, AVG(amount)*price_upon_order as avgPerPrice FROM  
            Dish INNER JOIN  MealContains ON MealContains.dish_id = Dish.dish_id
            INNER JOIN DishNotWorthCandidates ON DishNotWorthCandidates.dish_id = MealContains.dish_id
            GROUP BY price_upon_order, MealContains.dish_id, Dish.price)"""))
        conn.execute(query)


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
        conn.execute("DROP TABLE IF EXISTS Ordered CASCADE;")
        conn.execute("DROP TABLE IF EXISTS MealContains CASCADE;")
        conn.execute("DROP TABLE IF EXISTS Rated;")
        conn.execute("DROP TABLE IF EXISTS Customers;")
        conn.execute("DROP TABLE IF EXISTS Orders ;")
        conn.execute("DROP TABLE IF EXISTS Dish CASCADE;")

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
                         _date=sql.Literal(order.get_datetime()),
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
            ret_val.set_datetime(res["date"][0])
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
    conn = None
    try:
        conn = Connector.DBConnector()
        query = (sql.SQL("UPDATE Dish"
                        " SET price = {_price} WHERE dish_id = {_dish_id} "
                         "AND is_active = True;")
                 .format(_price=sql.Literal(price),
                         _dish_id = sql.Literal(dish_id)))
        rows_effected, _ = conn.execute(query)
        if rows_effected == 0:
            return ReturnValue.NOT_EXISTS
    except DatabaseException.NOT_NULL_VIOLATION:
        return ReturnValue.BAD_PARAMS
    except DatabaseException.CHECK_VIOLATION:
        return ReturnValue.BAD_PARAMS
    finally:
        if conn:
            conn.close()


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


###############################################################################################################################
def order_contains_dish(order_id: int, dish_id: int, amount: int) -> ReturnValue:
    conn = None
    try:
        conn = Connector.DBConnector()

        query_cont = (sql.SQL(
            "INSERT INTO MealContains (order_id, dish_id, amount, price_upon_order) "
            "SELECT {lit_order_id}, {lit_dish_id}, {lit_amount}, price "
            "FROM Dish "
            "WHERE dish_id = {lit_dish_id} AND is_active = TRUE;"
        ).format(
            lit_order_id=sql.Literal(order_id),
            lit_dish_id=sql.Literal(dish_id),
            lit_amount=sql.Literal(amount)
        ))
        conn.execute(query_cont)
        return ReturnValue.OK

    except DatabaseException.NOT_NULL_VIOLATION:
        return ReturnValue.BAD_PARAMS
    except DatabaseException.CHECK_VIOLATION:
        return ReturnValue.BAD_PARAMS
    except DatabaseException.FOREIGN_KEY_VIOLATION:
            return ReturnValue.NOT_EXISTS
    except DatabaseException.UNIQUE_VIOLATION:
        return ReturnValue.ALREADY_EXISTS
    except Exception as e:
        print(e)
        return ReturnValue.ERROR

    finally:
        if conn:
            conn.close()


def order_does_not_contain_dish(order_id: int, dish_id: int) -> ReturnValue:
    if order_id <= 0 or dish_id <= 0: #illegal id's
        return ReturnValue.NOT_EXISTS

    conn = None
    rows_effected = 0
    try:
        conn = Connector.DBConnector()
        query = (sql.SQL("DELETE FROM MealContains WHERE order_id = {_order_id} AND dish_id = {_dish_id}")
                 .format(_order_id=sql.Literal(order_id), _dish_id=sql.Literal(dish_id)))
        rows_effected, _ = conn.execute(query)
        if rows_effected == 0:
            return ReturnValue.NOT_EXISTS
        return ReturnValue.OK
    except Exception as e:
        print(e)
        return ReturnValue.ERROR
    finally:
        if conn:
            conn.close()



def get_all_order_items(order_id: int) -> List[OrderDish]:
    conn = None
    ret_val = []
    try:
        conn = Connector.DBConnector()
        query = (sql.SQL("SELECT dish_id, amount, price_upon_order "
                        "FROM MealContains WHERE order_id = {_order_id}"
                         " ORDER BY dish_id ASC;")
                 .format(_order_id=sql.Literal(order_id)))
        res = conn.execute(query)
        res = res[1]
        for curr in enumerate(res):
            print(curr[1]['dish_id'])
            ret_val.append(OrderDish(curr[1]['dish_id'], curr[1]['amount'], curr[1]['price_upon_order'] ))
        return ret_val
    except Exception as e:
        print(e)
        return []
    finally:
        if conn:
            conn.close()

####################################################################################################################################

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
    conn = None
    ret_val = []
    try:
        conn = Connector.DBConnector()
        query = (sql.SQL("CREATE VIEW OrderView AS"
            " SELECT order_id, SUM(amount*price_upon_order) AS bill"
            " FROM MealContains"
            " GROUP BY order_id"))
        conn.execute(query)

        query_cont = sql.SQL("SELECT bill+delivery_fee+tip AS res "
                             "FROM OrderView INNER JOIN Orders "
                             "ON OrderView.order_id = Orders.order_id "
                             "WHERE Orders.order_id = {_order_id}").format(_order_id=sql.Literal(order_id))
        res = ((conn.execute(query_cont)[1]['res']))
        res = res[0]
        res = float(res)
        return res

    except Exception as e:
        print(e)
        return []
    finally:
        if conn:
            conn.close()


def get_customers_spent_max_avg_amount_money() -> List[int]:
    conn = None
    ret_val = []
    try:
        conn = Connector.DBConnector()
        query = (sql.SQL("CREATE VIEW OrderView AS"
            " SELECT order_id, SUM(amount*price_upon_order) AS bill"
            " FROM MealContains"
            " GROUP BY order_id"))
        conn.execute(query)

        query_cont = sql.SQL("SELECT Ordered.cust_id, SubTable.res "
                             "FROM (SELECT Ordered.cust_id, AVG(bill + delivery_fee + tip) AS res "
                             "FROM Ordered "
                             "INNER JOIN OrderView ON Ordered.order_id = OrderView.order_id "
                             "INNER JOIN Orders ON OrderView.order_id = Orders.order_id "
                             "GROUP BY Ordered.cust_id) AS SubTable"
                             "WHERE SubTable.res = (SELECT MAX(InnerSub.res)"
                             "FROM (SELECT AVG(bill + delivery_fee + tip) AS res"
                             "FROM Ordered"
                             "INNER JOIN OrderView ON Ordered.order_id = OrderView.order_id"
                             "INNER JOIN Orders ON OrderView.order_id = Orders.order_id"
                             "GROUP BY Ordered.cust_id) AS InnerSub)"
                             "ORDER BY Ordered.cust_id ASC")
        res = ((conn.execute(query_cont)))

        return res

    except Exception as e:
        print(e)
        return []
    finally:
        if conn:
            conn.close()



def get_most_profitable_dish_in_period(start: datetime, end: datetime) -> Dish:
    conn = None
    try:
        conn = Connector.DBConnector()
        query = (sql.SQL("""SELECT Dish.dish_id, name, price, is_active
                            FROM Dish INNER JOIN
                            (SELECT dish_id, SUM(dish_bill) AS total
                            FROM	
                            (SELECT amount, price_upon_order,dish_id, 
                            MealContains.order_id, amount*price_upon_order as dish_bill
                            FROM (MealContains INNER JOIN 
                            (SELECT order_id 
                             FROM Orders 
                             WHERE date > {_start} AND date < {_end}) AS CURR 
                             ON MealContains.order_id = CURR.order_id))
                             GROUP BY dish_id
                             ORDER BY total DESC , dish_id ASC
                             LIMIT 1) AS ChosenDish
                             ON Dish.dish_id = ChosenDish.dish_id
                             """)
                .format(_start= sql.Literal(start), _end=sql.Literal(end)))

        res = ((conn.execute(query)))
        if res[0] == 0:
            return BadDish()
        res = res[1]
        ret_val = Dish(dish_id=res['dish_id'][0], name=res['name'][0],
                       price=float(res['price'][0]), is_active=bool(res['is_active']))
        return ret_val

    except Exception as e:
        return BadDish()
    finally:
        if conn:
            conn.close()

def did_customer_order_top_rated_dishes(cust_id: int) -> bool:
    conn = None
    try:
        conn = Connector.DBConnector()
        query = (sql.SQL("""
            SELECT Dishes.dish_id
            FROM 
            (SELECT DISTINCT MealContains.dish_id
            FROM MealContains 
            INNER JOIN Ordered ON Ordered.order_id = MealContains.order_id
            WHERE Ordered.cust_id = {_cust_id}) AS Dishes
            INNER JOIN 
            (SELECT 
            DishesSub.dish_id,
            COALESCE(Average.avgRated, 3) AS final_rating
            FROM 
            (SELECT DISTINCT MealContains.dish_id
            FROM MealContains 
            INNER JOIN Ordered ON Ordered.order_id = MealContains.order_id
            WHERE Ordered.cust_id = {_cust_id}) AS DishesSub
            LEFT JOIN 
            (SELECT dish_id, AVG(rating) AS avgRated
            FROM Rated
            GROUP BY dish_id) AS Average 
            ON DishesSub.dish_id = Average.dish_id
            ORDER BY final_rating DESC, DishesSub.dish_id ASC
            LIMIT 5) AS TopFiveDishes
            ON Dishes.dish_id = TopFiveDishes.dish_id
        """)).format(_cust_id= sql.Literal(cust_id))

        res = ((conn.execute(query)))
        if res[0] == 0:
            return False
        return True
    except Exception as e:
        return False
    finally:
        if conn:
            conn.close()


# ---------------------------------- ADVANCED API: ----------------------------------

# Advanced API


def get_customers_rated_but_not_ordered() -> List[int]:
    conn = None
    try:
        conn = Connector.DBConnector()

        query = (sql.SQL("""
                SELECT DISTINCT custRatedDishBad.cust_id 
                FROM                    
                (SELECT lowestDishes.dish_id, badRatings.cust_id
                FROM
                (SELECT cust_id, dish_id FROM Rated WHERE rating < 3 ) AS badRatings 
                INNER JOIN
                (SELECT 
                Dish.dish_id,
                COALESCE(AVG(Rated.rating), 3.0) AS avg_rating
                FROM Dish 
                LEFT JOIN 
                Rated ON Dish.dish_id = Rated.dish_id
                GROUP BY Dish.dish_id
                ORDER BY avg_rating ASC, Dish.dish_id ASC    
                LIMIT 5) 
                AS lowestDishes
    
                ON badRatings.dish_id = lowestDishes.dish_id) AS custRatedDishBad
                
                WHERE NOT EXISTS (
                        SELECT * FROM customerOrderedDishes
                        WHERE customerOrderedDishes.cust_id = custRatedDishBad.cust_id 
                          AND customerOrderedDishes.dish_id = custRatedDishBad.dish_id
                    )
                ORDER BY custRatedDishBad.cust_id ASC
        """))
        res = ((conn.execute(query)))
        if res[0] == 0:
            return []
        ret_val = [] #tomorrow....
        return res[1]

    except Exception as e:
        return []
    finally:
        if conn:
            conn.close()


def get_non_worth_price_increase() -> List[int]:
    conn = None
    try:
        conn = Connector.DBConnector()
        query = (sql.SQL(""" SELECT DISTINCT avgPerPriceTable.dish_id
            FROM avgPerPriceTable
            INNER JOIN
            avgPerPriceTable AS avgPerPriceTableDup
            ON avgPerPriceTable.dish_id = avgPerPriceTableDup.dish_id
            
            WHERE avgPerPriceTableDup.price_upon_order = avgPerPriceTableDup.price 
            AND avgPerPriceTableDup.price > avgPerPriceTable.price
            AND avgPerPriceTable.avgPerPrice > avgPerPriceTableDup.avgPerPrice
            ORDER BY avgPerPriceTable.dish_id ASC;
            """))

        res = ((conn.execute(query)))
        if res[0] == 0:
            return []
        ret_val = [] #tomorrow....
        return res[1]

    except Exception as e:
        return []
    finally:
        if conn:
            conn.close()



def get_cumulative_profit_per_month(year: int) -> List[Tuple[int, float]]:
    # TODO: implement
    pass


def get_potential_dish_recommendations(cust_id: int) -> List[int]:
    # TODO: implement
    pass


if __name__ == '__main__':
    #clear_tables()
    #drop_tables()
    create_tables()

    order = Order(20,"2026-07-03 14:30:15.123456",50, "hadera", 5)
    add_order(order)
    order = Order(21,"2026-07-03 20:30:15.123456",50, "hadera", 5)
    add_order(order)
    order = Order(22,"2026-07-03 20:30:15.123456",50, "hadera", 5)
    add_order(order)

    customer = Customer(10,"itamar1", 20,"0584706025")
    add_customer(customer)
    customer = Customer(11,"itamar2", 20,"0584706025")
    add_customer(customer)
    customer = Customer(12,"itamar3", 20,"0584706025")
    add_customer(customer)

    print(customer_placed_order(10,20))
    customer_placed_order(11,21)
    customer_placed_order(12,22)
    did_customer_order_top_rated_dishes(10)

    dish = Dish(20, "itamar", 10, True)
    #add_dish(dish)
    dish = Dish(30, "itamar", 10, True)
    #add_dish(dish)
    dish = Dish(40, "itamar", 10, True)
    #add_dish(dish)

    #order_contains_dish(20,20,10)
    #order_contains_dish(21, 30, 10)
    #order_contains_dish(22, 40, 10)

    #order_contains_dish(22, 30, 3)
    #get_most_profitable_dish_in_period("2020-07-03 16:30:15.123456","2029-07-03 22:30:15.123456" )

    clear_tables()
    drop_tables()