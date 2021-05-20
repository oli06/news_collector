# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


from pymongo import MongoClient
from scrapy import settings


class MongoDbPipeline(object):
    def __init__(self, mongo_server, mongo_port, mongo_db, mongo_collection, authors_collection, mongo_user, mongo_password, store_metadata, store_authors):
        self.mongo_server = mongo_server
        self.mongo_port = mongo_port
        self.mongo_db = mongo_db
        self.mongo_collection = mongo_collection
        self.authors_collection = authors_collection
        self.mongo_user = mongo_user
        self.mongo_password = mongo_password
        self.store_metadata = store_metadata
        self.store_authors = store_authors

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_server=crawler.settings.get('MONGODB_SERVER'), 
            mongo_port=crawler.settings.get('MONGODB_PORT'), 
            mongo_db=crawler.settings.get('MONGODB_DB'), 
            mongo_collection=crawler.settings.get('MONGODB_COLLECTION'),
            authors_collection = crawler.settings.get('MONGODB_AUTHORS_COLLECTION', ""),
            mongo_user=crawler.settings.get('MONGODB_USER', None),
            mongo_password=crawler.settings.get('MONGODB_PASSWORD', None),
            store_metadata=crawler.settings.get("STORE_METADATA", False),
            STORE_AUTHORS=crawler.settings.get("STORE_AUTHORS", False)

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

        if not item['headline'] or not item['text'] or not item['url'] or not item['date']:
            return item

        if self.store_authors:
            #replace author names with sufficient _id field from authors collection
            author_ids = []
            for a in item['authors']:
                a_exists = self.db[self.authors_collection].find_one({'author': a, 'agency': item['agency']})
                if not exists:
                    #create new author
                    author_ids.append(self.db[self.authors_collection].insert_one({'author': a, 'agency': item['agency']}))
                else:
                    a_exists.get('_id')

            item['authors'] = author_ids

        #insert article
        _id = self.db[self.mongo_collection].insert_one(dict(item))

        #insert metadata if required
        if self.store_metadata:
            metadata = {'raw': item.pop('raw'), 'url': item['url']}    
            metadata['ref_id'] = _id.inserted_id
            self.db['metadata'].insert_one(dict(metadata))

        return item
