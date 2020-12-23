from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from news_collector.spiders.ntv_spider import NtvSpider

process = CrawlerProcess(get_project_settings())
process.crawl(NtvSpider)
process.start()
