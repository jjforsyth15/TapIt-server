from pymongo import MongoClient
import os

client = MongoClient(os.environ.get('MONGO_ORDERS'))
db = client["TapIt"]
orders = db["ORDERS"]

class Order:
    def __init__(self, orderNum, name, phoneNumber, email, url, numCards, paymentMethod):
        
        if orders.find_one({"orderNumber": orderNum}):
            print("Order already exists")
        else:
            orders.insert_one({
                "orderNumber": orderNum,
                "name": name,
                "phoneNumber": phoneNumber,
                "email": email,
                "url": url,
                "numCards": numCards,
                "paymentMethod": paymentMethod,
                "status": "Placed"
            })

        self.orderNum = orderNum
        self.name = name
        self.phoneNumber = phoneNumber
        self.email = email
        self.url = url
        self.numCards = numCards
        self.paymentMethod = paymentMethod


    @classmethod
    def load_order(cls, orderNum):
        order_doc = orders.find_one({"orderNumber": orderNum})

        if not order_doc:
            return None
        
        order = cls.__new__(cls)

        order.orderNum = order_doc["orderNum"]
        order.name = order_doc["name"]
        order.phoneNumber = order_doc["phoneNumber"]
        order.email = order_doc["email"]
        order.url = order_doc["url"]
        order.numCards = order_doc["numCards"]
        order.paymentMethod = order_doc["paymentMethod"]

        return order