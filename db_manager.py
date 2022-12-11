from pymongo import MongoClient

class DBManager():
    def __init__(self, host, port, username, password, dbName) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.dbName = dbName

        if username and password:
            mongo_uri = 'mongodb://%s:%s@%s:%s/%s' % (username, password, host, port, dbName)
            conn = MongoClient(mongo_uri)
        else:
            conn = MongoClient(host, port)

        self.db = conn[dbName]

    def connect_mongodb(self, host, port, username, password, dbName):
        """ A util for making a connection to mongo """

        if username and password:
            mongo_uri = 'mongodb://%s:%s@%s:%s/%s' % (username, password, host, port, dbName)
            conn = MongoClient(mongo_uri)
        else:
            conn = MongoClient(host, port)

        return conn[dbName]

    def delete_one(self, collection, query={}):
        db = self.db 
        """ self.connect_mongodb("localhost", 27018, "", "", "trady") """
        #query = {"Name": { "$regex": 'USDT$' }}
        mycol  = db[collection]
        x = mycol.delete_one(query)
        
        return x

    def delete_many(self, collection, query={}):
        db = self.db  
        # self.connect_mongodb("localhost", 27018, "", "", "trady")
        #query = {"Name": { "$regex": 'USDT$' }}
        mycol  = db[collection]
        x = mycol.delete_many(query)
    
        return x

    def insert_one(self, collection, record):
        db = self.db 
        #  self.connect_mongodb("localhost", 27018, "", "", "trady")
        #record = {"PAIR": "TRX_USDT", "PRICE": "0.05202", "AMOUNT": "9199"}
        mycol  = db[collection]
        x = mycol.insert_one(record)

        return x

    def insert_many(self, collection, records):
        db = self.db 
        # self.connect_mongodb("localhost", 27018, "", "", "trady")
        mycol  = db[collection]
        x = mycol.insert_many(records)

        return x
    
    def update_one(self, collection, filter={}, newvalues={}):
        """ Read from Mongo and Store into DataFrame """
        "Default: localhost, port: 27018"
        # Make a query to the specific DB and Collection
        collection = self.db[collection]

        collection.update_one(filter, newvalues)
        
        # Printing the updated content of the
        # database
        cursor = collection.find_one(filter)

        return cursor

    def read_one(self, collection, query={}):
        """ Read from Mongo and Store into DataFrame """
        "Default: localhost, port: 27018"
        # Make a query to the specific DB and Collection
        cursor = self.db[collection].find_one(query)

        return cursor

    def read_collection(self, collection, query={}):
        """ Read from Mongo and Store into DataFrame """
        "Default: localhost, port: 27018"
        # Make a query to the specific DB and Collection
        cursor = self.db[collection].find(query)

        # Expand the cursor and construct the DataFrame
        df =  list(cursor)

        return df