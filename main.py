import asyncio
# from telegram import Bot
import time
import configparser
import os
from reverse_dca import ReverseDCA
from telegram_utils import TelegramBot
from binance.client import Client
from binance.enums import *
import requests
import multiprocessing


top_strategy_volume_pairs = []


def get_top_volume_pairs(api_key, limit=800):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    parameters = {
        'start': '1',
        'limit': str(limit),
        'convert': 'USD',
        'sort': 'volume_24h'
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
    }

    response = requests.get(url, headers=headers, params=parameters)

    if response.status_code == 200:
        data = response.json()
        top_pairs = []

        for currency in data['data']:
            if (currency['symbol'] != 'USDT') and (currency['symbol'] != 'FDUSD') and (currency['symbol'] != 'vBNB') and (currency['symbol'] != 'WETH') and (currency['symbol'] != 'PEPE') and (currency['symbol'] != 'WBTC'):
                pair_name = currency['symbol'] + 'USDT'
                volume = currency['quote']['USD']['volume_24h']
                top_pairs.append((pair_name, volume))

        top_pairs.sort(key=lambda x: x[1], reverse=True)
        return top_pairs[:limit]
    
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []

def get_my_pairs():
    coinmarket_api_key = '5e8e7147-6955-433e-892c-e765d5f9ee81'
    top_volume_pairs = get_top_volume_pairs(coinmarket_api_key)
    print(top_volume_pairs)
    config = configparser.ConfigParser(inline_comment_prefixes=";")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, 'settings.ini')
    config.read(config_path)

    ticker = config['settings']['ticker']
    max_position = config['settings']['Max-positions']
    initial_direction = config['settings']['initial_direction']
    base_order_size = int(config['settings']['base_order_size'])
    volume_scale = float(config['settings']['volume_scale'])
    breakeven_threshold_pct = float(config['settings']['breakeven_threshold_pct'])
    stop_loss_pct = float(config['settings']['stop_loss_pct'])
    increment_pct = float(config['settings']['increment_pct'])
    take_profit_pct = float(config['settings']['take_profit_pct'])
    sma_period = int(config['settings']['sma_period'])
    hma1_period = int(config['settings']['hma1_period'])
    hma2_period = int(config['settings']['hma2_period'])
    hma3_period = int(config['settings']['hma3_period'])
    sma_tf = config['settings']['sma_timeframe']
    hma1_tf = config['settings']['hma1_timeframe']   
    hma2_tf = config['settings']['hma2_timeframe']  
    hma3_tf = config['settings']['hma3_timeframe']  
    
    setting_message  =  (
                            f"Ticker = {ticker}\n"
                            f"Initial Direction = {initial_direction}\n"
                            f"Base Order Size = {base_order_size}\n"
                            f"Volume Scale = {volume_scale}\n"
                            f"Breakeven Percent = {breakeven_threshold_pct}\n"
                            f"Stop Loss Percent = {stop_loss_pct}\n"
                            f"Increment Percent = {increment_pct}\n"
                            f"Take Profit Percent = {take_profit_pct}\n"
                            f"SMA = {sma_period}, {sma_tf}\n"
                            f"HMA 1 = {hma1_period}, {hma1_tf}\n"
                            f"HMA 2 = {hma2_period}, {hma2_tf}\n"
                            f"HMA 3 = {hma3_period}, {hma3_tf}"                            
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
                                 setting_message, sma_period, sma_tf, hma1_period, 
                                 hma2_period, hma3_period, hma1_tf, hma2_tf, hma3_tf)
    if int(max_position) < 1:
        obj_reverse_dca.telegram_bot.send_message("Max-positions must be equal or bigger than 1.")
        return
    else:
        pairs_num = 0
        i = 0
        top_strategy_volume_pairs.clear()
        while (i <= 790):
            ticker = top_volume_pairs[i][0]
            setting_message  =  (
                            f"Ticker = {ticker}\n"
                            f"Initial Direction = {initial_direction}\n"
                            f"Base Order Size = {base_order_size}\n"
                            f"Volume Scale = {volume_scale}\n"
                            f"Breakeven Percent = {breakeven_threshold_pct}\n"
                            f"Stop Loss Percent = {stop_loss_pct}\n"
                            f"Increment Percent = {increment_pct}\n"
                            f"Take Profit Percent = {take_profit_pct}\n"
                            f"SMA = {sma_period}, {sma_tf}\n"
                            f"HMA 1 = {hma1_period}, {hma1_tf}\n"
                            f"HMA 2 = {hma2_period}, {hma2_tf}\n"
                            f"HMA 3 = {hma3_period}, {hma3_tf}"                            
                        )
            obj_reverse_dca = ReverseDCA(binance_client, telegram_bot, ticker, 
                                initial_direction, base_order_size, 
                                volume_scale, breakeven_threshold_pct, 
                                stop_loss_pct, increment_pct, take_profit_pct, 
                                setting_message, sma_period, sma_tf, hma1_period, 
                                hma2_period, hma3_period, hma1_tf, hma2_tf, hma3_tf)
            # obj_reverse_dca_next = ReverseDCA(binance_client, telegram_bot, top_volume_pairs[i+1][0], 
            #                     initial_direction, base_order_size, 
            #                     volume_scale, breakeven_threshold_pct, 
            #                     stop_loss_pct, increment_pct, take_profit_pct, 
            #                     setting_message, sma_period, sma_tf, hma1_period, 
            #                     hma2_period, hma3_period, hma1_tf, hma2_tf, hma3_tf)
            print(obj_reverse_dca.get_order_check())
            print(ticker)
            if obj_reverse_dca.get_order_check()==True:
                top_strategy_volume_pairs.append(ticker)
                pairs_num = pairs_num + 1
            if pairs_num > int(max_position) - 1 or i == 790:
                return
        
            i = i + 1
            print(pairs_num)
    
    


