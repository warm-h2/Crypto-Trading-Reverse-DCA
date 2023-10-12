
import time
from binance.enums import *

class ReverseDCA:
    def __init__(self, binance_client, telegram_bot, ticker, initial_direction, base_order_size, volume_scale, breakeven_threshold_pct, stop_loss_pct, increment_pct, take_profit_pct):
        self.binance_client = binance_client
        self.telegram_bot = telegram_bot
        self.ticker = ticker
        self.initial_direction = initial_direction
        self.base_order_size = base_order_size
        self.volume_scale = volume_scale
        self.breakeven_threshold_pct = breakeven_threshold_pct / 100
        self.stop_loss_pct = stop_loss_pct / 100
        self.base_increment_pct = increment_pct / 100
        self.take_profit_pct = take_profit_pct / 100
        self.first_entry_price = 0
        self.avg_entry_price = 0
        self.hit_tp = False
        self.current_volume = self.base_order_size
        self.current_increment_pct = self.base_increment_pct
    
    def get_mark_price(self):
        while True:
            try:
                # return round(float(self.binance_client.futures_symbol_ticker(symbol=self.ticker)['price']), 2)  # testnet futures price
                return round(float(self.binance_client.get_margin_price_index(symbol="BTCUSDT")['price']), 2)   # production margin price
            except:
                time.sleep(5)
                self.telegram_bot.send_message("Exception! Fetching mark price. Retrying...")
    
    def get_open_position(self):
        while True:
            try:
                open_positions = self.binance_client.futures_position_information(symbol=self.ticker)
                if len(open_positions) == 0:
                    return -1
                return open_positions[0]

            except:
                time.sleep(5)
                self.telegram_bot.send_message("Exception! Get open positions. Retrying...")
    
    def close_position(self):
        open_position = self.get_open_position()
        if open_position != -1:
            size = float(open_position['positionAmt'])
            if size > 0:
                side = "sell"
            elif size < 0:
                side = "buy"
            else:
                self.telegram_bot.send_message("Invalid position size!")
                return

            # side = open_position['positionSide']
            # if side == SIDE_BUY:
            #     side = "sell"
            # elif side == SIDE_SELL:
            #     side = "buy"
            
            self.place_market_order(size, side, self.get_mark_price())
    
    def place_market_order(self, size, direction, mark_price):
        if direction.lower() == "buy":
            direction = SIDE_BUY
        elif direction.lower() == "sell":
            direction = SIDE_SELL
        else:
            self.telegram_bot.send_message(f"Invalid direction {direction}!")
            return
        
        while True:
            try:
                # order = self.binance_client.futures_create_order(symbol=self.ticker, side=direction, type=ORDER_TYPE_MARKET, quantity=size)   # futures (testnet)
                order = self.binance_client.create_margin_order(symbol=self.ticker, side=direction, type=ORDER_TYPE_MARKET, timeInForce=TIME_IN_FORCE_GTC, quantity=size)      # margin (production)
                break
            except:
                time.sleep(5)
                self.telegram_bot.send_message("Exception! Placing market order. Retrying...")

        time.sleep(2)
        while True:
            try:
                # _order = self.binance_client.futures_get_order(symbol=self.ticker, orderId=order['orderId'])   # futures (testnet)
                _order = self.binance_client.get_margin_order(symbol=self.ticker, orderId=order['orderId'])      # margin (production)
                break
            except:
                time.sleep(5)
                self.telegram_bot.send_message("Exception! Getting order information. Retrying...")
        
        order_status = _order['status'].lower()
        fill_price = round(float(_order['avgPrice']), 2)
        if order_status == "filled":
            open_position = self.get_open_position()
            if open_position != -1:
                position_size = float(open_position['positionAmt'])
                self.avg_entry_price = float(open_position['entryPrice'])
                self.telegram_bot.send_message(f"Market {direction} order of size {round(size, 4)} {self.ticker} filled at ${fill_price}. Mark price at that time: ${mark_price}. Current {direction} position size: {position_size} {self.ticker}. Average entry price: ${self.avg_entry_price}")
        
    
    # def get_average_entry_price(self):
    #     avg_entry_price = 26000
    #     return avg_entry_price
    
    def reset(self):
        self.first_entry_price = 0
        self.avg_entry_price = 0
        self.hit_tp = False
        self.current_volume = self.base_order_size
        self.current_increment_pct = self.base_increment_pct
    
    def buy_check_tp_sl_increment(self, current_price):
        increment_price = self.first_entry_price * (1 + self.current_increment_pct)
        take_profit_price = self.first_entry_price * (1 + self.take_profit_pct)
        if not self.hit_tp:
            stop_loss_price = self.first_entry_price * (1 - self.stop_loss_pct)
        else:
            stop_loss_price = self.avg_entry_price * (1 + self.breakeven_threshold_pct)

        if current_price > take_profit_price:       # hit take profit
            self.telegram_bot.send_message(f"TAKE PROFIT HIT! Closing open position.")
            self.close_position()
            self.reset()
            return
        
        if current_price < stop_loss_price:         # hit stop loss
            self.telegram_bot.send_message(f"STOP LOSS HIT! Closing open position.")
            self.close_position()
            self.reset()
            return

        if current_price > increment_price:         # increment level exceeded
            self.telegram_bot.send_message(f"Increment price reached. Scaling volume by {self.volume_scale}x")
            scaled_volume = self.current_volume * self.volume_scale
            self.current_volume = scaled_volume + self.current_volume
            mark_price = self.get_mark_price()
            self.place_market_order(round(scaled_volume / mark_price, 3), self.initial_direction, mark_price)
            # self.avg_entry_price = self.get_average_entry_price()
            self.current_increment_pct += self.base_increment_pct
            self.hit_tp = True
    
    def sell_check_tp_sl_increment(self, current_price):
        increment_price = self.first_entry_price * (1 - self.current_increment_pct)
        take_profit_price = self.first_entry_price * (1 - self.take_profit_pct)
        if not self.hit_tp:
            stop_loss_price = self.first_entry_price * (1 + self.stop_loss_pct)
        else:
            stop_loss_price = self.avg_entry_price * (1 + self.breakeven_threshold_pct*-1)  # multiplied by -1 since the positives and negatives will opposite in case of short

        if current_price < take_profit_price:       # hit take profit
            self.telegram_bot.send_message(f"TAKE PROFIT HIT! Closing open position.")
            self.close_position()
            self.reset()
            return
        
        if current_price > stop_loss_price:         # hit stop loss
            self.telegram_bot.send_message(f"STOP LOSS HIT! Closing open position.")
            self.close_position()
            self.reset()
            return

        if current_price < increment_price:         # increment level exceeded
            self.telegram_bot.send_message(f"Increment price reached. Scaling volume by {self.volume_scale}x")
            scaled_volume = self.current_volume * self.volume_scale
            self.current_volume = scaled_volume + self.current_volume
            mark_price = self.get_mark_price()
            self.place_market_order(round(scaled_volume / mark_price, 3), self.initial_direction, mark_price)
            # self.avg_entry_price = self.get_average_entry_price()
            self.current_increment_pct += self.base_increment_pct
            self.hit_tp = True

    def run(self):
        self.telegram_bot.send_message("Running Reverse DCA...")
        while True:
            time.sleep(1.5)
            if self.avg_entry_price == 0:    # not in position
                mark_price = self.get_mark_price()
                order_size = round(self.current_volume / mark_price, 3)
                self.telegram_bot.send_message(f"First entry. Opening new position with base volume {order_size} {self.ticker}")
                self.place_market_order(order_size, self.initial_direction, mark_price)
                self.first_entry_price = self.avg_entry_price
                # self.first_entry_price = self.avg_entry_price = self.get_average_entry_price()
            
            else:    # already in position
                current_price = self.get_mark_price()
                print(current_price)
                if self.initial_direction.lower() == "buy":
                    self.buy_check_tp_sl_increment(current_price)

                elif self.initial_direction.lower() == "sell":
                    self.sell_check_tp_sl_increment(current_price)