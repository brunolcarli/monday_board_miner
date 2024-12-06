# Bultin modules
import sys
from datetime import datetime, timedelta
import logging
from time import time

# third party modules
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# proprietary modules
from config.settings import GOOGLE_CREDENTIALS
from src.query import initial_query, get_next_page

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)


class Scraper:
    def __init__(self, spreadsheet_name):
        self.spreadsheet = spreadsheet_name
        self.board = None
        self.cursor = None
        self.last_run = datetime.now() - timedelta(days=1)
        self.dataframe = None
        self.columns = [
            'Name',
            'Subitems',
            'Tutor messaged',
            'Tutor confirmed',
            'Confirmed tutor',
            'Confirmation sent',
            'FS FU 1',
            'FS FU 2',
            'FS FU 3',
            'Tutor in contact with family',
            'No response from family',
            'First session date',
            'First session occurred',
            'Next action date',
            'Next action',
            'item_id'
        ]
        self.blacklist = ('Name', 'Apex responded to application', 'Subitems')

    def get_first_page(self):
        """
        Try to request the first page from target monday board.
        """
        try:
            board = initial_query()['data']['boards'][0]
        except Exception as error:
            logger.error('Failed requesting monday board')
            raise Exception(f'[{str(datetime.now())}] {str(error)}')
        self.board = board

    def set_cursor(self, cursor):
        """
        Sets the cursor that points to the next page of the board
        """
        self.cursor = cursor

    def reset(self):
        self.dataframe = None
        self.get_first_page()
        self.set_cursor(self.board['items_page']['cursor'])
        logger.info('Scraper restored')
        logger.info(f'Monday board: {self.board["name"]}')
        logger.info(f'Cursor: {self.cursor}')
        logger.info(f'Last run: {str(self.last_run)}')

    def update_sheet(self):
        logger.info(f'[{str(datetime.now())}] Connecting to Google API')
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive'
        ]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS, scope)
        client = gspread.authorize(credentials)
        spreadsheet = client.open(self.spreadsheet)

        self.dataframe.to_csv('datasheet.csv', index=False)
        with open('datasheet.csv', 'r') as file_obj:
            content = file_obj.read()
            client.import_csv(spreadsheet.id, data=content)

        logging.info(f'[{str(datetime.now())}] Spreadsheet updated')

    def run(self):
        run_start = time()
        logger.info(f'[{str(datetime.now())}] Starting data mining!')

        # Run only if a period of 24 hours have passed since last run
        time_passed = (datetime.now() - self.last_run).total_seconds() / 60 / 60
        if time_passed < 24:
            logger.info('Skipping run until complete 24 hours since last run')
            raise Exception('SKIP')
        
        self.reset()

        rows = []
        last_name = None
        while self.cursor is not None:
            logger.info(f'Current cursor: {self.cursor}')
            for item in self.board['items_page']['items']:
                name, _id, col_vals = item.values()
                if name in self.blacklist:
                    continue
                elif name == 'Unnamed':
                    v = [j['text'] for j in col_vals[:len(self.columns)-2]]
                    rows.append([last_name]+v+[_id])
                else:
                    last_name = name

            logger.info('requesting next page...')
            data = get_next_page(self.cursor)
            self.board = data['data']['boards'][0]
            logger.info('Current board updated')

            self.set_cursor(self.board['items_page']['cursor'])
            logger.info(f'[{str(datetime.now())}] Collected {len(rows)} rows of data until now')

        # since the last page returns a null cursor the last page wont execute inside the loop
        # so we process the last page outside the loop, otherwise tha last page data is lost
        for item in self.board['items_page']['items']:
            name, _id, col_vals = item.values()
            if name in self.blacklist:
                continue
            elif name == 'Unnamed':
                v = [j['text'] for j in col_vals[:len(self.columns)-2]]
                rows.append([last_name]+v+[_id])
            else:
                last_name = name

        logger.info(f'[{str(datetime.now())}] Total rows: {len(rows)}')
        logger.info('Building dataframe')

        self.dataframe = pd.DataFrame(rows, columns=self.columns).replace('v', 'TRUE').replace('', 'FALSE').fillna('FALSE').drop_duplicates(subset=['Name'])
        self.update_sheet()
        self.last_run = datetime.now()
        runtime = time() - run_start
        logger.info(f'[{str(datetime.now())}] Process finished in {runtime} seconds')

