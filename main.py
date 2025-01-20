import asyncio
# from telegram import Bot
import time
from datetime import datetime
import configparser
import os
from reverse_dca import ReverseDCA
from telegram_utils import TelegramBot
from binance.client import Client
from binance.enums import *
import requests

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import threading

import sys
import asyncio

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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
            if (currency['symbol'] != 'USDT') and (currency['symbol'] != 'FDUSD') and (currency['symbol'] != 'vBNB') and (currency['symbol'] != 'LUNA') and (currency['symbol'] != 'WETH') and (currency['symbol'] != 'PEPE') and (currency['symbol'] != 'WBTC'):
                pair_name = currency['symbol'] + 'USDT'
                volume = currency['quote']['USD']['volume_24h']
                top_pairs.append((pair_name, volume))

        top_pairs.sort(key=lambda x: x[1], reverse=True)
        return top_pairs[:limit]
    
    else:
        print(f"Error: {response.status_code} - {response.text}")        
        return []

def main():
    
    # Parsing settigns config file
    config = configparser.ConfigParser(inline_comment_prefixes=";")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, 'settings.ini')
    config.read(config_path)

    ticker = config['settings']['ticker']
    max_position = config['settings']['Max_positions']
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
    
    telegram_api_token = config['telegram']['api_token']
    telegram_channel_chat_id_1 = config['telegram']['channel_chat_id_1']
    telegram_channel_chat_id_2 = config['telegram']['channel_chat_id_2']
    telegram_bot = TelegramBot(telegram_api_token, telegram_channel_chat_id_1, telegram_channel_chat_id_2)    

    binance_api_key = config['binance']['api_key']
    binance_api_secret = config['binance']['api_secret']
    # binance_client = Client(binance_api_key, binance_api_secret)

    # binance_api_key = config['binance']['test_api_key']
    # binance_api_secret = config['binance']['test_api_secret']
    print(f"api => {binance_api_key}  secret=> {binance_api_secret}")
    # telegram_bot.send_message("--------------------------------------------------------\nRunning Reverse DCA Stategy...")
    # self.telegram_bot.send_message(self.setting_message)
    if(ticker == "auto"):
        pairs = []
        nowcount  = 0
        past_time = datetime.now()
        delta_criteria= 3600
        while True:
            delta = datetime.now()-past_time
            print(f'nowcount => {nowcount}  delta=> {delta.total_seconds()}' )
            if nowcount == 0 or delta.total_seconds()>delta_criteria:
                nowcount = 0     
                past_time = datetime.now()
                coinmarket_api_key = '5e8e7147-6955-433e-892c-e765d5f9ee81'
                top_volume_pairs = get_top_volume_pairs(coinmarket_api_key)
                # print(f'top_volume => ', top_volume_pairs)
                # break
                # Close the position of all current working bots.
                while len(pairs)>0:
                    cur_bot = pairs.pop()
                    cur_bot.reset()
                    cur_bot.close_position()
                print(f'initial pairs => {pairs}')
                pairCount = 0
                # top_volume_pairs = [("TRBUSDT",10929),("ZETAUSDT",29192),("MANTAUSDT",238838)]
                for pair in top_volume_pairs:
                    ticker = pair[0]
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
                    
                    binance_client = Client(binance_api_key, binance_api_secret)
                    obj_reverse_dca = ReverseDCA(binance_client, telegram_bot, ticker, 
                                        initial_direction, base_order_size, 
                                        volume_scale, breakeven_threshold_pct, 
                                        stop_loss_pct, increment_pct, take_profit_pct, 
                                        setting_message, sma_period, sma_tf, hma1_period, 
                                        hma2_period, hma3_period, hma1_tf, hma2_tf, hma3_tf)
                    # continue
                    try:
                        isOk = obj_reverse_dca.isAvailable()
                        print(f"-----------------------------------\n{ticker} => IsAvailable => {isOk}")
                        if isOk == False: 
                            print(f"count => {pairCount}")
                            continue
                    except Exception as e:
                        print(f'Exception => {e}')
                        continue
                    try :
                        pairCount = pairCount + 1
                        pairs.append(obj_reverse_dca)
                        print(f"count => {pairCount}")
                        if pairCount >= int(max_position) : break
                    except KeyboardInterrupt:  
                        telegram_bot.logger.warning("Keyboard interrupt detected, stopping the bot.")
                        print("\nProgram interrupted by user.")
                print(f'after pairs => {pairs}')
            for ticker in pairs:
                if nowcount % 3600 == 0:
                    telegram_bot.send_message(ticker.setting_message)
                ticker.run()
            nowcount = nowcount + 1

            time.sleep(1)
    else : 
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
        binance_client = Client(binance_api_key, binance_api_secret)

        # print(f'-----------------binance_client------------------------\n{binance_client}\n-----------------------------------')
        # return
        # initializing and running the strategy
        obj_reverse_dca = ReverseDCA(binance_client, telegram_bot, ticker, 
                                    initial_direction, base_order_size, 
                                    volume_scale, breakeven_threshold_pct, 
                                    stop_loss_pct, increment_pct, take_profit_pct, 
                                    setting_message, sma_period, sma_tf, hma1_period, 
                                    hma2_period, hma3_period, hma1_tf, hma2_tf, hma3_tf)
        # obj_reverse_dca.close_position()
        # obj_reverse_dca.cancel_all_open_orders()
        while True:
            try:
                telegram_bot.send_message(obj_reverse_dca.setting_message)
                obj_reverse_dca.run()
            except KeyboardInterrupt:
                telegram_bot.logger.warning("Keyboard interrupt detected, stopping the bot.")
                print("\nProgram interrupted by user.")
            time.sleep(1)


# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text('Bot is starting...')
#     thread = threading.Thread(target=main)
#     thread.start()




# async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text('Bot is stopping...')
    


if __name__ == '__main__':
    main()
    # config = configparser.ConfigParser(inline_comment_prefixes=(";",))
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # config_path = os.path.join(current_dir, 'settings.ini')
    # config.read(config_path)

    # telegram_api_token = config['telegram']['api_token']

    # application = Application.builder().token(telegram_api_token).build()
    # application.add_handler(CommandHandler("start", start))
    # # application.add_handler(CommandHandler("stop", stop))
    # application.run_polling()
