# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from pydispatch import dispatcher
from pymongo import MongoClient
from scrapy.exceptions import IgnoreRequest
import logging

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

    def __init__(self, mongo_server, mongo_port, mongo_db, mongo_collection, mongo_user, mongo_password, whitelist):
        self.mongo_server = mongo_server
        self.mongo_port = mongo_port
        self.mongo_db = mongo_db
        self.mongo_collection = mongo_collection
        self.mongo_user = mongo_user
        self.mongo_password = mongo_password

        if mongo_user is None:
            self.client = MongoClient(mongo_server, mongo_port)
        else:
            # self.urls = self.db.news.articles.find({ "agency": "n-tv" })
            self.client = MongoClient(
                f'mongodb://{mongo_user}:{mongo_password}@{mongo_server}:{mongo_port}')

        self.db = self.client[mongo_db]
        self.whitelist = whitelist
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls(crawler.settings.get('MONGODB_SERVER'),
                crawler.settings.get('MONGODB_PORT'),
                crawler.settings.get('MONGODB_DB'),
                crawler.settings.get('MONGODB_COLLECTION'),
                crawler.settings.get('MONGODB_USER', None),
                crawler.settings.get('MONGODB_PASSWORD', None),
                crawler.settings['WHITELIST'])

        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)

        return s

    def process_request(self, request, spider):
        url = request.url

        # TODO regex for file names
        if url.endswith('.pdf') or url.endswith('.png'):
            raise IgnoreRequest()

        tl_domain = '/'.join(url.split('/')[:3])
        if tl_domain in self.whitelist:
            if self.db[self.mongo_collection].find({"url": url}).count(with_limit_and_skip=True) == 1:
                logging.debug(f'skipping {url}, already in database')
                raise IgnoreRequest()
            return None  # everything is fine

        logging.debug(f'skipping {url}, not in whitelist')
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
        self.client.close()
