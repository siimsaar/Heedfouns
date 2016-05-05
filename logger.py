import logging
import os

LOG_NAME = "log.log"

# initialize logging
logging.basicConfig(filename=LOG_NAME,
                    level=logging.INFO,
                    format='[%(levelname)s] - %(asctime)s - %(message)s',
                    datefmt='%d/%m/%Y, %H:%M:%S')
logging.info('Sucessfully started the logging module')

def get_log_entries(limit):
    log_file = open(LOG_NAME, 'r').readlines()[-limit:]
    return log_file