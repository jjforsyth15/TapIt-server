from pymongo import MongoClient
import os

client = MongoClient(os.environ.get('MONGO_ORDERS'))
db = client["TapIt"]
orders = db["ORDERS"]

class Order:
    def __init__(self, orderNum, name, phoneNumber, email, url, numCards, paymentMethod, total, deliveryMethod="campus", note=None, street=None, city=None, state=None, zipCode=None):
        
        if orders.find_one({"orderNumber": orderNum}):
            print("Order already exists")
        else:
            orders.insert_one({
                "orderNumber": orderNum,
                "total": total,
                "name": name,
                "phoneNumber": phoneNumber,
                "email": email,
                "url": url,
                "numCards": numCards,
                "paymentMethod": paymentMethod,
                "deliveryMethod": deliveryMethod,
                "note": note,
                "street": street,
                "city": city,
                "state": state,
                "zipCode": zipCode,
                "status": "Placed"
            })

        self.orderNum = orderNum
        self.total = total
        self.name = name
        self.phoneNumber = phoneNumber
        self.email = email
        self.url = url
        self.numCards = numCards
        self.paymentMethod = paymentMethod
        self.deliveryMethod = deliveryMethod
        self.note = note
        self.street = street
        self.city = city
        self.state = state
        self.zipCode = zipCode


    @classmethod
    def load_order(cls, orderNum):
        order_doc = orders.find_one({"orderNumber": orderNum})

        if not order_doc:
            return None
        
        order = cls.__new__(cls)

        order.orderNum = order_doc["orderNum"]
        order.total = order_doc["total"]
        order.name = order_doc["name"]
        order.phoneNumber = order_doc["phoneNumber"]
        order.email = order_doc["email"]
        order.url = order_doc["url"]
        order.numCards = order_doc["numCards"]
        order.paymentMethod = order_doc["paymentMethod"]
        order.deliveryMethod = order_doc["deliveryMethod"]
        order.note = order_doc["note"]
        order.street = order_doc["street"]
        order.city = order_doc["city"]
        order.state = order_doc["state"]
        order.zipCode = order_doc["zipCode"]

        return order