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

    def process_item(self,item,spider):

        if item['date']:
            time.sleep(1)
            self.sheet.append_row([
                item['date'],
                item['currency'],
                item['total_amounts']
            ])

