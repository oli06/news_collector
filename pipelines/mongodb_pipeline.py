# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


from pymongo import MongoClient
from scrapy import settings


class MongoDbPipeline(object):
    def __init__(self, mongo_server, mongo_port, mongo_db, mongo_collection, mongo_user, mongo_password, store_metadata):
        self.mongo_server = mongo_server
        self.mongo_port = mongo_port
        self.mongo_db = mongo_db
        self.mongo_collection = mongo_collection
        self.mongo_user = mongo_user
        self.mongo_password = mongo_password
        self.store_metadata = store_metadata

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_server=crawler.settings.get('MONGODB_SERVER'), 
            mongo_port=crawler.settings.get('MONGODB_PORT'), 
            mongo_db=crawler.settings.get('MONGODB_DB'), 
            mongo_collection=crawler.settings.get('MONGODB_COLLECTION'),
            mongo_user=crawler.settings.get('MONGODB_USER', None),
            mongo_password=crawler.settings.get('MONGODB_PASSWORD', None),
            store_metadata=crawler.settings.get("STORE_METADATA", False)
        )

    def open_spider(self, spider):
        #use auth or not (if no user is specified in settings.py)
        if self.mongo_user is None:
            self.client = MongoClient(self.mongo_server, self.mongo_port)
        else: 
            self.client = MongoClient(f'mongodb://{self.mongo_user}:{self.mongo_password}@{self.mongo_server}:{self.mongo_port}')
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        exists = self.db[self.mongo_collection].find({ 'url': item['url'] }).count()
        if exists:
            return item

        valid = True

        if item['headline'] == '' or item['text'] == '' or item['url'] == '' or item['date'] == '':
            valid = False

        if not valid:
            return item

        _id = self.db[self.mongo_collection].insert_one(dict(item))

        if self.store_metadata:
            metadata = {'raw': item.pop('raw'), 'url': item['url']}    
            metadata['ref_id'] = _id.inserted_id
            self.db['metadata'].insert_one(dict(metadata))

        return item
