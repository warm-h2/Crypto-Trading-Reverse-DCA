# from telegram import Bot
import requests
import os
import datetime

class TelegramBot:
    def __init__(self, api_token, chat_id_1, chat_id_2):
        self.api_token = api_token
        self.chat_id_1 = chat_id_1
        self.chat_id_2 = chat_id_2
        self.logs_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        self.file_name = "logs_" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
        if not os.path.exists(self.logs_dir_path):
            os.makedirs(self.logs_dir_path)

    def send_message(self, message, print_terminal=True, log_file=True):
        api_url = f'https://api.telegram.org/bot{self.api_token}/sendMessage'

        try:
            if print_terminal:
                print(message)
            if log_file:
                with open(os.path.join(self.logs_dir_path, self.file_name), "a") as file:
                    file.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " | "  + message + "\n")
            response_1 = requests.post(api_url, json={'chat_id': self.chat_id_1, 'text': message})
            response_2 = requests.post(api_url, json={'chat_id': self.chat_id_2, 'text': message})
            # # print(response.text)
        except Exception as e:
            print("Exception! Telegram Bot.", e)