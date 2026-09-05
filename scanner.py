import os
import time
import pandas as pd
import pandas_ta as ta  # High-performance technical analysis library
import yfinance as yf

def calculate_rsi(ticker_symbol):
    """Calculates the current 14-day Relative Strength Index (RSI)."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        # Fetching 3 months of historical daily candles to properly seed the RSI
        df = ticker.history(period="3mo", interval="1d")
        
        if df.empty or len(df) < 20:
            return None
            
        # Compute RSI using pandas_ta implementation
        df.ta.rsi(close="Close", length=14, append=True)
        
        # Extract the most recent calculation row
        latest_rsi = df['RSI_14'].iloc[-1]
        return latest_rsi if not pd.isna(latest_rsi) else None
    except Exception:
        return None

def calculate_open_interest(ticker_symbol, max_expirations=3):
    """Aggregates the sum of Open Interest from upcoming options expiration cycles."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        expiration_dates = ticker.options
        
        if not expiration_dates:
            return 0
            
        total_oi = 0
        # Sampling the closest expiration periods maximizes execution speed
        for date in expiration_dates[:max_expirations]:
            chain = ticker.option_chain(date)
            
            # Aggregate OI values while cleaning NaN instances
            calls_oi = chain.calls['openInterest'].dropna().sum()
            puts_oi = chain.puts['openInterest'].dropna().sum()
            
            total_oi += (calls_oi + puts_oi)
            # Modest rest window to protect your system from API rate limits
            time.sleep(0.1)
            
        return int(total_oi)
    except Exception:
        return 0

def run_screener(ticker_universe):
    """Executes filtering rules across target stock lists."""
    qualified_matches = []
    
    print(f"🔄 Scanning {len(ticker_universe)} symbols for RSI < 30 and OI > 10,000...")
    
    for symbol in ticker_universe:
        # Optimization Guardrail: Calculate technical metrics first to filter noise 
        rsi = calculate_rsi(symbol)
        
        if rsi is not None and rsi < 30:
            print(f"🎯 Match found on Momentum: {symbol} (RSI: {rsi:.2f}). Extracting OI...")
            
            # Fetch options density only for technical qualifiers
            open_interest = calculate_open_interest(symbol)
            
            if open_interest >= 10000:
                qualified_matches.append({
                    "Ticker": symbol,
                    "RSI_14": round(rsi, 2),
                    "Open_Interest": open_interest
                })
                print(f"✅ Added: {symbol} matches all parameters.")
        
        # Base latency buffer to prevent cloud server environment bans
        time.sleep(0.5)
        
    return pd.DataFrame(qualified_matches)

if __name__ == "__main__":
    # Sample liquid subset list for testing parameters
    test_universe = ["CSCO", "BA", "BRK-B", "URI", "HON", "MMM", "AAPL", "MSFT"]
    
    results_df = run_screener(test_universe)
    
    print("\n📊 Final Scanner Results:")
    if not results_df.empty:
        print(results_df.to_string(index=False))
    else:
        print("No securities currently match the technical boundaries.")
