import asyncio
from telegram import Bot
import time
import configparser
import os
from telegram_utils import TelegramBot
from reverse_dca import ReverseDCA
from binance import Client
from binance.enums import *


def main():
    # Parsing settigns config file
    config = configparser.ConfigParser(inline_comment_prefixes=";")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, 'settings.ini')
    config.read(config_path)

    ticker = config['settings']['ticker']
    initial_direction = config['settings']['initial_direction']
    base_order_size = int(config['settings']['base_order_size'])
    volume_scale = float(config['settings']['volume_scale'])
    breakeven_threshold_pct = float(config['settings']['breakeven_threshold_pct'])
    stop_loss_pct = float(config['settings']['stop_loss_pct'])
    increment_pct = float(config['settings']['increment_pct'])
    take_profit_pct = float(config['settings']['take_profit_pct'])

    telegram_api_token = config['telegram']['api_token']
    telegram_channel_chat_id = config['telegram']['channel_chat_id']
    telegram_bot = TelegramBot(telegram_api_token, telegram_channel_chat_id)

    binance_api_key = config['binance']['test_api_key']
    binance_api_secret = config['binance']['test_api_secret']

    binance_client = Client(binance_api_key, binance_api_secret, testnet=True)
    # print(binance_client.futures_account_balance())
    order = binance_client.futures_create_order(symbol='BTCUSDT', side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=0.01)
    time.sleep(2)
    order_status = binance_client.futures_get_order(symbol='BTCUSDT', orderId=order['orderId'])['status'].lower()
    
    fill_price = binance_client.futures_position_information(symbol='BTCUSDT')[0]['entryPrice']
    position_size = binance_client.futures_position_information(symbol='BTCUSDT')[0]

    if order_status == "filled":
        print("Order filled, fill price = " + str(fill_price) + ", size = " + str(position_size))

    # initializing and running the strategy
    obj_reverse_dca = ReverseDCA(binance_client, telegram_bot, ticker, initial_direction, base_order_size, volume_scale, breakeven_threshold_pct, stop_loss_pct, increment_pct, take_profit_pct)
    obj_reverse_dca.run()


if __name__ == '__main__':
    main()

# import os
# import configparser
# import telegram
# from telegram.ext import Updater, MessageHandler
# from reverse_dca import ReverseDCA
# import requests
# import asyncio
# import time
# from telegram_utils import TelegramBot

# import telegram

# api_token = '6581004381:AAFi9oyhuLees1Jvm2kxtEcbP3PJYI0RDgI'
# channel_chat_id = '-1001817728781'

# obj_telegram = TelegramBot(api_token, channel_chat_id)

# if __name__ == '__main__':
#     asyncio.run(obj_telegram.send_message("TESTTT1"))
#     time.sleep(2)
#     asyncio.run(obj_telegram.send_message("TESTTT2"))
#     time.sleep(2)
#     asyncio.run(obj_telegram.send_message("TESTTT3"))
#     time.sleep(2)
#     asyncio.run(obj_telegram.send_message("TESTTT4"))
#     time.sleep(20)

# # async def send_message(message):
# #     channel_id = '-1001817728781'  # Replace with your channel's username
# #     bot = telegram.Bot(token='6581004381:AAFi9oyhuLees1Jvm2kxtEcbP3PJYI0RDgI')
# #     await bot.send_message(chat_id=channel_id, text=message)
# # if __name__ == '__main__':
# #     send = send_message("HELLLLLO")
# #     asyncio.run(send)

# #     time.sleep(10)
    

# # async def send_telegram_message():
# #     telegram_api_token = "6581004381:AAFi9oyhuLees1Jvm2kxtEcbP3PJYI0RDgI"
# #     bot = telegram.Bot(token=telegram_api_token)
# #     chat_id = '1987057001'
# #     bot.send_message(chat_id=chat_id, text="Hello, this is your bot!")

# # def main():
# #     send_telegram_message()
# #     time.sleep(10)
# #     # telegram_api_token = "6581004381:AAFi9oyhuLees1Jvm2kxtEcbP3PJYI0RDgI"
# #     # updater = Updater(token=telegram_api_token, use_context=True)
# #     # dispatcher = updater.dispatcher
# #     # dispatcher.add_handler(MessageHandler(telegram.ext.Filters.text & ~telegram.ext.Filters.command, send_telegram_message))

# #     # updater.start_polling()
# #     # updater.idle()
    
# #     # # Parsing settigns config file
# #     # config = configparser.ConfigParser(inline_comment_prefixes=";")
# #     # current_dir = os.path.dirname(os.path.abspath(__file__))
# #     # config_path = os.path.join(current_dir, 'settings.ini')
# #     # config.read(config_path)

# #     # ticker = config['settings']['ticker']
# #     # initial_direction = config['settings']['initial_direction']
# #     # base_order_size = int(config['settings']['base_order_size'])
# #     # volume_scale = float(config['settings']['volume_scale'])
# #     # breakeven_threshold_pct = float(config['settings']['breakeven_threshold_pct'])
# #     # stop_loss_pct = float(config['settings']['stop_loss_pct'])
# #     # increment_pct = float(config['settings']['increment_pct'])
# #     # take_profit_pct = float(config['settings']['take_profit_pct'])

# #     # # initializing and running the strategy
# #     # obj_reverse_dca = ReverseDCA(ticker, initial_direction, base_order_size, volume_scale, breakeven_threshold_pct, stop_loss_pct, increment_pct, take_profit_pct)
# #     # obj_reverse_dca.run()

# # if __name__ == "__main__":
# #     main()