import pandas as pd
import streamlit as st
import yfinance as yf

# Page Configuration
st.set_page_config(
page_title="Technical & Options Stock Scanner",
page_icon="📈",
layout="wide",
)

st.title("Interactive Stock & Options Screener")
st.write(
"Filter stocks based on RSI, volume, and options open interest data."
)

# Sidebar for User Inputs
st.sidebar.header("Scanner Parameters")

default_watchlist = "AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META, NFLX, AMD"
tickers_input = st.sidebar.text_area(
"Enter Tickers (comma-separated)", default_watchlist
)
watchlist = [t.strip().upper() for t in tickers_input.split(",")]

rsi_threshold = st.sidebar.slider(
"Max RSI (Oversold Filter)", min_value=10, max_value=50, value=30, step=1
)
volume_multiplier = st.sidebar.slider(
"Volume Multiplier vs 20-Day SMA",
min_value=1.0,
max_value=3.0,
value=1.5,
step=0.1,
)
timeframe = st.sidebar.selectbox("Historical Period", ["3mo", "6mo", "1y"], index=1)

st.sidebar.subheader("Options Open Interest (Nearest Expiry)")
include_options = st.sidebar.checkbox(
"Fetch Options Data", value=True
)
min_total_oi = st.sidebar.number_input(
"Min Total Open Interest", min_value=0, value=10000, step=5000
)


def calculate_rsi(series, period=14):
delta = series.diff()
gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
rs = gain / loss
return 100 - (100 / (1 + rs))


if st.sidebar.button("Run Scanner"):
results = []

with st.spinner(
"Fetching market data, indicators, and options chains..."
):
for symbol in watchlist:
try:
ticker = yf.Ticker(symbol)
df = ticker.history(period=timeframe)

if df.empty or len(df) < 30:
continue

if isinstance(df.columns, pd.MultiIndex):
df.columns = df.columns.get_level_values(0)

# Calculate indicators natively
df["RSI"] = calculate_rsi(df["Close"], period=14)
df["Vol_SMA_20"] = df["Volume"].rolling(window=20).mean()

latest = df.iloc[-1]
current_price = float(latest["Close"])
current_rsi = float(latest["RSI"])
current_vol = float(latest["Volume"])
avg_vol = float(latest["Vol_SMA_20"])

is_rsi_match = current_rsi < rsi_threshold
is_vol_match = current_vol > (volume_multiplier * avg_vol)

if not (is_rsi_match and is_vol_match):
continue

total_oi = 0
call_oi = 0
put_oi = 0
pc_ratio = 0.0

if include_options:
exp_dates = ticker.options
if exp_dates:
nearest_expiry = exp_dates[0]
opt_chain = ticker.option_chain(nearest_expiry)

call_oi = int(opt_chain.calls["openInterest"].fillna(0).sum())
put_oi = int(opt_chain.puts["openInterest"].fillna(0).sum())
total_oi = call_oi + put_oi

if call_oi > 0:
pc_ratio = round(put_oi / call_oi, 2)

if include_options and total_oi < min_total_oi:
continue

results.append({
"Ticker": symbol,
"Price ($)": round(current_price, 2),
"RSI (14)": round(current_rsi, 2),
"Volume": int(current_vol),
"20D Avg Volume": int(avg_vol),
"Call OI": call_oi if include_options else "N/A",
"Put OI": put_oi if include_options else "N/A",
"Total OI": total_oi if include_options else "N/A",
"P/C Ratio": pc_ratio if include_options else "N/A",
})

except Exception as e:
st.error(f"Error processing {symbol}: {e}")

if results:
result_df = pd.DataFrame(results)
st.success(f"Found {len(result_df)} matching stocks!")
st.dataframe(result_df, use_container_width=True)
else:
st.warning(
"No stocks matched your current criteria. Try loosening the filters."
