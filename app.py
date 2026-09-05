import streamlit as st
import yfinance as yf
import pandas as pd

def scan_stock(ticker_symbol):
    try:
        # 1. Fetch historical data for RSI calculation (need at least 30-40 days)
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="3mo")
        
        if len(hist) < 14:
            return None
        
        # Calculate 14-day RSI using pandas_ta
        hist.ta.rsi(length=14, append=True)
        current_rsi = hist['RSI_14'].iloc[-1]
        
        # Filter 1: RSI under 30
        if current_rsi >= 30 or pd.isna(current_rsi):
            return None
            
        # 2. Fetch Options Chain Data for Open Interest
        total_open_interest = 0
        expirations = ticker.options # Gets all available expiration dates
        
        # To keep your Streamlit app fast, only check the first 3 closest expiration dates
        for date in expirations[:3]:
            opt_chain = ticker.option_chain(date)
            
            # Sum up Open Interest from both Calls and Puts
            calls_oi = opt_chain.calls['openInterest'].sum()
            puts_oi = opt_chain.puts['openInterest'].sum()
            
            total_open_interest += (calls_oi + puts_oi)
            
        # Filter 2: Cumulative Open Interest above 10,000
        if total_open_interest > 10000:
            return {
                "Ticker": ticker_symbol,
                "RSI": round(current_rsi, 2),
                "Total_OI": int(total_open_interest)
            }
            
    except Exception as e:
        # Avoid crashing the Streamlit UI loop if a specific ticker fails
        return None
    
    return None

# Quick UI implementation example
st.title("Oversold & Highly Liquid Scanner")
test_tickers = ["CSCO", "BA", "BRK-B", "AAPL", "URI"]

if st.button("Run Custom Scan"):
    results = []
    for t in test_tickers:
        res = scan_stock(t)
        if res:
            results.append(res)
            
    if results:
        st.write(pd.DataFrame(results))
    else:
        st.write("No stocks met the criteria right now.")
