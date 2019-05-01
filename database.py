
from bson.objectid import ObjectId
import pymongo
from pymongo import MongoClient
import csv
import configparser
import redis


config = configparser.ConfigParser()
config.read('config.ini')
connection_string = config['database']['mongo_connection']

customers= None
products = None
orders = None

#Establishing a connection to redis 
r = redis.StrictRedis(host = 'redis-19521.c74.us-east-1-4.ec2.cloud.redislabs.com',port = 19521, password = 'OfGWjWTsbBM2QgEEu0fLN5UDpO9xaPFj', db=0, decode_responses=True)
r.set('x',14)
v = r.get('x')
print(v)

# The following functions are REQUIRED - you should REPLACE their implementation
# with the appropriate code to interact with your Mongo database.
def initialize():
    # this function will get called once, when the application starts.
    # this would be a good place to initalize your connection!
    # You might also want to connect to redis...
    global customers
    global products
    global orders
    client = MongoClient(connection_string)
    customers = client.cmps364.customers
    products = client.cmps364.products
    orders = client.cmps364.orders

    print('Nothing to do here...')


def get_customers():
    customerList = customers.find({})
    turnList =list() 
    for row in customerList:
        turnList.append(row)
    return turnList 

def get_customer(id): 
    returnValue =customers.find_one({'_id':ObjectId(id)})
    return returnValue

def upsert_customer(customer):
    
    if '_id' in customer:
        customers.update_one({'_id':ObjectId(customer.get('_id'))},{'$set':{'firstName':customer.get('firstName'),'lastName':customer.get('lastName'),'street':customer.get('street'),'city':customer.get('city'),'state':customer.get('state'),'zip':customer.get('zip')}})
    else:
        customers.insert_one(customer)

def delete_customer(id):
    customers.delete_one({'_id':ObjectId(id)})

    #check if the product is in Order Collection or not and if it is, delete that row of data in order collection 
    orders.remove({'customerId':id})
    
    
def get_products():
    productsList = products.find({})
    turnList = list()
    for row in productsList:
        turnList.append(row)
    return turnList

def get_product(id):
    returnValue = products.find_one({'_id':ObjectId(id)})
    return returnValue

def upsert_product(product):
    if '_id' in product:
        products.update_one({'_id':ObjectId(product.get('_id'))}, {'$set':{'name':product.get('name'), 'price':product.get('price')}})
        r.delete(product.get('_id'))
    else:
        products.insert_one(product)

def delete_product(id):
    products.delete_one({'_id':ObjectId(id)})

    #Check if the product is in Order Collection or not and if it is. Delete that row of data in order collection
    orders.remove({'productId':id})

def get_orders():
    ordersList = orders.find({})
    turnList = list()
    for row in ordersList:
        turnList.append(row)

    for order in turnList:
        order['product']=get_product(order['productId'])
        order['customer']=get_customer(order['customerId'])

    return turnList

def get_order(id):
    returnValue = orders.find_one({'_id':ObjectId(id)})
    return returnValue

def upsert_order(order):
    orders.insert_one(order)
    if order['productId'] in r.keys():
        r.delete(order['productId'])


def delete_order(id):
    getOrderReturn = get_order(id)
    orders.delete_one({'_id':ObjectId(id)})
    r.delete(getOrderReturn['productId'])

def customer_report(id):
    return None

# Pay close attention to what is being returned here.  Each product in the products
# list is a dictionary, that has all product attributes + last_order_date, total_sales, and 
# gross_revenue.  This is the function that needs to be use Redis as a cache.

# - When a product dictionary is computed, save it as a hash in Redis with the product's
#   ID as the key.  When preparing a product dictionary, before doing the computation, 
#   check if its already in redis!
def sales_report():
    productList = get_products()
    redisList = list()
    for row in productList:
        checkList = list()
        hashName = str(row['_id'])
        value = r.exists(hashName)

        #CALCULATING DATE VALUES TO ADD IT TO THE DICTIONARY 
        dateType = orders.find({'productId':str(row['_id'])})
        for insideType in dateType:
            checkList.append(insideType['date'])#checklist contains list of dates of the given product id

        if len(checkList) != 0:
            last_order_date = (max(checkList))
        else:
            last_order_date=0

        if value == 0:
            row['total_sales']=orders.find({'productId':str(row['_id'])}).count()
            row['gross_revenue']=orders.find({'productId':str(row['_id'])}).count() * row['price']
            row['last_order_date']=last_order_date
            r.hmset(hashName,{'name':row['name'],'price': row['price'],'total_sales': row['total_sales'],'gross_revenue': row['gross_revenue'],'last_order_date': row['last_order_date']}) 
            
        redisList.append(r.hgetall(hashName))
    
    return redisList




