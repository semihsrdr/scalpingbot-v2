import config
import pandas as pd
import pandas_ta as ta
from exchange import get_client
import json

def get_market_summary(symbol=config.TRADING_SYMBOLS[0], interval='1m', limit=100):
    """
    Fetches recent candles, calculates EMA20, EMA50, RSI and returns a JSON summary for the LLM.
    """
    try:
        client = get_client()
        # 1. Fetch recent candles
        # ccxt fetch_ohlcv format: [ [timestamp, open, high, low, close, volume], ... ]
        ohlcv = client.fetch_ohlcv(symbol, timeframe=interval, limit=limit)
        
        # 2. Convert to Pandas DataFrame
        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        df = pd.DataFrame(ohlcv, columns=columns)
        
        # Convert necessary columns to numeric types
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])

        # 3. Calculate Indicators (using pandas-ta)
        df.ta.ema(length=20, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.rsi(length=14, append=True)
        
        # 4. Select the last candle (most recent data)
        last_candle = df.iloc[-1]

        # Fetch the most recent price using fetch_ticker
        ticker = client.fetch_ticker(symbol)
        current_price = ticker['last'] if ticker and 'last' in ticker else last_candle['close']

        # 5. Create summary JSON for the LLM
        summary = {
            "symbol": symbol,
            "current_price": current_price,
            "ema_20": round(last_candle['EMA_20'], 2),
            "ema_50": round(last_candle['EMA_50'], 2),
            "rsi_14": round(last_candle['RSI_14'], 2),
            "market_trend": "bullish" if last_candle['EMA_20'] > last_candle['EMA_50'] else "bearish"
        }
        
        return summary
        
    except Exception as e:
        print(f"Error getting market data for {symbol}: {e}")
        return None

# You can test this file directly
if __name__ == "__main__":
    # Test with the first symbol from the config
    test_symbol = config.TRADING_SYMBOLS[0]
    summary = get_market_summary(symbol=test_symbol)
    if summary:
        print(f"\n--- Market Summary for {test_symbol} ---")
        print(json.dumps(summary, indent=2))
