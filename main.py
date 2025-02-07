import certifi
import time
import configparser
import os
from reverse_dca import ReverseDCA
from telegram_utils import TelegramBot
from binance.client import Client
from binance.enums import *
import requests
import multiprocessing

from hma import HMAFilter


top_strategy_volume_pairs = []


def get_top_volume_pairs(api_key, limit = 100):
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

    response = requests.get(url, headers=headers, params=parameters,  verify=certifi.where())

    if response.status_code == 200:
        data = response.json()
        top_pairs = []

        for currency in data['data']:
            if (currency['symbol'] != 'USDT') and (currency['symbol'] != 'FDUSD') and (currency['symbol'] != 'vBNB') and (currency['symbol'] != 'WETH') and (currency['symbol'] != 'PEPE') and (currency['symbol'] != 'WBTC'):
                # pair_name = currency['symbol'] + 'USDT'
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
    for top_volume_pair in top_volume_pairs:
        print("************* top_volume_pair ------->", top_volume_pair)

    print("--------------------------------------------------")    
    print("--------------- Finish Getting Pair --------------")
    print("--------------------------------------------------")
    config = configparser.ConfigParser(inline_comment_prefixes=";")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, 'settings.ini')
    config.read(config_path)

    ticker = config['settings']['ticker']
    initial_direction = config['settings']['initial_direction']
    base_order_size = float(config['settings']['base_order_size'])
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

    binance_api_key = config['binance']['api_key']
    binance_api_secret = config['binance']['api_secret']
    binance_client = Client(binance_api_key, binance_api_secret)

    # initializing and running the strategy
    obj_reverse_dca = ReverseDCA(binance_client, telegram_bot, ticker, 
                                 initial_direction, base_order_size, 
                                 volume_scale, breakeven_threshold_pct, 
                                 stop_loss_pct, increment_pct, take_profit_pct, 
                                 setting_message, sma_period, sma_tf, hma1_period, 
                                 hma2_period, hma3_period, hma1_tf, hma2_tf, hma3_tf)
    pairs_num = 0
    i = 0
    top_strategy_volume_pairs.clear()

    for ticker_pair in top_volume_pairs:
        
        ticker = ticker_pair[0]
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
            hma2_period, hma3_period, hma1_tf, hma2_tf, hma3_tf
        )
        
        # obj_reverse_dca.telegram_bot.send_message(f"✅ {setting_message}")
        if obj_reverse_dca.get_order_check()==True:
            top_strategy_volume_pairs.append(ticker)
            pairs_num = pairs_num + 1
            telegram_bot.send_message(f"✅ get_order_check: {obj_reverse_dca.get_order_check()} ------ ticker:{ticker} ------ pairs_num:{pairs_num}")

        else :
            telegram_bot.send_message(f"*** get_order_check: {obj_reverse_dca.get_order_check()} ------ ticker:{ticker} ------ pairs_num:{pairs_num}")

        i = i + 1
        # telegram_bot.send_message(f"{setting_message}")
        # print(f"🔴 get_order_check: {obj_reverse_dca.get_order_check()} ------ ticker:{ticker} ------ pairs_num:{pairs_num}")
        

def main():

    # Parsing setigns config file
    config = configparser.ConfigParser(inline_comment_prefixes=";")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, 'settings.ini')
    config.read(config_path)

    ticker = config['settings']['ticker']
    initial_direction = config['settings']['initial_direction']
    base_order_size = float(config['settings']['base_order_size'])
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
    max_positions = int(config['settings']['max_positions'])

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

    binance_api_key = config['binance']['api_key']
    binance_api_secret = config['binance']['api_secret']
    binance_client = Client(binance_api_key, binance_api_secret)

    obj_reverse_dca = ReverseDCA(binance_client, telegram_bot, ticker, 
        initial_direction, base_order_size, 
        volume_scale, breakeven_threshold_pct, 
        stop_loss_pct, increment_pct, take_profit_pct, 
        setting_message, sma_period, sma_tf, hma1_period, 
        hma2_period, hma3_period, hma1_tf, hma2_tf, hma3_tf
    )

    print("\nProgram interrupted by user.")
    current_positions = 0
    while True:  
        
        # obj_reverse_dca.telegram_bot.send_message(f"🥇🥇🥇 ------------ Current_positions : {current_positions}")
        
        # time.sleep(1)
        obj_reverse_dca.telegram_bot.send_message(f"---------------Start!------------------\n" f"Checking coins for Reverse DCA Strategy...")
        get_my_pairs()
        obj_reverse_dca.telegram_bot.send_message(f"Checking coins finished.")
        processes = []
        # top_strategy_volume_pairs = ['SCRUSDT', 'STPTUSDT']
        # top_strategy_volume_pairs = [ 'JTOUSDT', 'STPTUSDT', 'LUNAUSDT','ACHUSDT', 'SCRUSDT']
        print("----------Top_strategy_volume_pairs", top_strategy_volume_pairs)
        if len(top_strategy_volume_pairs) == 0:
            obj_reverse_dca.telegram_bot.send_message("-------- No suitable coins found -----------")
        else:
            obj_reverse_dca.telegram_bot.send_message("-------- Suitable coins found -----------")
        print("------------ Suitable coins found ------------------------")
        
        for ticker in top_strategy_volume_pairs:
            print(f"🥇🥇🥇 ------------ Current_positions : {current_positions}")
            setting_message  =  (
                f"🟢 \n"
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
                hma2_period, hma3_period, hma1_tf, hma2_tf, hma3_tf
            )
            obj_reverse_dca.telegram_bot.send_message(setting_message)

            symbol_info = binance_client.get_symbol_info(ticker)
            if symbol_info:
                print(f"🍀🍀🍀 Symbol Info: {symbol_info['symbol']},{symbol_info['status']},{symbol_info['baseAsset']},{symbol_info['quoteAsset']}")
            
            print(f"🚩 Multiprocessing Process {ticker}")
            process = multiprocessing.Process(target=obj_reverse_dca.run(), args=(ticker, ))
            processes.append(process)
            process.start() 

            num_positions = obj_reverse_dca.get_num_positions()

            if (current_positions >= max_positions):
                continue
            elif num_positions == 1:
                current_positions += 1
                print(f"------------------------ 🎉 New_position Added!!!!!")
            elif num_positions == -1:
                print(f"------------------------ 🎉 One Position Closed!!!!!")
                current_positions -= 1
            elif num_positions == 0:
                print("------------------------- 🎉 No num_positions")
            
        for process in processes:
            process.join() 
        

    
    

if __name__ == '__main__':
    main()