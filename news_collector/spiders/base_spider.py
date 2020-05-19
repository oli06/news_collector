import scrapy
import logging
import datetime
from scrapy import signals
from pydispatch import dispatcher
import math
import news_collector.top_level_formatter as tlf


class BaseSpider(scrapy.Spider):
    total_parsed = 0
    urls_parsed = []

    def __init__(self, name, max, tld, ignore_dirs):
        dispatcher.connect(self.spider_closed, signals.spider_closed)
        self.name = name
        self.max = max or math.inf
        self.tld = tld
        self.ignore_dirs = ignore_dirs or []
        log_init(self)

    def spider_closed(self, spider):
        logging.info(f'total parsed: {self.total_parsed}')

    def isAccessible(self, response, url):
        if self.total_parsed >= self.max:
            logging.debug(f'max ({self.max}) reached')
            return False

        if not url.startswith(self.tld):
            # currently no support for other newspages
            logging.debug(f'not parsing, other newspage {url}')
            return False

        for dir in self.ignore_dirs:
            if dir in url:
                logging.debug(f'not parsing, ignore directory {url}')
                return False

        if url in self.urls_parsed:
            logging.debug(f"{url} already parsed")
            return False
        else:
            self.urls_parsed.append(url)

        return True




def log_init(spider):
    date = datetime.datetime.now()
    now = date.strftime('%Y-%m-%d-%H-%M-%S')
    log_name = "./logs/spiders/{0}_{1}.log".format(spider.name, now)

    handler = logging.FileHandler(log_name)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('[{0}] - [%(asctime)s] - [%(levelname)s]\t|  %(message)s'.format(spider.name))
    handler.setFormatter(formatter)
    handler.addFilter(tlf.MyTopLevelFormatter(loggers=[__name__], name=spider.name))

    # Add the spider handler with filtering
    if handler not in spider.logger.logger.parent.handlers:
        spider.logger.logger.parent.addHandler(handler)
