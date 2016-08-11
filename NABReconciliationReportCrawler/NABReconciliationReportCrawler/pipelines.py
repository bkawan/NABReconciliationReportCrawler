# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from NABReconciliationReportCrawler import settings
from NABReconciliationReportCrawler.sheets import Sheets

import time


class NabreconciliationreportcrawlerPipeline(object):

    def __init__(self):
        self.sheet = Sheets(
        settings.SHEETS_PARAMETERS['spreadsheetId'],
        settings.SHEETS_PARAMETERS['client_secret_file'],
        settings.SHEETS_PARAMETERS['application_name'],
        settings.SHEETS_PARAMETERS['sheet_name'],
        )

    def close_spider(self, spider):
        self.sheet.sort_sheet()

    def process_item(self, item, spider):

        AUD = None
        EUR = None
        USD = None
        CAD = None
        CHF = None
        GBP = None
        HKD = None
        JPY = None
        NZD = None
        SGD = None

        if item['currency'] == 'AUD':
            AUD = item['total_amounts']

        if item['currency'] == 'EUR':
            EUR = item['total_amounts']
        if item['currency'] == 'USD':
            USD = item['total_amounts']
        if item['currency'] == 'CAD':
            CAD = item['total_amounts']
        if item['currency'] == 'CHF':
            CHF = item['total_amounts']
        if item['currency'] == 'GBP':
            GBP = item['total_amounts']
        if item['currency'] == 'HKD':
            HKD = item['total_amounts']
        if item['currency'] == 'JPY':
            JPY = item['total_amounts']
        if item['currency'] == 'NZD':
            NZD = item['total_amounts']
        if item['currency'] == 'SGD':
            SGD = item['total_amounts']

        self.sheet.append_row([
            item['date'],
            AUD,
            EUR,
            USD,
            CAD,
            CHF,
            GBP,
            HKD,
            JPY,
            NZD,
            SGD,

        ])

