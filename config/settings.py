import os

VERSION = '0.0.1'
GOOGLE_CREDENTIALS = os.environ.get('GOOGLE_CREDENTIALS', '/path/to/google_credentials.json')
MONDAY_TOKEN = os.environ.get('MONDAY_TOKEN', 'monday_api_token')
SPREADSHEET = os.environ.get('SPREADSHEET', 'spreadsheet_name')
MONDAY_URL = 'https://api.monday.com/v2'
BOARD_ID = os.environ.get('BOARD_ID')