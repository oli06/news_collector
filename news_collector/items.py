# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class NewsCollectorItem(scrapy.Item):
    url = scrapy.Field() #article url
    date = scrapy.Field() #datetime: release date of the article
    teaser = scrapy.Field() #short introduction or first few sentences of the article (shown on the main page)
    agency = scrapy.Field() #spiegel, ntv, etc
    authors = scrapy.Field() #list of authors
    is_update = scrapy.Field() #bool: is it a update on the article (used by ntv, but doesnot work currently)
    kicker = scrapy.Field() #second-headline
    headline = scrapy.Field() 
    named_references = scrapy.Field() #dict: term´s that references to another article
    article_text_blocks = scrapy.Field()
    text = scrapy.Field()
    tags = scrapy.Field() #list: ntv uses tags to describe the content of an article
    category = scrapy.Field() #politics, sports, economy, etc 