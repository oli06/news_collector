# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from pydispatch import dispatcher
from pymongo import MongoClient
from scrapy.exceptions import IgnoreRequest

class NewsCollectorSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)




class NewsCollectorDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    def __init__(self):
        if self.mongo_user is None:
            client = MongoClient(self.mongo_server, self.mongo_port)
        else: 
            client = MongoClient(f'mongodb://{self.mongo_user}:{self.mongo_password}@{self.mongo_server}:{self.mongo_port}')        #self.urls = self.db.news.articles.find({ "agency": "n-tv" })
        
        self.db = client[self.mongo_db]
        dispatcher.connect(self.spider_closed, signals.spider_closed)


    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        cls.whitelist = crawler.settings['WHITELIST']

        cls.mongo_server=crawler.settings.get('MONGODB_SERVER')
        cls.mongo_port=crawler.settings.get('MONGODB_PORT')
        cls.mongo_db=crawler.settings.get('MONGODB_DB')
        cls.mongo_collection=crawler.settings.get('MONGODB_COLLECTION')
        cls.mongo_user=crawler.settings.get('MONGODB_USER', None)
        cls.mongo_password=crawler.settings.get('MONGODB_PASSWORD', None)

        return s

    def process_request(self, request, spider):
        url = request.url

        #TODO regex for file names
        if url.endswith('.pdf') or url.endswith('.png'):
            raise IgnoreRequest()

        tl_domain = '/'.join(url.split('/')[:3])
        if tl_domain in self.whitelist:
            if self.db[self.mongo_collection].find({"url": url}).count(with_limit_and_skip=True) == 1:
                raise IgnoreRequest()
            return None #everything is fine
     
        raise IgnoreRequest()
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


    def spider_closed(self, spider):
        self.db.close()