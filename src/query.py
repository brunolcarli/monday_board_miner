import requests
from config.settings import MONDAY_URL, MONDAY_TOKEN, BOARD_ID


headers = {
    'Authorization': MONDAY_TOKEN
}


def initial_query():
    query = f'''
        query {{
            boards(limit: 1 ids: ["{BOARD_ID}"]) {{
                name
                
                items_page(limit: 500) {{
                    cursor
                    items{{
                        name
                        id
                        column_values {{
                        text
                        }}
                    }}
                }}
            }}
        }}
    '''
    r = requests.post(MONDAY_URL, json={'query': query}, headers=headers)
    return r.json()


def get_next_page(cursor):
    query = f'''
    query {{
      boards(limit: 1 ids: ["{BOARD_ID}"]) {{
        name

      	items_page(limit: 500 cursor: "{cursor}") {{
          cursor
          items{{
            name
            id
            column_values {{
              text
            }}
          }}
        }}
      }}
    }}
    '''
    r = requests.post(MONDAY_URL, json={'query': query}, headers=headers)
    return r.json()
