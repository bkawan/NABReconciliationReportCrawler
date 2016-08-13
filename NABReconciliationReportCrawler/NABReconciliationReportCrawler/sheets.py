#!/usr/bin/env python2

from __future__ import print_function
import httplib2
import os
import csv

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools


class Sheets:

    def __init__(self, spreadsheetId, client_secret_file, application_name, sheet_name):
        self.flags = None

        self.SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
        self.CLIENT_SECRET_FILE = client_secret_file
        self.APPLICATION_NAME = application_name

        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = 'https://sheets.googleapis.com/$discovery/rest?version=v4'
        self.service = discovery.build('sheets', 'v4', http=http,
                                  discoveryServiceUrl=discoveryUrl)

        self.spreadsheetId = spreadsheetId

        result = self.service.spreadsheets().get(spreadsheetId=self.spreadsheetId).execute()

        sheet = [ (sheet['properties']['sheetId'], sheet['properties']['title']) for sheet in result['sheets'] if sheet['properties']['title'] == sheet_name ]

        if not sheet:
            raise ValueError('No such sheet in this spreadsheet')

        self.sheet_name = sheet_name
        self.sheet_id = sheet[0][0]
        self.last_row = self.get_row(last=True)

    def get_credentials(self):
        """Gets valid user credentials from storage.
        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.
        Returns:
            Credentials, the obtained credential.
        """

        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'sheets.googleapis.com-python-quickstart.json')

        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
        return credentials

    def get_last_date(self, row_no = False):
        date_range_name = self.sheet_name + '!'
        date_range_name += 'A1:A'

        result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheetId, range=date_range_name,
                majorDimension='COLUMNS').execute()

        values = result.get('values', [])
        last_date = values[0][-1]
     
        if row_no:
            return len(values[0])
        else:
            return last_date

    """ To get date row index if exists"""
    
    def get_date_row_index(self, check_date):
        date_range_name = self.sheet_name + '!'
        date_range_name += 'A1:A'

        result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheetId, range=date_range_name,
                majorDimension='COLUMNS').execute()

        values = result.get('values', [])
        last_date = values[0]
        date_row_index = False
        if check_date in last_date:
            date_row_index = last_date.index(check_date) + 1

        return date_row_index
    
    def get_row(self, row_no = None, last = False):

        if not row_no and not last:
            raise ValueError('Invalid usage')

        if last:
            row_no = self.get_last_date(row_no = True)  ## give row number

        date_range_name = self.sheet_name + '!'
        date_range_name += 'A{0}:K{0}'.format(row_no)

        result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheetId, range=date_range_name,
                majorDimension='ROWS').execute()

        values = result.get('values',[])

        row = values[0]## give row value of row number
       
        return row

    def append_row(self, row):

        if not type(row) is list:
            raise Exception('row is not a list')

        date_row_index = self.get_date_row_index(row[0])
        if date_row_index:
            row_count = date_row_index
        else:
            row_count = self.get_last_date(row_no=True) + 1 # give last row  +1 to instert into
            
        new_row = row[0:11]  # A-K
     
        date_range_name = self.sheet_name + '!'
        date_range_name += 'A{0}'.format(row_count)

        currency_range_name = self.sheet_name + '!'

        if row[1] == 'AUD':
            currency_range_name += 'B{0}'.format(row_count)

        if row[1] == 'EUR':
            currency_range_name += 'C{0}'.format(row_count)

        if row[1] == 'USD':
            currency_range_name += 'D{0}'.format(row_count)
        if row[1] == 'CAD':
            currency_range_name += 'E{0}'.format(row_count)

        if row[1] == 'CHF':
            currency_range_name += 'F{0}'.format(row_count)

        if row[1] == 'GBP':
            currency_range_name += 'G{0}'.format(row_count)

        if row[1] == 'HKD':
            currency_range_name += 'H{0}'.format(row_count)

        if row[1] == 'JPY':
            currency_range_name += 'I{0}'.format(row_count)

        if row[1] == 'NZD':
            currency_range_name += 'J{0}'.format(row_count)
        if row[1] == 'SGD':
            currency_range_name += 'K{0}'.format(row_count)

        if new_row:

            date_body = {
                'range': date_range_name,
                'values': [[row[0]]],
                'majorDimension': 'COLUMNS'
            }
            date_result = self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheetId, range=date_range_name,
                    valueInputOption='USER_ENTERED', body=date_body).execute()

            currency_body = {
                    'range' : currency_range_name,
                    'values' : [[row[2]]],
                    'majorDimension': 'COLUMNS'
                }

            currency_result = self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheetId, range=currency_range_name,
                        valueInputOption='USER_ENTERED', body=currency_body).execute()

            return currency_result, date_result

    def sort_sheet(self):
        sort_column_index = 0 # sort using 1st column
        body = {
            'requests': [
                {
                    'sortRange': {
                        'range': {
                            'sheetId': self.sheet_id,
                            'startRowIndex': 1,
                            'startColumnIndex': 0
                        },
                        'sortSpecs': [
                            {
                                'dimensionIndex': sort_column_index,
                                'sortOrder': 'ASCENDING'
                            }
                        ]
                    },
                }


            ]
        }

        result = self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheetId, body=body).execute()
        return result



if __name__=='__main__':
    #     1iNeNK-ATYFpu1wvS_JLZKjzcVVDqYbmcW6Dn8c705Xs

    sheet = Sheets(spreadsheetId='1iNeNK-ATYFpu1wvS_JLZKjzcVVDqYbmcW6Dn8c705Xs',
                   client_secret_file='client_secret.json',
                   application_name='FinancialData',
                   sheet_name='V46')

