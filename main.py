import sys
import logging
from time import sleep
from config.settings import VERSION, SPREADSHEET
from src.scraper import Scraper

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    logger.info(f'Starting scraper version {VERSION}')

    scraper = Scraper(SPREADSHEET)

    while True:
        try:
            scraper.run()
        except Exception as err:
            logger.error(str(err))
            sleep(60 * 60)
            continue
        
        # wait 24 hours before run again
        sleep(60*60*24)
