from telegram import Bot
import requests

class TelegramBot:
    def __init__(self, api_token, chat_id):
        self.api_token = api_token
        self.chat_id = chat_id

    def send_message(self, message, print_terminal=True):
        apiURL = f'https://api.telegram.org/bot{self.api_token}/sendMessage'

        try:
            if print_terminal:
                print(message)
            response = requests.post(apiURL, json={'chat_id': self.chat_id, 'text': message})
            # print(response.text)
        except Exception as e:
            print("Exception! Telegram Bot.", e)