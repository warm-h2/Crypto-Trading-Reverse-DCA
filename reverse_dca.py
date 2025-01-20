import time
import math
import pandas as pd
import numpy as np
from binance.enums import *
import json

class ReverseDCA:
	def __init__(self, binance_client, telegram_bot, ticker, initial_direction, 
              	base_order_size, volume_scale, breakeven_threshold_pct, stop_loss_pct, 
               increment_pct, take_profit_pct, setting_message, sma_period, sma_tf, hma1_period, hma2_period, hma3_period, hma1_tf, hma2_tf, hma3_tf):
		self.telegram_bot = telegram_bot
		self.binance_client = binance_client
		self.ticker = ticker
		self.initial_direction = initial_direction
		self.base_order_size = base_order_size
		self.volume_scale = volume_scale
		self.breakeven_threshold_pct = breakeven_threshold_pct / 100
		self.stop_loss_pct = stop_loss_pct / 100
		self.base_increment_pct = increment_pct / 100
		self.take_profit_pct = take_profit_pct / 100
		self.first_entry_price = 0
		self.filled_price = 0
		self.avg_entry_price = 0
		self.hit_tp = False
		self.current_volume = self.base_order_size
		self.stop_loss_order_id = 0
		self.take_profit_order_id = 0
		self.take_profit_price = 0
		self.setting_message = setting_message
		self.sma_period = sma_period
		self.sma_tf = sma_tf
		self.hma1_period = hma1_period
		self.hma2_period = hma2_period
		self.hma3_period = hma3_period
		self.hma1_tf = hma1_tf
		self.hma2_tf = hma2_tf
		self.hma3_tf = hma3_tf
		self.filter_met = False
		self.increment_num = 0

		if self.initial_direction.lower() == "buy":
			self.stop_market_direction = SIDE_SELL
			self.stop_market_side = 'LONG'
		elif self.initial_direction.lower() == "sell":
			self.stop_market_direction = SIDE_BUY
			self.stop_market_side = 'SHORT'
		else:
			self.telegram_bot.send_message("Invalid initial direction provided in the config. Exiting!")
			exit()

		try:
			# comprehensive information about the futures trading market on Binance.
			futures_exchange_info = self.binance_client.futures_exchange_info() 
			# with open("1.json", "w") as file:
			# 	file.write(f'------------------{self.ticker}-----------------------\n\n{futures_exchange_info}\n\naaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
				# json.dump(futures_exchange_info, file, indent =4)
			# print(f'futures_exchange_info => {futures_exchange_info}')
			# find and return the information for a specific trading pair (specified by ticker) within the list of futures symbols.
			symbol_info = next(item for item in futures_exchange_info['symbols'] if item['symbol'] == ticker) 
			# indicates the number of decimal places allowed for the quantity of a particular trading pair. 
			self.quantity_precision = int(symbol_info['quantityPrecision']) 
			# indicates the number of decimal places allowed for the price of a particular trading pair on Binance's futures market.
			self.price_precision = int(symbol_info['pricePrecision']) 
		except Exception as e:
			print(f"Exception! Getting futures exchange info. {e}. Exiting!")
			# self.telegram_bot.send_message(f"Exception! Getting futures exchange info. {e}. Exiting!")

			# exit()
 
	def get_tf_val(self, timeframe):
		if timeframe == "1M":
			return self.binance_client.KLINE_INTERVAL_1MINUTE
		elif timeframe == "5M":
			return self.binance_client.KLINE_INTERVAL_5MINUTE
		elif timeframe == "15M":
			return self.binance_client.KLINE_INTERVAL_15MINUTE
		elif timeframe == "30M":
			return self.binance_client.KLINE_INTERVAL_30MINUTE
		elif timeframe == "1H":
			return self.binance_client.KLINE_INTERVAL_1HOUR
		elif timeframe == "4H":
			return self.binance_client.KLINE_INTERVAL_4HOUR
		elif timeframe == "1D":
			return self.binance_client.KLINE_INTERVAL_1DAY
		elif timeframe == "1W":
			return self.binance_client.KLINE_INTERVAL_1WEEK
		elif timeframe == "0":
			return self.binance_client.KLINE_INTERVAL_1MINUTE
		else:
			self.telegram_bot.send_message("Invalid initial timeframe provided in the config. Exiting!")
			exit()
	
	def get_start_str(self, timeframe, period):
		if timeframe == "1M":
			return '{} minute ago UTC'.format(period+5)
		elif timeframe == "5M":
			return '{} minute ago UTC'.format((period+1)*5)
		elif timeframe == "15M":
			return '{} minute ago UTC'.format((period+1)*15)
		elif timeframe == "30M":
			return '{} minute ago UTC'.format((period+1)*30)
		elif timeframe == "1H":
			return '{} hour ago UTC'.format(period+5)
		elif timeframe == "4H":
			return '{} hour ago UTC'.format((period+1)*4)
		elif timeframe == "1D":
			return '{} day ago UTC'.format(period+5)
		elif timeframe == "1W":
			return '{} week ago UTC'.format(period+5)
		elif timeframe == "0":
			return '{} minute ago UTC'.format(period+5)
		else:
			self.telegram_bot.send_message("Invalid initial timeframe or period provided in the config. Exiting!")
			exit()
	
	def get_mark_price(self):
		while True:
			try:
				return float(self.binance_client.futures_symbol_ticker(symbol=self.ticker)['price'])    # futures price
			except Exception as e:
				self.telegram_bot.send_message(f"Exception! Getting mark price. Retrying... {e}")
				time.sleep(2)

	def get_order_info(self, order_id):
		while True:
			try:
				order = self.binance_client.futures_get_order(symbol=self.ticker, orderId=order_id)
				return order
			except Exception as e:
				return 'None'
				self.telegram_bot.send_message(f"Exception! Getting Order information. Retrying...{e}")
				time.sleep(2)

	def check_signal_reversal(self, current_signals_invalid):
		if current_signals_invalid:
			# Require confirmation over multiple periods
			self.reversal_counter += 1
			if self.reversal_counter >= self.reversal_confirmation_periods:
				self.close_position()
				self.reset()
		else:
			self.reversal_counter = 0

	def check_opened_position(self):
		while True:
			try:
				open_positions = self.binance_client.futures_position_information(symbol=self.ticker)    # returns details relevant to your position.
				print(f"open_positions => {open_positions}")
				if float(open_positions[0]['entryPrice']) == 0:
					return -1
				else :
					return open_positions[0]

			except Exception as e:
				# self.telegram_bot.send_message(f"Exception! Get open positions. Retrying... {e}")
				return -1
				# time.sleep(2)
	
	def close_position(self):
		open_position = self.check_opened_position()
		print(f'Here is close_position :  open_position => {open_position}')
		if open_position != -1:
			size = float(open_position['positionAmt'])
			current_positionSide = open_position['positionSide']
			if size > 0:
				side = SIDE_SELL
				close_positionSide = "LONG"
			elif size < 0:
				side = SIDE_BUY
				close_positionSide = "SHORT"
			else:
				self.telegram_bot.send_message("Invalid position size!")
				# print("Invalid position size!")
				return
			
		while True:
			try:
				order = self.binance_client.futures_create_order(symbol=self.ticker, side=side, 
													 type=ORDER_TYPE_MARKET, quantity=abs(size))   # futures 
				break
			except Exception as e:
				self.telegram_bot.send_message(f"Exception! Placing Close position market order. Retrying... {e}")
				time.sleep(10)
	
	def place_market_order(self, size, direction, mark_price):
		if direction.lower() == "buy":
			direction = SIDE_BUY
			position_side = 'LONG'
		elif direction.lower() == "sell":
			direction = SIDE_SELL
			position_side = 'SHORT'
		else:
			self.telegram_bot.send_message(f"Invalid direction {direction}!")
			# print(f"Invalid direction {direction}!")
			return
		
		while True:
			try:
				order = self.binance_client.futures_create_order(symbol=self.ticker, side=direction, 
													 type=ORDER_TYPE_MARKET, quantity=abs(size))   # futures 
				break
			except Exception as e:
				# self.telegram_bot.send_message(f"Exception! Placing market order. Retrying... {e}")
				# return
				time.sleep(10)

		time.sleep(1)
		_order = self.get_order_info(order['orderId'])
		
		order_status = _order['status'].lower()
		fill_price = float(_order['avgPrice'])
		self.filled_price = fill_price
		if order_status == "filled":
			open_position = self.check_opened_position()
			if open_position != -1:
				position_size = float(open_position['positionAmt'])
				self.avg_entry_price = float(open_position['entryPrice'])
				self.telegram_bot.send_message(f"Market {direction} order of size {round(size, self.quantity_precision)} "
								               f"{self.ticker} filled at ${fill_price}. Market price at that time: ${mark_price}. "
								   			   f"Current {direction} position size: {position_size} {self.ticker}.")

	def cancel_order(self, order_id):
		order = self.get_order_info(order_id)   # futures
		order_status = order['status'].lower()
		if order_status.lower() != "filled":
			while True:
				try:
					self.binance_client.futures_cancel_order(symbol=self.ticker, orderId=order_id)
					# self.telegram_bot.send_message("Order canceled!")
					break
				except Exception as e:
					self.telegram_bot.send_message(f"Exception! Canceling order. Retrying... {e}")

					time.sleep(10)
					
	def place_stop_market_order(self, stop_price):
		open_position = self.check_opened_position()
		if open_position != -1:
			size = float(open_position['positionAmt'])

		stop_price = round(stop_price, self.price_precision)
		while True:
			try:
				order = self.binance_client.futures_create_order(symbol=self.ticker, side=self.stop_market_direction, 
													 type=FUTURE_ORDER_TYPE_STOP_MARKET, stopPrice=stop_price, 
													 quantity=abs(size))   # futures 
				break
			except Exception as e:
				# self.telegram_bot.send_message(f"Exception! Placing market order. Retrying... {e}")

				time.sleep(10)

		self.stop_order_id = order['orderId']
		self.telegram_bot.send_message(f"Stop Loss Market {self.stop_market_direction} order of size "
								       f"{round(abs(size), self.quantity_precision)} {self.ticker} placed at {stop_price}")
		return self.stop_order_id

	def place_take_profit_market_order(self, stop_price):
		open_position = self.check_opened_position()
		if open_position != -1:
			size = float(open_position['positionAmt'])

		stop_price = round(stop_price, self.price_precision)
		while True:
			try:
				order = self.binance_client.futures_create_order(symbol=self.ticker, side=self.stop_market_direction, 
													 type=FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET, stopPrice=stop_price, 
													 quantity=abs(size))   # futures 
				break
			except Exception as e:
				# self.telegram_bot.send_message(f"Exception! Placing market order. Retrying... {e}")
				
				time.sleep(2)

		self.stop_order_id = order['orderId']
		self.telegram_bot.send_message(f"Take Profit Market {self.stop_market_direction} order of size "
								 	   f"{round(abs(size), self.quantity_precision)} {self.ticker} placed at {stop_price}")
		return self.stop_order_id
	
	def place_initial_tpsl_orders(self):
		if self.initial_direction.lower() == "buy":
			self.take_profit_price = self.first_entry_price * (1 + self.take_profit_pct)
			stop_loss_price = self.first_entry_price * (1 - self.stop_loss_pct)
		else:
			self.take_profit_price = self.first_entry_price * (1 - self.take_profit_pct)
			stop_loss_price = self.first_entry_price * (1 + self.stop_loss_pct)

		self.telegram_bot.send_message(f"Placing initial Take profit order.")
		# print(f"Placing initial Take profit order.")
		self.take_profit_order_id = self.place_take_profit_market_order(self.take_profit_price)
		self.telegram_bot.send_message(f"Placing initial Stop loss order.")
		# print(f"Placing initial Stop Loss order.")
		self.stop_loss_order_id = self.place_stop_market_order(stop_loss_price) 
		
	def reset(self):
		self.first_entry_price = 0
		self.filled_price = 0
		self.avg_entry_price = 0
		self.hit_tp = False
		self.filter_met = False
		self.increment_num = 0
		self.current_volume = self.base_order_size
		if self.stop_loss_order_id != 0:
			self.cancel_order(self.stop_loss_order_id)
			self.stop_loss_order_id = 0
		if self.take_profit_order_id != 0:
			self.cancel_order(self.take_profit_order_id)
			self.take_profit_order_id = 0
		self.take_profit_price = 0   

	def buy_check_tp_sl_increment(self, current_price):
		increment_price = self.first_entry_price + self.first_entry_price*self.base_increment_pct
		take_profit_order = self.get_order_info(self.take_profit_order_id)
		stop_loss_order = self.get_order_info(self.stop_loss_order_id)
		tp_order_status = take_profit_order['status'].lower()
		sl_order_status = stop_loss_order['status'].lower()

		if tp_order_status == 'filled':       # hit take profit
			self.telegram_bot.send_message(f"$$$ TAKE PROFIT HIT! Closing open position and sleeping for 10 seconds.")
			# print(f"$$$TAKE PROFIT HIT! Closing open position and sleeping for 10 seconds.")
			self.reset()
			time.sleep(2)
			return
		
		if sl_order_status == 'filled':         # hit stop loss
			if not self.hit_tp:
				self.telegram_bot.send_message(f"!!! STOP LOSS HIT! Closing open position and sleeping for 10 seconds")
			else:
				self.telegram_bot.send_message(f"### BREAK EVEN HIT! Closing open position and sleeping for 10 seconds")
			# print(f"!!!STOP LOSS HIT! Closing open position and sleeping for 10 seconds")
			self.reset()
			time.sleep(2)
			return

		if current_price >= increment_price:         # increment level exceeded
			self.increment_num += 1
			self.telegram_bot.send_message(f"Increment price reached. Scaling volume by {self.volume_scale}x. ({self.increment_num}th order)")
			# print(f"Increment price reached. Scaling volume by {self.volume_scale}x")
			scaled_volume = self.current_volume * self.volume_scale
			self.current_volume = scaled_volume
			mark_price = self.get_mark_price()
			self.place_market_order(round(scaled_volume / mark_price, self.quantity_precision), self.initial_direction, mark_price)
			self.first_entry_price = self.filled_price
			print("filled price : ", self.filled_price)
			print("average price : ", self.avg_entry_price)
			self.update_sl_tp_order()
			self.hit_tp = True

	def sell_check_tp_sl_increment(self, current_price):
		print("Here is sell_check_tp_sl_increment")
		increment_price = self.first_entry_price - self.first_entry_price*self.base_increment_pct
		take_profit_order = self.get_order_info(self.take_profit_order_id)
		stop_loss_order = self.get_order_info(self.stop_loss_order_id)
		tp_order_status = take_profit_order['status'].lower()
		sl_order_status = stop_loss_order['status'].lower()
		print(f"Here is sell_check_tp_sl_increment.  tp_order_status =>{tp_order_status}")
		if tp_order_status == 'filled':       # hit take profit
			self.telegram_bot.send_message(f"$$$ TAKE PROFIT HIT! Closing open position and sleeping for 10 seconds.")
			# print(f"$$$TAKE PROFIT HIT! Closing open position and sleeping for 10 seconds.")
			self.reset()
			time.sleep(2)
			return
		
		if sl_order_status == 'filled':         # hit stop loss
			if not self.hit_tp:
				self.telegram_bot.send_message(f"!!! STOP LOSS HIT! Closing open position and sleeping for 10 seconds")
			else:
				self.telegram_bot.send_message(f"### BREAK EVEN HIT! Closing open position and sleeping for 10 seconds")
			# print(f"!!!STOP LOSS HIT! Closing open position and sleeping for 10 seconds")
			self.reset()
			time.sleep(2)
			return
		print(f"Here is sell_check_tp_sl_increment.  current_price =>{current_price}   increment_price=>{increment_price}")
		if current_price <= increment_price:         # increment level exceeded

			self.increment_num += 1
			self.telegram_bot.send_message(f"Increment price reached. Scaling volume by {self.volume_scale}x. ({self.increment_num}th order)")
			# print(f"Increment price reached. Scaling volume by {self.volume_scale}x")
			scaled_volume = self.current_volume * self.volume_scale
			self.current_volume = scaled_volume
			mark_price = self.get_mark_price()
			self.place_market_order(round(scaled_volume / mark_price, self.quantity_precision), self.initial_direction, mark_price)
			self.first_entry_price = self.filled_price
			print("filled price : ", self.filled_price)
			print("average price : ", self.avg_entry_price)
			self.update_sl_tp_order()
			self.hit_tp = True

	def update_sl_tp_order(self):
		if self.initial_direction.lower() == "buy":
			stop_loss_price = self.avg_entry_price * (1 + self.breakeven_threshold_pct)
		else:
			stop_loss_price = self.avg_entry_price * (1 + self.breakeven_threshold_pct*-1)  # multiplied by -1 in sell trade
		self.telegram_bot.send_message(f"Canceling existing Stop Loss & Take Profit order to update them!")

		self.cancel_order(self.stop_loss_order_id)
		self.stop_loss_order_id = self.place_stop_market_order(stop_loss_price)
		self.cancel_order(self.take_profit_order_id)
		self.take_profit_order_id = self.place_take_profit_market_order(self.take_profit_price)
	
	def update_sl_tp_order(self):
		if self.increment_num > 0:
			# Use breakeven threshold after first increment
			stop_loss_price = self.avg_entry_price * (1 + self.breakeven_threshold_pct)
		else:
			# Use initial stop loss before first increment
			stop_loss_price = self.first_entry_price * (1 - self.stop_loss_pct)

	def calculate_sma(self, prices, period, sma_tf):
		if period == 0 or sma_tf == '0':
			return 0
		else:
			sma = pd.Series(prices).rolling(window=period).mean().iloc[-1]
			return sma

	def calculate_wma(self, prices, period):
		weights = np.arange(1, period + 1)
		wma = prices.rolling(period).apply(lambda prices: np.dot(prices, weights)/weights.sum(), raw=True)
		return wma

	def calculate_hma(self, prices, period, hma_tf):
		if period == 0 or hma_tf == '0':
			return 0
		else:
			half_length = math.ceil(period / 2)
			sqrt_length = round(math.sqrt(period))

			hma_prices_series = pd.Series(prices)

			wma_half = self.calculate_wma(hma_prices_series, half_length)
			wma_full = self.calculate_wma(hma_prices_series, period)

			diff_wma = 2 * wma_half - wma_full
			hma = self.calculate_wma(diff_wma, sqrt_length)
			
			return hma.iloc[-1]
	
	def get_historical_klines(self, interval, start_str):
		while True:
			try:
				klines = self.binance_client.futures_historical_klines(symbol=self.ticker, interval=interval, start_str=start_str)
				return klines
			except Exception as e:
				# self.telegram_bot.send_message(f"Exception! Getting Historical Klines. Retrying... {e}")
				return 'None'
				time.sleep(2)

	def update_sl_tp_order(self):
		if self.increment_num > 0:
			# Use breakeven threshold after first increment
			stop_loss_price = self.avg_entry_price * (1 + self.breakeven_threshold_pct)
		else:
			# Use initial stop loss before first increment
			stop_loss_price = self.first_entry_price * (1 - self.stop_loss_pct)


	def isAvailable(self) :		
		# getting historical candle data

		# print(datetime.now().strftime("%H:%M:%S"))
		sma_klines = self.get_historical_klines(self.get_tf_val(self.sma_tf), self.get_start_str(self.sma_tf, self.sma_period))				
		# Parse the closing prices
		# getting historical candle data
		hma1_klines = self.get_historical_klines(self.get_tf_val(self.hma1_tf), self.get_start_str(self.hma1_tf, self.hma1_period*3))
		hma2_klines = self.get_historical_klines(self.get_tf_val(self.hma2_tf), self.get_start_str(self.hma2_tf, self.hma2_period*3))
		hma3_klines = self.get_historical_klines(self.get_tf_val(self.hma3_tf), self.get_start_str(self.hma3_tf, self.hma3_period*3))
		
		if sma_klines =='None' or hma1_klines=='None' or hma2_klines=='None' or  hma3_klines=='None' :
			print("Error getting historical klines----1-->")
			return False

		sma_prices = [float(kline[4]) for kline in sma_klines][:-1]
		# Parse the closing prices
		hma1_prices = [float(kline[4]) for kline in hma1_klines][:-1]
		hma2_prices = [float(kline[4]) for kline in hma2_klines][:-1]
		hma3_prices = [float(kline[4]) for kline in hma3_klines][:-1]

		# Calculate current SMA and HMA values
		current_sma = self.calculate_sma(sma_prices, self.sma_period, self.sma_tf)
		current_hma1 = self.calculate_hma(hma1_prices, self.hma1_period, self.hma1_tf)
		current_hma2 = self.calculate_hma(hma2_prices, self.hma2_period, self.hma2_tf)
		current_hma3 = self.calculate_hma(hma3_prices, self.hma3_period, self.hma3_tf)
		sma_last_closed_candle = 0 if self.sma_tf == "0" or self.sma_period == 0 else sma_prices[-1]
		hma1_last_closed_candle = 0 if self.hma1_tf == "0" or self.hma1_period == 0 else hma1_prices[-1]
		hma2_last_closed_candle = 0 if self.hma2_tf == "0" or self.hma2_period == 0 else hma2_prices[-1]
		hma3_last_closed_candle = 0 if self.hma3_tf == "0" or self.hma3_period == 0 else hma3_prices[-1]

		# print(f"{self.ticker}----->  \n"
			# f"SMA Last Candle's Price is {sma_last_closed_candle} and SMA_{self.sma_period} is {round(current_sma, 4)}. \n" 
			# f"HMA 1 Last Candle's Price is {hma1_last_closed_candle} and HMA_{self.hma1_period} is {round(current_hma1, 4)}. \n"
			# f"HMA 2 Last Candle's Price is {hma2_last_closed_candle} and HMA_{self.hma2_period} is {round(current_hma2, 4)}. \n"
			# f"HMA 3 Last Candle's Price is {hma3_last_closed_candle} and HMA_{self.hma3_period} is {round(current_hma3, 4)}. \n")
							
		if self.avg_entry_price == 0:
			if self.initial_direction.lower() == "buy":
				if (sma_last_closed_candle > current_sma != 0 or current_sma == 0) and \
					   (hma1_last_closed_candle > current_hma1 != 0 or current_hma1 == 0) and \
					   (hma2_last_closed_candle > current_hma2 != 0 or current_hma2 == 0) and \
					   (hma3_last_closed_candle > current_hma3 != 0 or current_hma3 == 0):
					return True
			elif self.initial_direction.lower() == "sell":
				if (sma_last_closed_candle < current_sma != 0 or current_sma == 0) and \
					(hma1_last_closed_candle < current_hma1 != 0 or current_hma1 == 0) and \
					(hma2_last_closed_candle < current_hma2 != 0 or current_hma2 == 0) and \
					(hma3_last_closed_candle < current_hma3 != 0 or current_hma3 == 0) :
					return True
		return False
 
	def run(self): 				
		# getting historical candle data
		sma_klines = self.get_historical_klines(self.get_tf_val(self.sma_tf), self.get_start_str(self.sma_tf, self.sma_period))				
		# Parse the closing prices
		sma_prices = [float(kline[4]) for kline in sma_klines][:-1]

		# getting historical candle data
		hma1_klines = self.get_historical_klines(self.get_tf_val(self.hma1_tf), self.get_start_str(self.hma1_tf, self.hma1_period*3))
		hma2_klines = self.get_historical_klines(self.get_tf_val(self.hma2_tf), self.get_start_str(self.hma2_tf, self.hma2_period*3))
		hma3_klines = self.get_historical_klines(self.get_tf_val(self.hma3_tf), self.get_start_str(self.hma3_tf, self.hma3_period*3))
		
		# Parse the closing prices
		hma1_prices = [float(kline[4]) for kline in hma1_klines][:-1]
		hma2_prices = [float(kline[4]) for kline in hma2_klines][:-1]
		hma3_prices = [float(kline[4]) for kline in hma3_klines][:-1]

		# Calculate current SMA and HMA values
		current_sma = self.calculate_sma(sma_prices, self.sma_period, self.sma_tf)
		current_hma1 = self.calculate_hma(hma1_prices, self.hma1_period, self.hma1_tf)
		current_hma2 = self.calculate_hma(hma2_prices, self.hma2_period, self.hma2_tf)
		current_hma3 = self.calculate_hma(hma3_prices, self.hma3_period, self.hma3_tf)
		sma_last_closed_candle = 0 if self.sma_tf == "0" or self.sma_period == 0 else sma_prices[-1]
		hma1_last_closed_candle = 0 if self.hma1_tf == "0" or self.hma1_period == 0 else hma1_prices[-1]
		hma2_last_closed_candle = 0 if self.hma2_tf == "0" or self.hma2_period == 0 else hma2_prices[-1]
		hma3_last_closed_candle = 0 if self.hma3_tf == "0" or self.hma3_period == 0 else hma3_prices[-1]
		print(f"avg_entry_price => {self.avg_entry_price}")
		open_position = self.check_opened_position()
		if open_position == -1:    # not in position
			mark_price = self.get_mark_price()

			if self.initial_direction.lower() == "buy":
				if (sma_last_closed_candle > current_sma or current_sma == 0) and \
					(hma1_last_closed_candle > current_hma1 or current_hma1 == 0) and \
					(hma2_last_closed_candle > current_hma2 or current_hma2 == 0) and \
					(hma3_last_closed_candle > current_hma3 or current_hma3 == 0):
					
					self.telegram_bot.send_message(f"Conditions have been met, so Starting the bot!!! \n"
													f"SMA Last Candle's Price is {sma_last_closed_candle} and SMA_{self.sma_period} is {round(current_sma, 4)}. \n" 
													f"HMA 1 Last Candle's Price is {hma1_last_closed_candle} and HMA_{self.hma1_period} is {round(current_hma1, 4)}. \n"
													f"HMA 2 Last Candle's Price is {hma2_last_closed_candle} and HMA_{self.hma2_period} is {round(current_hma2, 4)}. \n"
													f"HMA 3 Last Candle's Price is {hma3_last_closed_candle} and HMA_{self.hma3_period} is {round(current_hma3, 4)}. \n")
					order_size = round(self.current_volume / mark_price, self.quantity_precision)
					self.telegram_bot.send_message(f"****************************************************\n "
													f"First entry. Opening new position with base volume {order_size} {self.ticker}")
					self.place_market_order(order_size, self.initial_direction, mark_price)			
					self.first_entry_price = self.filled_price
					# Place initial take profit and stop loss orders.
					self.place_initial_tpsl_orders()		
				elif (sma_last_closed_candle < current_sma or hma1_last_closed_candle < current_hma1 or 
						hma2_last_closed_candle < current_hma2 or hma3_last_closed_candle < current_hma3) and not self.filter_met:
					
					self.telegram_bot.send_message(f"Pauses the bot until the condition is met!!! \n"
													f"SMA Last Candle's Price is {sma_last_closed_candle} and SMA_{self.sma_period} is {round(current_sma, 4)}. \n" 
													f"HMA 1 Last Candle's Price is {hma1_last_closed_candle} and HMA_{self.hma1_period} is {round(current_hma1, 4)}. \n"
													f"HMA 2 Last Candle's Price is {hma2_last_closed_candle} and HMA_{self.hma2_period} is {round(current_hma2, 4)}. \n"
													f"HMA 3 Last Candle's Price is {hma3_last_closed_candle} and HMA_{self.hma3_period} is {round(current_hma3, 4)}. \n")
					self.filter_met = True
			elif self.initial_direction.lower() == "sell":
				if (sma_last_closed_candle < current_sma or current_sma == 0) and \
					(hma1_last_closed_candle < current_hma1 or current_hma1 == 0) and \
					(hma2_last_closed_candle < current_hma2 or current_hma2 == 0) and \
					(hma3_last_closed_candle < current_hma3 or current_hma3 == 0) :
					
					self.telegram_bot.send_message(f"Conditions have been met, so Starting the bot!!! \n"
													f"SMA Last Candle's Price is {sma_last_closed_candle} and SMA_{self.sma_period} is {round(current_sma, 4)}. \n" 
													f"HMA 1 Last Candle's Price is {hma1_last_closed_candle} and HMA_{self.hma1_period} is {round(current_hma1, 4)}. \n"
													f"HMA 2 Last Candle's Price is {hma2_last_closed_candle} and HMA_{self.hma2_period} is {round(current_hma2, 4)}. \n"
													f"HMA 3 Last Candle's Price is {hma3_last_closed_candle} and HMA_{self.hma3_period} is {round(current_hma3, 4)}. \n")
					order_size = round(self.current_volume / mark_price, self.quantity_precision)
					print(f"------------------------------------------------------------\n current_volume => {self.current_volume}   mark_price=>{mark_price}  order_size=>{order_size}\n-------------------------------------------------")
					self.telegram_bot.send_message(f"****************************************************\n First entry."
													f"Opening new position with base volume {order_size} {self.ticker}")
					self.place_market_order(order_size, self.initial_direction, mark_price)			
					self.first_entry_price = self.filled_price
					# Place initial take profit and stop loss orders.
					self.place_initial_tpsl_orders()
				elif (sma_last_closed_candle > current_sma or hma1_last_closed_candle > current_hma1 or 
						hma2_last_closed_candle > current_hma2 or hma3_last_closed_candle > current_hma3) and not self.filter_met:
					
					self.telegram_bot.send_message(f"Pauses the bot until the condition is met!!! \n"
													f"SMA Last Candle's Price is {sma_last_closed_candle} and SMA_{self.sma_period} is {round(current_sma, 4)}. \n" 
													f"HMA 1 Last Candle's Price is {hma1_last_closed_candle} and HMA_{self.hma1_period} is {round(current_hma1, 4)}. \n"
													f"HMA 2 Last Candle's Price is {hma2_last_closed_candle} and HMA_{self.hma2_period} is {round(current_hma2, 4)}. \n"
													f"HMA 3 Last Candle's Price is {hma3_last_closed_candle} and HMA_{self.hma3_period} is {round(current_hma3, 4)}. \n")
					self.filter_met = True
			else:
				self.telegram_bot.send_message("Invalid initial direction provided in the config. Exiting!")
				exit()
		else:    # already in position
				print("Here is already in position")
				current_price = self.get_mark_price()
				if self.initial_direction.lower() == "buy":
					if (sma_last_closed_candle > current_sma or current_sma == 0) and \
					   (hma1_last_closed_candle > current_hma1 or current_hma1 == 0) and \
					   (hma2_last_closed_candle > current_hma2 or current_hma2 == 0) and \
					   (hma3_last_closed_candle > current_hma3 or current_hma3 == 0):
						
						self.buy_check_tp_sl_increment(current_price)
					else:
						self.telegram_bot.send_message(f"Signals reversed. Closing positions!!! \n"
									 				   f"SMA Last Candle's Price is {sma_last_closed_candle} and SMA_{self.sma_period} is {round(current_sma, 4)}. \n" 
													   f"HMA 1 Last Candle's Price is {hma1_last_closed_candle} and HMA_{self.hma1_period} is {round(current_hma1, 4)}. \n"
													   f"HMA 2 Last Candle's Price is {hma2_last_closed_candle} and HMA_{self.hma2_period} is {round(current_hma2, 4)}. \n"
													   f"HMA 3 Last Candle's Price is {hma3_last_closed_candle} and HMA_{self.hma3_period} is {round(current_hma3, 4)}. \n")
						self.close_position()
						self.reset()
				elif self.initial_direction.lower() == "sell":
					if (sma_last_closed_candle < current_sma or current_sma == 0) and \
					   (hma1_last_closed_candle < current_hma1 or current_hma1 == 0) and \
					   (hma2_last_closed_candle < current_hma2 or current_hma2 == 0) and \
					   (hma3_last_closed_candle < current_hma3 or current_hma3 == 0) :
						
						print("Here is already in position. I have met the criteria")
						self.sell_check_tp_sl_increment(current_price)
					else:
						print("Here is already in position. I haven't met the criteria")
						self.telegram_bot.send_message(f"Signals reversed. Closing positions!!! \n"
									 				   f"SMA Last Candle's Price is {sma_last_closed_candle} and SMA_{self.sma_period} is {round(current_sma, 4)}. \n" 
													   f"HMA 1 Last Candle's Price is {hma1_last_closed_candle} and HMA_{self.hma1_period} is {round(current_hma1, 4)}. \n"
													   f"HMA 2 Last Candle's Price is {hma2_last_closed_candle} and HMA_{self.hma2_period} is {round(current_hma2, 4)}. \n"
													   f"HMA 3 Last Candle's Price is {hma3_last_closed_candle} and HMA_{self.hma3_period} is {round(current_hma3, 4)}. \n")
						self.close_position()
						self.reset()
				else:
					self.telegram_bot.send_message("Invalid initial direction provided in the config. Exiting!")
					exit()