def main():

    # Parsing settigns config file
    config = configparser.ConfigParser(inline_comment_prefixes=";")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, 'settings.ini')
    config.read(config_path)

    ticker = config['settings']['ticker']
    max_position = config['settings']['Max-positions']
    initial_direction = config['settings']['initial_direction']
    base_order_size = int(config['settings']['base_order_size'])
    volume_scale = float(config['settings']['volume_scale'])
    breakeven_threshold_pct = float(config['settings']['breakeven_threshold_pct'])
    stop_loss_pct = float(config['settings']['stop_loss_pct'])
    increment_pct = float(config['settings']['increment_pct'])
    take_profit_pct = float(config['settings']['take_profit_pct'])
    sma_period = int(config['settings']['sma_period'])
    hma1_period = int(config['settings']['hma1_period'])
    hma2_period = int(config['settings']['hma2_period'])
    hma3_period = int(config['settings']['hma3_period'])
    sma_tf = config['settings']['sma_timeframe']
    hma1_tf = config['settings']['hma1_timeframe']   
    hma2_tf = config['settings']['hma2_timeframe']  
    hma3_tf = config['settings']['hma3_timeframe']  
    
    setting_message  =  (
                            f"Ticker = {ticker}\n"
                            f"Initial Direction = {initial_direction}\n"
                            f"Base Order Size = {base_order_size}\n"
                            f"Volume Scale = {volume_scale}\n"
                            f"Breakeven Percent = {breakeven_threshold_pct}\n"
                            f"Stop Loss Percent = {stop_loss_pct}\n"
                            f"Increment Percent = {increment_pct}\n"
                            f"Take Profit Percent = {take_profit_pct}\n"
                            f"SMA = {sma_period}, {sma_tf}\n"
                            f"HMA 1 = {hma1_period}, {hma1_tf}\n"
                            f"HMA 2 = {hma2_period}, {hma2_tf}\n"
                            f"HMA 3 = {hma3_period}, {hma3_tf}"                            
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
                                 setting_message, sma_period, sma_tf, hma1_period, 
                                 hma2_period, hma3_period, hma1_tf, hma2_tf, hma3_tf)
    # obj_reverse_dca.close_position()
    # obj_reverse_dca.cancel_all_open_orders()
    # try:
    #     obj_reverse_dca.run()
    # except KeyboardInterrupt:
    #     telegram_bot.logger.warning("Keyboard interrupt detected, stopping the bot.")
    # #     print("\nProgram interrupted by user.")
    
    if ticker == "auto":

        while True:
            # time.sleep(1)
            obj_reverse_dca.telegram_bot.send_message(f"---------------Start!------------------\n" f"Checking coins for Reverse DCA Strategy...")
            get_my_pairs()
            obj_reverse_dca.telegram_bot.send_message(f"Checking coins finished.")
            processes = []
            print(top_strategy_volume_pairs)
            if len(top_strategy_volume_pairs) == 0:
                obj_reverse_dca.telegram_bot.send_message("no suitable coins found")
            else:
                obj_reverse_dca.telegram_bot.send_message("suitable coins found")
                for ticker in top_strategy_volume_pairs:

                    setting_message  =  (
                                        f"Ticker = {ticker}\n"
                                        f"Initial Direction = {initial_direction}\n"
                                        f"Base Order Size = {base_order_size}\n"
                                        f"Volume Scale = {volume_scale}\n"
                                        f"Breakeven Percent = {breakeven_threshold_pct}\n"
                                        f"Stop Loss Percent = {stop_loss_pct}\n"
                                        f"Increment Percent = {increment_pct}\n"
                                        f"Take Profit Percent = {take_profit_pct}\n"
                                        f"SMA = {sma_period}, {sma_tf}\n"
                                        f"HMA 1 = {hma1_period}, {hma1_tf}\n"
                                        f"HMA 2 = {hma2_period}, {hma2_tf}\n"
                                        f"HMA 3 = {hma3_period}, {hma3_tf}"                            
                                    )
                    obj_reverse_dca = ReverseDCA(binance_client, telegram_bot, ticker, 
                                        initial_direction, base_order_size, 
                                        volume_scale, breakeven_threshold_pct, 
                                        stop_loss_pct, increment_pct, take_profit_pct, 
                                        setting_message, sma_period, sma_tf, hma1_period, 
                                        hma2_period, hma3_period, hma1_tf, hma2_tf, hma3_tf)
                    obj_reverse_dca.telegram_bot.send_message(setting_message)
                    process = multiprocessing.Process(target=obj_reverse_dca.run(), args=(ticker, ))
                    processes.append(process)
                    process.start()
                    # obj_reverse_dca.run()
                for process in processes:
                    process.join()

    else:        
        obj_reverse_dca.telegram_bot.send_message(f"---------------Start!------------------\n" f"Applying RDCA for {ticker} strategy...")
        try:
            obj_reverse_dca.run_single()
        except KeyboardInterrupt:
            telegram_bot.logger.warning("Keyboard interrupt detected, stopping the bot.")
            print("\nProgram interrupted by user.")



if __name__ == '__main__':
    main()