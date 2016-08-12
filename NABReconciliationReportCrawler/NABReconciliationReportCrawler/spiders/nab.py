# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request, FormRequest

from scrapy.shell import  inspect_response
from scrapy.utils.response import open_in_browser
import sys
import codecs
import locale
import json
import re
from datetime import  date
import datetime
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

    def __init__(self, client_id, *args, **kwargs):
        super(NabSpider, self).__init__(*args, **kwargs)
        sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)
        reload(sys)
        sys.setdefaultencoding('utf-8')

        self.client_id = client_id.strip()

        self.cli = 1
        self.currency_list = ['AUD', 'EUR', 'USD', 'CAD', 'CHF', 'GBP', 'HKD', 'JPY', 'NZD', 'SGD',False]
        # self.currency_list = ['USD',False]
        self.currency = 'AUD'

        """ Setting Sheet name by client id """
        settings.SHEETS_PARAMETERS['sheet_name'] = self.client_id
        #
        sheet = Sheets(
            settings.SHEETS_PARAMETERS['spreadsheetId'],
            settings.SHEETS_PARAMETERS['client_secret_file'],
            settings.SHEETS_PARAMETERS['application_name'],
            settings.SHEETS_PARAMETERS['sheet_name'],
        )

        self.sheet_last_date = sheet.get_last_date()
        self.from_date = (datetime.datetime.strptime(self.sheet_last_date,"%d/%m/%Y") + datetime.timedelta(days=1))
        self.from_date = self.from_date.strftime("%d/%m/%Y")
        self.to_date = date.today().strftime("%d/%m/%Y")
        self.to_date = "12/08/2016"
        # self.from_date = "01/07/2016"
        # self.to_date = "01/08/2016"

        print("*************************************")
        print ("Sheet From Date", self.from_date)
        print("**************************************")
        print ("Sheet To Date", self.to_date)


        try:
            self.login_credentials_list = load_login_data('data/login_data/login_data.json')
        except (OSError, IOError) as e:
            self.logger.error("**************************************")
            self.logger.error(e)
            self.logger.error("**************************************")

    def parse(self, response):

        try:
            login_data = [x for x in self.login_credentials_list if self.client_id in x.values()][0]

            return scrapy.FormRequest.from_response(
                response,
                formdata={'j_subaccount': login_data['client_id'].strip(),
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

    def after_login(self, response):
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

    def search_reconciliation_report(self, response):
        # inspect_response(response, self)


        while self.currency:

            yield scrapy.FormRequest.from_response(
                response,
                formdata={
                    'merchid': self.client_id,
                    'fromdate': self.from_date,
                    'todate': self.to_date,
                    'cardtypes': 'vm',
                    'currency': self.currency,

                }
                ,
                callback=self.search_results,
                method="POST",
                # dont_filter=True,
                meta={'currency': self.currency}

            )


    def search_results(self, response):
        # inspect_response(response,self)


        data_table_elem = response.xpath("//table[@id='datatable']")

        if data_table_elem:

            self.currency = self.currency_list[self.cli]
            self.cli += 1
            # inspect_response(response,self)


            for data in data_table_elem.xpath(".//tr"):
                # date = data.xpath(".//td/a/@href").extract()
                date = data.xpath("normalize-space(.//td/a/@href)").extract_first()
                if date:
                    date = re.search(r'[\d\/]+', date).group()
                    total_amounts = data.xpath(".//td/text()").extract()[-1]
                    print(date,total_amounts)
                    item = NabreconciliationreportcrawlerItem()
                    item['total_amounts'] = total_amounts
                    item['currency'] = response.meta['currency']
                    item['date'] = date

                    yield item

