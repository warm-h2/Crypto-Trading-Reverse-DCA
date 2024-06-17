import asyncio
# from telegram import Bot
import time
import configparser
import os
from reverse_dca import ReverseDCA
from telegram_utils import TelegramBot
from binance.client import Client
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
    sma_period = int(config['settings']['sma_period'])
    hma_period = int(config['settings']['hma_period'])
    sma_tf = config['settings']['sma_timeframe']
    hma_tf = config['settings']['hma_timeframe']   
    
    setting_message  =  (
                            f"Ticker = {ticker}\n"
                            f"Initial Direction = {initial_direction}\n"
                            f"Base Order Size = {base_order_size}\n"
                            f"Volume Scale = {volume_scale}\n"
                            f"Breakeven Percent = {breakeven_threshold_pct}\n"
                            f"Stop Loss Percent = {stop_loss_pct}\n"
                            f"Increment Percent = {increment_pct}\n"
                            f"Take Profit Percent = {take_profit_pct}\n"
                            f"SMA Filter Period = {sma_period}\n"
                            f"HMA Filter Period = {hma_period}\n"
                            f"SMA Filter TimeFrame = {sma_tf}\n"
                            f"HMA Filter TimeFrame = {hma_tf}"                            
                        )
    
    telegram_api_token = config['telegram']['api_token']
    telegram_channel_chat_id_1 = config['telegram']['channel_chat_id_1']
    telegram_channel_chat_id_2 = config['telegram']['channel_chat_id_2']
    telegram_bot = TelegramBot(telegram_api_token, telegram_channel_chat_id_1, telegram_channel_chat_id_2)    

    # binance_api_key = config['binance']['test_api_key']
    # binance_api_secret = config['binance']['test_api_secret']
    # binance_client = Client(binance_api_key, binance_api_secret, testnet=True)

    binance_api_key = config['binance']['api_key']
    binance_api_secret = config['binance']['api_secret']
    binance_client = Client(binance_api_key, binance_api_secret)

    # info = binance_client.get_account_api_permissions()

    # initializing and running the strategy
    obj_reverse_dca = ReverseDCA(binance_client, telegram_bot, ticker, 
                                 initial_direction, base_order_size, 
                                 volume_scale, breakeven_threshold_pct, 
                                 stop_loss_pct, increment_pct, take_profit_pct, 
                                 setting_message, sma_period, hma_period, sma_tf, hma_tf)
    # obj_reverse_dca.close_position()
    # obj_reverse_dca.cancel_all_open_orders()
    obj_reverse_dca.run()


if __name__ == '__main__':
    main()