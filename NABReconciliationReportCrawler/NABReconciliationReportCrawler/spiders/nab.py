# -*- coding: utf-8 -*-
import scrapy

import sys
import codecs
import locale
import json
import time
import re
import datetime
from scrapy.shell import inspect_response
from NABReconciliationReportCrawler.items import NabreconciliationreportcrawlerItem
from NABReconciliationReportCrawler.sheets import Sheets
from NABReconciliationReportCrawler import settings


def load_login_data(filename):

    with open(filename) as json_data:
        login_credentials_list = json.load(json_data)

    return login_credentials_list


class NabSpider(scrapy.Spider):
    name = "nab"
    allowed_domains = ["nab.com.au"]
    start_urls = (
        'https://transact.nab.com.au/nabtransact/',
    )

    def __init__(self,client_id,*args, **kwargs):
        super(NabSpider,self).__init__(*args,**kwargs)
        sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)
        reload(sys)
        sys.setdefaultencoding('utf-8')

        self.client_id = client_id.strip()

        """ Setting Sheet name by client id """
        settings.SHEETS_PARAMETERS['sheet_name'] = self.client_id

        sheet = Sheets(
            settings.SHEETS_PARAMETERS['spreadsheetId'],
            settings.SHEETS_PARAMETERS['client_secret_file'],
            settings.SHEETS_PARAMETERS['application_name'],
            settings.SHEETS_PARAMETERS['sheet_name'],
        )

        self.sheet_last_date = sheet.get_last_date()
        print("*************************************")
        print ("Sheet Last Date", self.sheet_last_date)
        print("**************************************")

        self.sheet_last_date_epoch = int((time.mktime(time.strptime(self.sheet_last_date, '%d/%m/%Y')))) - time.timezone
        self.from_date_epoch = self.sheet_last_date_epoch + 86400  # add 1 day
        self.time_today_epoch = time.time()

        # self.sheet_last_date ="9/08/2016"

        try:
            self.login_credentials_list = load_login_data('data/login_data/logins_data.json')
        except (OSError, IOError) as e:
            self.logger.error("**************************************")
            self.logger.error(e)
            self.logger.error("**************************************")

    def parse(self, response):

        try:
            login_data = [x for x in self.login_credentials_list if self.client_id in x.values()][0]

            return scrapy.FormRequest.from_response(
                response,
                formdata={'j_subaccount':login_data['client_id'].strip(),
                          'j_username': login_data['username'].strip(),
                          'j_password': login_data['password'].strip()
                          # 'j_password': "dfs"
                          },
                callback=self.after_login,

            )
        except (IndexError, AttributeError):
            print("************************************************************************")
            print(" Sorry We couldn't find the client id You have entered: %s " % self.client_id)
            print(" Please enter client Id again  in login_data.json file")
            print("****************************************************************************")
            login_data = False

        print("***********")
        print(self.client_id)
        print("***********")

    def after_login(self,response):
        # inspect_response(response, self)
        if "Login Failed" in response.body:
            self.logger.error("********************************************"
                              "**********************************************")
            self.logger.error("Login failed!! Please check user name and "
                              "password in data/login_data/login_data.json file")
            self.logger.error("**********************************************"
                              "*******************************************")
            return
        else:
            link = response.xpath("//ul[@class='level1']/li/a/@href")
            if link:
                link = link[3].extract()
            else:
                link = ""
            base_url = "https://transact.nab.com.au/nabtransact/"
            link = "{}/{}".format(base_url, link)
            yield scrapy.Request(link, self.search_reconciliation_report)

    def search_reconciliation_report(self,response):

        # inspect_response(response, self)

        merchant_id = self.client_id
        card_types = 'vm'
        currency_list = response.xpath("//select[@id='currency']/option/@value").extract()
        from_date_epoch = self.from_date_epoch
        from_date = time.strftime("%d/%m/%Y", time.gmtime(from_date_epoch))
        time_loop = True
        while time_loop:
            for currency in currency_list:
                request = scrapy.FormRequest.from_response(
                    response,
                    formdata={
                        'merchid': merchant_id,
                        'fromdate': from_date,
                        'todate': from_date,
                        'cardtypes': card_types,
                        'currency': currency,
                        'submit': 'Search',
                    },
                    callback=self.search_results,

                )
                request.meta['currency'] = currency
                request.meta['date'] = from_date
                yield request

            from_date_epoch += 86400
            if from_date_epoch > self.time_today_epoch:
                time_loop = False
                
    def search_results(self, response):

        # inspect_response(response, self)
        data_table_elem = response.xpath("//table[@id='datatable']")
        table_data_list = data_table_elem.xpath('.//td/text()').extract()
        from_date_errors = response.xpath("//span[@id='fromdate.errors']")
        to_date_errors = response.xpath("//span[@id='todate.errors']")
        if table_data_list:
            total_amounts = table_data_list[-1]
            total_amounts_group = re.search(r'([-+]?)(.*?)([\d,\.]+)', total_amounts)
            sign = total_amounts_group.group(1)
            total_amounts = re.sub(r'[,]+', "", total_amounts_group.group(3))
            total_amounts = "{}{}".format(sign, total_amounts)

            item = NabreconciliationreportcrawlerItem()
            item['total_amounts'] = total_amounts
            item['currency'] = response.meta['currency']
            item['date'] = response.meta['date']

            print("****************************")
            print (total_amounts,response.meta['currency'], response.meta['date'])
            print("****************************")
            yield item
        else:
            self.logger.error("*******************************************")
            if from_date_errors:
                self.logger.error("From Date:{} {}  For Currency {}".
                                  format(response.meta['currency'],
                                         from_date_errors.xpath("text()").extract_first(),
                                         response.meta['date']))

            if to_date_errors:
                self.logger.error("To Date: {} {} for Currency {} ".
                                  format(response.meta['date'],
                                         from_date_errors.xpath("text()").extract_first(),
                                         response.meta['currency']))
            self.logger.error("*******************************************")




