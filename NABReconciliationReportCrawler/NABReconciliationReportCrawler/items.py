# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class NabreconciliationreportcrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # report = scrapy.Field()
    currency = scrapy.Field()
    date = scrapy.Field()
    total_amounts = scrapy.Field()


    # report = scrapy.Field()
