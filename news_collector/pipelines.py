# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


from pymongo import MongoClient


class NewsCollectorPipeline(object):
    def __init__(self, mongo_server, mongo_port, mongo_db, mongo_collection):
        self.mongo_server = mongo_server
        self.mongo_port = mongo_port
        self.mongo_db = mongo_db
        self.mongo_collection = mongo_collection

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_server=crawler.settings.get('MONGODB_SERVER'), 
            mongo_port=crawler.settings.get('MONGODB_PORT'), 
            mongo_db=crawler.settings.get('MONGODB_DB'), 
            mongo_collection=crawler.settings.get('MONGODB_COLLECTION')
        )

    def open_spider(self, spider):
        self.client = MongoClient(self.mongo_server, self.mongo_port)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        exists = self.db[self.mongo_collection].find({ 'url': item['url'] }).count()
        if exists:
            return item
            
        valid = True

        if valid:
            self.db[self.mongo_collection].insert_one(dict(item))

        return item
