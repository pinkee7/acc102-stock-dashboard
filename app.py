"""
ACC102 Track 4 - Interactive Stock Performance Tool
Author: [Your Name]
Date: April 2026
Description: A Streamlit app to compare cumulative returns and risk metrics.
              Falls back to local sample data if Yahoo Finance is unreachable.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# ----- Try to import yfinance, but don't crash if not installed -----
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# ----- Page Config -----
st.set_page_config(page_title="Stock Comparison Tool", layout="wide")
st.title("📊 Stock Return & Volatility Dashboard")
st.markdown("Compare cumulative returns and risk metrics for selected US stocks.")

# ----- Helper function to load local fallback data -----
@st.cache_data
def load_fallback_data():
    """Load sample stock data from local CSV file."""
    file_path = os.path.join(os.path.dirname(__file__), "sample_stock_data.csv")
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        return df
    else:
        return None

# ----- Sidebar Controls -----
st.sidebar.header("User Controls")

# Stock selection
available_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "JPM", "NVDA", "META"]
tickers = st.sidebar.multiselect(
    "Select stock tickers:",
    options=available_tickers,
    default=["AAPL", "MSFT", "GOOGL"]
)

# Date range
start_date = st.sidebar.date_input("Start date", value=pd.to_datetime("2024-01-01"))
end_date = st.sidebar.date_input("End date", value=datetime.today())

analyze_button = st.sidebar.button("Fetch Data & Analyze")

# ----- Main Logic -----
if analyze_button:
    if not tickers:
        st.warning("Please select at least one ticker.")
    else:
        prices = None
        data_source = ""
        
        # ---- Attempt 1: Try Yahoo Finance (if available) ----
        if YFINANCE_AVAILABLE:
            with st.spinner("Attempting to download from Yahoo Finance..."):
                try:
                    data = yf.download(tickers, start=start_date, end=end_date, progress=False)
                    if 'Adj Close' in data.columns:
                        prices = data['Adj Close']
                    elif 'Close' in data.columns:
                        prices = data['Close']
                    else:
                        prices = data
                    
                    if not prices.empty:
                        data_source = "Yahoo Finance (live data)"
                    else:
                        prices = None
                except Exception as e:
                    st.info(f"Yahoo Finance download failed: {e}")
                    prices = None
        
        # ---- Attempt 2: Fallback to local CSV ----
        if prices is None or prices.empty:
            st.info("⚠️ Switching to local sample data (offline mode).")
            fallback_df = load_fallback_data()
            if fallback_df is not None:
                # Filter dates and tickers from the local data
                mask = (fallback_df.index >= pd.to_datetime(start_date)) & (fallback_df.index <= pd.to_datetime(end_date))
                prices = fallback_df.loc[mask, tickers] if mask.any() else pd.DataFrame()
                data_source = "Local sample data (CSV file)"
            else:
                st.error("Local fallback data file not found. Please ensure 'sample_stock_data.csv' is in the project folder.")
                prices = None
        
        # ---- Process and display ----
        if prices is not None and not prices.empty:
            st.success(f"✅ Data loaded successfully from: {data_source}")
            
            # Calculate daily returns
            returns = prices.pct_change().dropna()
            
            # Cumulative returns (base = 1)
            cum_returns = (1 + returns).cumprod()
            
            # Plot
            fig = px.line(
                cum_returns,
                title="Cumulative Return (Base = 1.0)",
                labels={"value": "Cumulative Return", "index": "Date", "variable": "Ticker"}
            )
            fig.update_layout(legend_title_text='')
            st.plotly_chart(fig, use_container_width=True)
            
            # Risk & Return Metrics
            ann_factor = 252
            metrics_list = []
            for ticker in returns.columns:
                avg_return = returns[ticker].mean()
                vol = returns[ticker].std()
                ann_return = avg_return * ann_factor * 100
                ann_vol = vol * (ann_factor ** 0.5) * 100
                sharpe = (avg_return / vol) * (ann_factor ** 0.5) if vol != 0 else 0
                
                metrics_list.append({
                    "Ticker": ticker,
                    "Annualized Return (%)": round(ann_return, 2),
                    "Annualized Volatility (%)": round(ann_vol, 2),
                    "Sharpe Ratio (approx)": round(sharpe, 2)
                })
            
            metrics_df = pd.DataFrame(metrics_list)
            st.subheader("📈 Risk & Return Summary")
            st.dataframe(
                metrics_df.style.format({
                    "Annualized Return (%)": "{:.2f}",
                    "Annualized Volatility (%)": "{:.2f}",
                    "Sharpe Ratio (approx)": "{:.2f}"
                }),
                use_container_width=True
            )
            
            # Show raw data
            with st.expander("Show raw price data (last 10 rows)"):
                st.dataframe(prices.tail(10))
        else:
            st.error("No data could be loaded. Please check your network or the local CSV file.")
else:
    st.info("👈 Select tickers and date range, then click 'Fetch Data & Analyze' to begin.")