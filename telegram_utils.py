# from telegram import Bot
import requests
import os
import datetime
import logging
import sys


class TelegramBot:
    def __init__(self, api_token, chat_id_1, chat_id_2):
        self.api_token = api_token
        self.chat_id_1 = chat_id_1
        self.chat_id_2 = chat_id_2
        self.logs_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        self.file_name = "logs_" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
        if not os.path.exists(self.logs_dir_path):
            os.makedirs(self.logs_dir_path)

        # Set up logging configuration
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s || %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(self.logs_dir_path, self.file_name)),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        # Set the unhandled exception hook
        sys.excepthook = self.handle_exception

    def send_message(self, message, print_terminal=True):
        api_url = f'https://api.telegram.org/bot{self.api_token}/sendMessage'

        try:
            if print_terminal:
                self.logger.info(message)

            response_1 = requests.post(api_url, json={'chat_id': self.chat_id_1, 'text': message})
            response_2 = requests.post(api_url, json={'chat_id': self.chat_id_2, 'text': message})
            # # print(response.text)
            # print(response_1.status_code)
            # print(response_2.status_code)
        except Exception as e:
            self.logger.error("Exception! Telegram Bot.", e)

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            self.logger.warning("Keyboard interrupt detected, stopping the application.")
            sys.exit(1)
        else:
            self.logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
            sys.exit(1)