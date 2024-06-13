import time
from binance.enums import *

class ReverseDCA:
	def __init__(self, binance_client, telegram_bot, ticker, initial_direction, base_order_size, volume_scale, breakeven_threshold_pct, stop_loss_pct, increment_pct, take_profit_pct):
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
		self.avg_entry_price = 0
		self.hit_tp = False
		self.current_volume = self.base_order_size
		self.stop_loss_order_id = 0
		self.take_profit_order_id = 0
		self.take_profit_price = 0

		if self.initial_direction.lower() == "buy":
			self.stop_market_direction = SIDE_SELL
		elif self.initial_direction.lower() == "sell":
			self.stop_market_direction = SIDE_BUY
		else:
			self.telegram_bot.send_message("Invalid initial direction provided in the config. Exiting!")
			# print("Invalid initial direction provided in the config. Exiting!")
			exit()

		try:
			futures_exchange_info = self.binance_client.futures_exchange_info()     # comprehensive information about the futures trading market on Binance.
			symbol_info = next(item for item in futures_exchange_info['symbols'] if item['symbol'] == ticker)     # find and return the information for a specific trading pair (specified by ticker) within the list of futures symbols.
			self.quantity_precision = int(symbol_info['quantityPrecision'])        # indicates the number of decimal places allowed for the quantity of a particular trading pair.
			self.price_precision = int(symbol_info['pricePrecision'])          # indicates the number of decimal places allowed for the price of a particular trading pair on Binance's futures market.
		except Exception as e:
			self.telegram_bot.send_message(f"Exception! Getting futures exchange info. {e}. Exiting!")
			# print(f"Exception! Getting futures exchange info. {e}. Exiting!")
			exit()
	
	def get_mark_price(self):
		while True:
			try:
				return float(self.binance_client.futures_symbol_ticker(symbol=self.ticker)['price'])    # futures price
				# return float(self.binance_client.get_margin_price_index(symbol="BTCUSDT")['price'])   # margin price
			except Exception as e:
				self.telegram_bot.send_message(f"Exception! Getting mark price. Retrying... {e}")
				# print(f"Exception! Getting mark price. Retrying... {e}")
				time.sleep(2)
	
	def check_opened_position(self):
		while True:
			try:
				open_positions = self.binance_client.futures_position_information(symbol=self.ticker)    # returns details relevant to your position in that specific futures contract.
				if float(open_positions[0]['entryPrice']) == 0:
					return -1
				return open_positions[0]

			except Exception as e:
				self.telegram_bot.send_message(f"Exception! Get open positions. Retrying... {e}")
				time.sleep(5)
	
	def close_position(self):
		open_position = self.check_opened_position()
		if open_position != -1:
			size = float(open_position['positionAmt'])
			if size > 0:
				side = "sell"
			elif size < 0:
				side = "buy"
			else:
				self.telegram_bot.send_message("Invalid position size!")
				# print("Invalid position size!")
				return
			
			self.place_market_order(size, side, self.get_mark_price())
	
	def place_market_order(self, size, direction, mark_price):
		if direction.lower() == "buy":
			direction = SIDE_BUY
		elif direction.lower() == "sell":
			direction = SIDE_SELL
		else:
			self.telegram_bot.send_message(f"Invalid direction {direction}!")
			# print(f"Invalid direction {direction}!")
			return
		
		while True:
			try:
				order = self.binance_client.futures_create_order(symbol=self.ticker, side=direction, type=ORDER_TYPE_MARKET, quantity=abs(size))   # futures 
				# order = self.binance_client.create_margin_order(symbol=self.ticker, side=direction, type=ORDER_TYPE_MARKET, timeInForce=TIME_IN_FORCE_GTC, quantity=size)      # margin
				break
			except Exception as e:
				self.telegram_bot.send_message(f"Exception! Placing market order. Retrying... {e}")
				# print(f"Exception! Placing market order. Retrying... {e}")
				time.sleep(5)

		time.sleep(1)
		while True:
			try:
				_order = self.binance_client.futures_get_order(symbol=self.ticker, orderId=order['orderId'])   # futures 
				# _order = self.binance_client.get_margin_order(symbol=self.ticker, orderId=order['orderId'])      # margin 
				break
			except Exception as e:
				self.telegram_bot.send_message(f"Exception! Getting order information. Retrying... {e}")
				print(f"Exception! Getting order information. Retrying... {e}")
				time.sleep(5)
		
		order_status = _order['status'].lower()
		fill_price = float(_order['avgPrice'])
		if order_status == "filled":
			open_position = self.check_opened_position()
			if open_position != -1:
				position_size = float(open_position['positionAmt'])
				self.avg_entry_price = float(open_position['entryPrice'])
				self.telegram_bot.send_message(f"Market {direction} order of size {round(size, self.quantity_precision)} {self.ticker} filled at ${fill_price}. Market price at that time: ${mark_price}. Current {direction} position size: {position_size} {self.ticker}.")
				# print(f"Market {direction} order of size {round(size, self.quantity_precision)} {self.ticker} filled at ${fill_price}. Market price at that time: ${mark_price}. Current {direction} position size: {position_size} {self.ticker}.")

	def cancel_order(self, order_id):
		order = self.binance_client.futures_get_order(symbol=self.ticker, orderId=order_id)   # futures
		order_status = order['status'].lower()
		if order_status.lower() != "filled":
			while True:
				try:
					self.binance_client.futures_cancel_order(symbol=self.ticker, orderId=order_id)
					self.telegram_bot.send_message("Order canceled!")
					# print("Order Canceled!")
					break
				except Exception as e:
					self.telegram_bot.send_message(f"Exception! Canceling order. Retrying... {e}")
					# print(f"Exception! Canceling order. Retrying... {e}")
					time.sleep(5)
					
	def place_stop_market_order(self, stop_price):
		open_position = self.check_opened_position()
		if open_position != -1:
			size = float(open_position['positionAmt'])

		stop_price = round(stop_price, self.price_precision)
		while True:
			try:
				order = self.binance_client.futures_create_order(symbol=self.ticker, side=self.stop_market_direction, type=FUTURE_ORDER_TYPE_STOP_MARKET, stopPrice=stop_price, quantity=abs(size))   # futures 
				# order = self.binance_client.create_margin_order(symbol=self.ticker, side=direction, type=ORDER_TYPE_MARKET, timeInForce=TIME_IN_FORCE_GTC, quantity=size)      # margin
				break
			except Exception as e:
				self.telegram_bot.send_message(f"Exception! Placing market order. Retrying... {e}")
				# print(f"Exception! Placing stop market order. Retrying... {e}")
				time.sleep(5)

		self.stop_order_id = order['orderId']
		self.telegram_bot.send_message(f"Stop market {self.stop_market_direction} order of size {round(abs(size), self.quantity_precision)} {self.ticker} placed at {stop_price}")
		# print(f"Stop market {self.stop_market_direction} order of size {round(abs(size), self.quantity_precision)} {self.ticker} placed at {stop_price}")
		return self.stop_order_id

	def place_take_profit_market_order(self, stop_price):
		open_position = self.check_opened_position()
		if open_position != -1:
			size = float(open_position['positionAmt'])

		stop_price = round(stop_price, self.price_precision)
		while True:
			try:
				order = self.binance_client.futures_create_order(symbol=self.ticker, side=self.stop_market_direction, type=FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET, stopPrice=stop_price, quantity=abs(size))   # futures 
				# order = self.binance_client.create_margin_order(symbol=self.ticker, side=direction, type=ORDER_TYPE_MARKET, timeInForce=TIME_IN_FORCE_GTC, quantity=size)      # margin
				break
			except Exception as e:
				self.telegram_bot.send_message(f"Exception! Placing market order. Retrying... {e}")
				# print(f"Exception! Placing market order(take profit). Retrying... {e}")
				time.sleep(5)

		self.stop_order_id = order['orderId']
		self.telegram_bot.send_message(f"Take profit market {self.stop_market_direction} order of size {round(abs(size), self.quantity_precision)} {self.ticker} placed at {stop_price}")
		# print(f"Take profit market {self.stop_market_direction} order of size {round(abs(size), self.quantity_precision)} {self.ticker} placed at {stop_price}")
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
		self.avg_entry_price = 0
		self.hit_tp = False
		self.current_volume = self.base_order_size
		if self.stop_loss_order_id != 0:
			self.cancel_order(self.stop_loss_order_id)
		if self.take_profit_order_id != 0:
			self.cancel_order(self.take_profit_order_id)
		self.stop_loss_order_id = 0
		self.take_profit_order_id = 0
		self.take_profit_price = 0     

	def buy_check_tp_sl_increment(self, current_price):
		increment_price = self.avg_entry_price + self.avg_entry_price*self.base_increment_pct
		take_profit_order = self.binance_client.futures_get_order(symbol=self.ticker, orderId=self.take_profit_order_id)
		stop_loss_order = self.binance_client.futures_get_order(symbol=self.ticker, orderId=self.stop_loss_order_id)
		tp_order_status = take_profit_order['status'].lower()
		sl_order_status = stop_loss_order['status'].lower()

		if tp_order_status == 'filled':       # hit take profit
			self.telegram_bot.send_message(f"TAKE PROFIT HIT! Closing open position and sleeping for 10 seconds.")
			# print(f"TAKE PROFIT HIT! Closing open position and sleeping for 10 seconds.")
			self.reset()
			time.sleep(10)
			return
		
		if sl_order_status == 'filled':         # hit stop loss
			self.telegram_bot.send_message(f"STOP LOSS HIT! Closing open position and sleeping for 10 seconds")
			# print(f"STOP LOSS HIT! Closing open position and sleeping for 10 seconds.")
			self.reset()
			time.sleep(10)
			return

		if current_price >= increment_price:         # increment level exceeded
			self.telegram_bot.send_message(f"Increment price reached. Scaling volume by {self.volume_scale}x")
			# print(f"Increment price reached. Scaling volume by {self.volume_scale}x")
			scaled_volume = self.current_volume * self.volume_scale
			self.current_volume = scaled_volume
			mark_price = self.get_mark_price()
			self.place_market_order(round(scaled_volume / mark_price, self.quantity_precision), self.initial_direction, mark_price)
			self.update_sl_tp_order()

	def update_sl_tp_order(self):
		if self.initial_direction.lower() == "buy":
			stop_loss_price = self.avg_entry_price * (1 + self.breakeven_threshold_pct)
		else:
			stop_loss_price = self.avg_entry_price * (1 + self.breakeven_threshold_pct*-1)  # multiplied by -1 since the positives and negatives will opposite in case of short
		self.telegram_bot.send_message(f"Canceling existing stop loss order and creating a new one at updated price!")
		# print(f"Canceling existing stop loss & take profit order and creating new one at updated price!")
		self.cancel_order(self.stop_loss_order_id)
		self.stop_loss_order_id = self.place_stop_market_order(stop_loss_price)
		self.cancel_order(self.take_profit_order_id)
		self.take_profit_order_id = self.place_take_profit_market_order(self.take_profit_price)

	def run(self):
		self.telegram_bot.send_message("Running Reverse DCA Stategy...")
		# print("Running Reverse DCA Strategy...")
		while True:
			time.sleep(1)
			if self.avg_entry_price == 0:    # not in position
				mark_price = self.get_mark_price()
				order_size = round(self.current_volume / mark_price, self.quantity_precision)
				self.telegram_bot.send_message(f"First entry. Opening new position with base volume {order_size} {self.ticker}")
				# print(f"First entry. Opening new position with base volume {order_size} {self.ticker}")
				self.place_market_order(order_size, self.initial_direction, mark_price)			
				self.first_entry_price = self.avg_entry_price

				self.place_initial_tpsl_orders()
			
			else:    # already in position
				current_price = self.get_mark_price()
				self.buy_check_tp_sl_increment(current_price)