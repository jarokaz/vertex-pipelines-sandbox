import os
import logging
import time
import signal
import sys


def send_cancel_request(message):
    logging.info(message)


from launcher import execution_context
def main():

    logging.info("Going to sleep")
    sleep_time = 30

    with execution_context.ExecutionContext(
        on_cancel=lambda: send_cancel_request('Cancelling')):
    
        for i in range(10):
            time.sleep(30)
            logging.info("Waking up for a little bit")
    logging.info('Done sleeping')

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(message)s',
                      level=logging.INFO, 
                      datefmt='%d-%m-%y %H:%M:%S',
                      stream=sys.stdout)
    main()
