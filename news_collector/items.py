# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class NewsCollectorItem(scrapy.Item):
    pass
    category = scrapy.Field()
    url = scrapy.Field()
    teaser = scrapy.Field()
    date = scrapy.Field()
    author = scrapy.Field()
    is_update = scrapy.Field()
    kicker = scrapy.Field()
    headline = scrapy.Field()
    named_references = scrapy.Field()
    text_segments = scrapy.Field()
    tags = scrapy.Field()
    
