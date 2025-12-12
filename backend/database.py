import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME')


class MongoDBClient:
    def __init__(self, uri, db_name, collection_name):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def find_unpredicted_texts_docs(self):
        return self.collection.find({
            "$or": [
                {"predictedAt": {"$exists": False}},
                {"pt_the_poli": {"$exists": False}}
            ]
        })

    def find_unweighted_text_docs(self):
        return self.collection.find({
            "pt_the_waiter": {"$exists": False},
            "pt_the_poli.final_the_poli": "political"
        })

    def get_all_docs(self):
        return self.collection.find({})

    def update_doc(self, doc_id, update_fields):
        self.collection.update_one({"_id": doc_id}, {"$set": update_fields})


def get_db_client(collection_name):
    return MongoDBClient(uri=MONGO_URI, db_name=DB_NAME, collection_name=collection_name)


def close_db(client):
    if client:
        client.client.close()
        print("Database connection closed.")
