
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
        self.entry_price = 0
        self.avg_entry_price = 0
        self.hit_tp = False
        self.current_volume = self.base_order_size
        self.current_increment_pct = self.base_increment_pct
    
    def get_mark_price(self):
        return round(float(self.binance_client.get_margin_price_index(symbol=self.ticker)['price']), 2)
    
    def close_position(self):
        open_position = self.binance_client.futures_position_information(symbol='BTCUSDT')[0]
        size = float(open_position['positionAmt'])
        side = open_position['positionSide']

        if side == SIDE_BUY:
            side = "sell"
        elif side == SIDE_SELL:
            side = "buy"
        
        self.place_market_order(size, side)
    
    def place_market_order(self, size, direction):
        # order = self.binance_client.create_test_order(symbol=self.ticker, side=SIDE_BUY, type=ORDER_TYPE_MARKET, timeInForce=TIME_IN_FORCE_GTC, quantity=100)
        # print(binance_client.futures_account_balance())
        order = self.binance_client.futures_create_order(symbol='BTCUSDT', side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=size)
        order_id = order['orderId']
        order = self.binance_client.get_order(symbol='BTCUSDT', orderId=order_id)

        # self.telegram_bot.send_message(f"Market {direction} order of size {size} at {price}")
    
    def get_average_entry_price():
        avg_entry_price = 26000
        return avg_entry_price
    
    def reset(self):
        self.entry_price = 0
        self.avg_entry_price = 0
        self.hit_tp = False
        self.current_volume = self.base_order_size
    
    def buy_check_tp_sl_increment(self, current_price):
        increment_price = self.entry_price * (1 + self.current_increment_pct)
        take_profit_price = self.entry_price * (1 + self.take_profit_pct)
        if not self.hit_tp:
            stop_loss_price = self.avg_entry_price * (1 - self.stop_loss_pct)
        else:
            # if self.breakeven_threshold_pct > 0:
            stop_loss_price = self.avg_entry_price * (1 + self.breakeven_threshold_pct)
            # else:
            #     stop_loss_price = self.avg_entry_price * (1 - self.breakeven_threshold_pct)

        if current_price > take_profit_price:       # hit take profit
            self.close_position()
            self.reset()
            return
        
        if current_price < stop_loss_price:         # hit stop loss
            self.close_position()
            self.reset()
            return

        if current_price > increment_price:         # increment level exceeded
            self.current_volume = (self.current_volume * self.volume_scale) - self.current_volume
            self.place_market_order(self.current_volume / self.get_mark_price(), self.initial_direction)
            self.avg_entry_price = self.get_average_entry_price()
            self.current_increment_pct += self.base_increment_pct
            self.hit_tp = True
    
    def sell_check_tp_sl_increment(self, current_price):
        increment_price = self.entry_price * (1 - self.current_increment_pct)
        take_profit_price = self.entry_price * (1 - self.take_profit_pct)
        if not self.hit_tp:
            stop_loss_price = self.avg_entry_price * (1 + self.stop_loss_pct)
        else:
            stop_loss_price = self.avg_entry_price * (1 + self.breakeven_threshold_pct*-1)  # multiplied by -1 since the positives and negatives will opposite in case of short

        if current_price < take_profit_price:       # hit take profit
            self.close_position()
            self.reset()
            return
        
        if current_price > stop_loss_price:         # hit stop loss
            self.close_position()
            self.reset()
            return

        if current_price < increment_price:         # increment level exceeded
            self.current_volume = (self.current_volume * self.volume_scale) - self.current_volume
            self.place_market_order(self.current_volume / self.get_mark_price(), self.initial_direction)
            self.avg_entry_price = self.get_average_entry_price()
            self.current_increment_pct += self.base_increment_pct
            self.hit_tp = True

    def run(self):
        self.telegram_bot.send_message("HELLO11111")
        while True:
            time.sleep(2)
            if self.avg_entry_price == 0:    # not in position
                self.place_market_order(self.current_volume / self.get_mark_price(), self.initial_direction)
                self.entry_price = self.avg_entry_price = self.get_average_entry_price()
            
            else:    # already in position
                current_price = self.get_mark_price()
                if self.initial_direction.lower() == "buy":
                    self.buy_check_tp_sl_increment(current_price)

                elif self.initial_direction.lower() == "sell":
                    self.sell_check_tp_sl_increment(current_price)