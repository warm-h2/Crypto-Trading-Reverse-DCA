import numpy as np
import pandas as pd
from binance.client import Client

class HMAFilter:
    def __init__(self, client):
        self.client = client
        self.timeframes = ['4h', '1d']
    
    def calculate_hma(self, data, period=20):
        # Calculate WMA with period/2
        half_length = int(period/2)
        wmaf = self.weighted_ma(data, half_length)
        
        # Calculate WMA for period
        wmaf2 = self.weighted_ma(data, period)
        
        # Calculate raw HMA
        raw_hma = (2 * wmaf) - wmaf2
        
        # Calculate final HMA
        hma = self.weighted_ma(raw_hma, int(np.sqrt(period)))
        return hma
    
    def weighted_ma(self, data, period):
        weights = np.arange(1, period + 1)
        wma = data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum())
        return wma
    
    def get_filtered_coins(self, symbols):
        filtered_coins = []
        
        for symbol in symbols:
            above_hma = True
            
            for timeframe in self.timeframes:
                klines = self.client.get_historical_klines(
                    symbol=symbol,
                    interval=timeframe,
                    limit=50
                )
                
                if not klines:
                    above_hma = False
                    break
                    
                df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
                df['close'] = df['close'].astype(float)
                
                # Calculate HMA
                hma = self.calculate_hma(df['close'])
                current_price = df['close'].iloc[-1]
                current_hma = hma.iloc[-1]
                
                if current_price <= current_hma:
                    above_hma = False
                    break
            
            if above_hma:
                filtered_coins.append(symbol)
        
        return filtered_coins
    
    def check_entry_conditions(self, symbol):
        # Get 1-hour data
        klines = self.client.get_historical_klines(
            symbol=symbol,
            interval='1h',
            limit=50
        )
        
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'])
        df['close'] = df['close'].astype(float)
        
        # Calculate HMA for 1-hour timeframe
        hma = self.calculate_hma(df['close'])
        
        current_price = df['close'].iloc[-1]
        previous_price = df['close'].iloc[-2]
        current_hma = hma.iloc[-1]
        previous_hma = hma.iloc[-2]
        
        # Long entry condition: Price crosses above HMA
        long_entry = previous_price <= previous_hma and current_price > current_hma
        
        # Short entry condition: Price crosses below HMA
        short_entry = previous_price >= previous_hma and current_price < current_hma
        
        return {
            'symbol': symbol,
            'long_entry': long_entry,
            'short_entry': short_entry,
            'current_price': current_price,
            'hma': current_hma
        }
    
    def scan_for_entries(self, filtered_coins):
        entry_signals = []
        
        for symbol in filtered_coins:
            entry_conditions = self.check_entry_conditions(symbol)
            if entry_conditions['long_entry'] or entry_conditions['short_entry']:
                entry_signals.append(entry_conditions)
        
        return entry_signals
          
# Usage example
def main():
    client = Client()
    hma_filter = HMAFilter(client)
    
    # Get all USDT pairs
    exchange_info = client.get_exchange_info()
    symbols = [s['symbol'] for s in exchange_info['symbols'] if s['symbol'].endswith('USDT')]
    
    # Filter coins above HMA
    filtered_coins = hma_filter.get_filtered_coins(symbols)
    
    print("Coins above HMA on both 4h and 1d timeframes:")
    for coin in filtered_coins:
        print(coin)
    
    entry_signals = hma_filter.scan_for_entries(filtered_coins)
    print("\nEntry Signals:")
    for signal in entry_signals:
        if signal['long_entry']:
            print(f"LONG Entry for {signal['symbol']} at {signal['current_price']}")
        if signal['short_entry']:
            print(f"SHORT Entry for {signal['symbol']} at {signal['current_price']}") 

if __name__ == "__main__":
    main()