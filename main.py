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

    # initializing and running the strategy
    obj_reverse_dca = ReverseDCA(binance_client, telegram_bot, ticker, initial_direction, base_order_size, volume_scale, breakeven_threshold_pct, stop_loss_pct, increment_pct, take_profit_pct)
    obj_reverse_dca.run()


if __name__ == '__main__':
    main()