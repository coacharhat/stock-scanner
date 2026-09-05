import os
import time
import pandas as pd
import yfinance as yf

def calculate_rsi(ticker_symbol):
    """Calculates 14-day RSI using pure pandas to prevent installation errors."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="3mo", interval="1d")
        
        if df.empty or len(df) < 15:
            return None
            
        # Calculate price changes
        delta = df['Close'].diff()
        
        # Separate gains and losses
        gain = (delta.where(delta > 0, 0)).copy()
        loss = (-delta.where(delta < 0, 0)).copy()
        
        # Calculate Wilder's Exponential Moving Average for RSI
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        latest_rsi = rsi.iloc[-1]
        return latest_rsi if not pd.isna(latest_rsi) else None
    except Exception:
        return None

def calculate_open_interest(ticker_symbol, max_expirations=3):
    """Aggregates Open Interest from the closest options chains."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        expiration_dates = ticker.options
        
        if not expiration_dates:
            return 0
            
        total_oi = 0
        for date in expiration_dates[:max_expirations]:
            chain = ticker.option_chain(date)
            calls_oi = chain.calls['openInterest'].dropna().sum()
            puts_oi = chain.puts['openInterest'].dropna().sum()
            total_oi += (calls_oi + puts_oi)
            time.sleep(0.1)
            
        return int(total_oi)
    except Exception:
        return 0

def run_screener(ticker_universe):
    qualified_matches = []
    print(f"🔄 Scanning {len(ticker_universe)} symbols...")
    
    for symbol in ticker_universe:
        rsi = calculate_rsi(symbol)
        
        if rsi is not None and rsi < 30:
            print(f"🎯 RSI Alert: {symbol} is at {rsi:.2f}")
            open_interest = calculate_open_interest(symbol)
            
            if open_interest >= 10000:
                qualified_matches.append({
                    "Ticker": symbol,
                    "RSI_14": round(rsi, 2),
                    "Open_Interest": open_interest
                })
                print(f"✅ Match Added: {symbol}")
        
        time.sleep(0.5) # Protects API from rate limits
        
    return pd.DataFrame(qualified_matches)

if __name__ == "__main__":
    test_universe = ["CSCO", "BA", "BRK-B", "URI", "HON", "MMM"]
    results_df = run_screener(test_universe)
    print("\n📊 Final Scanner Results:\n", results_df)
