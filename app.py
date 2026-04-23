"""
ACC102 Track 4 - Advanced Interactive Stock Analysis Tool
Author: [Your Name]
Date: April 2026
Description: Multi-view stock analysis dashboard with WRDS (CRSP) and Yahoo Finance support.
             Optimized for faster WRDS queries.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime
import os

# ----- Try to import data sources -----
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    import wrds
    WRDS_AVAILABLE = True
except ImportError:
    WRDS_AVAILABLE = False

# ----- Page Config -----
st.set_page_config(page_title="Advanced Stock Analyzer", layout="wide")
st.title("📊 Advanced Stock Analysis Dashboard")
st.markdown("Multi-view analysis tool with WRDS (CRSP) and Yahoo Finance support.")

# ----- Helper function to load local fallback data -----
@st.cache_data
def load_fallback_data():
    file_path = os.path.join(os.path.dirname(__file__), "sample_stock_data.csv")
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        return df
    return None

# ----- WRDS Data Fetching (Optimized) -----
@st.cache_resource
def get_wrds_connection():
    """Establish WRDS connection once and cache it."""
    if not WRDS_AVAILABLE:
        return None, "WRDS package not installed. Run: pip install wrds"
    try:
        conn = wrds.Connection()
        return conn, None
    except Exception as e:
        return None, f"WRDS connection failed: {e}"

def get_stock_data_from_wrds(tickers, start_date, end_date):
    """Fetch daily stock prices from CRSP via WRDS."""
    if not tickers:
        return None
    
    try:
        conn, error = get_wrds_connection()
        if error:
            st.error(error)
            return None
        
        ticker_str = "', '".join([t.upper() for t in tickers])
        
        query = f"""
        SELECT a.ticker, b.date, b.prc
        FROM crsp.dsf AS b
        JOIN crsp.stocknames AS a ON b.permno = a.permno
        WHERE a.ticker IN ('{ticker_str}')
        AND b.date BETWEEN '{start_date}' AND '{end_date}'
        AND b.prc > 0
        ORDER BY a.ticker, b.date
        """
        
        st.info(f"⏳ Querying CRSP for {len(tickers)} tickers... This may take 15-30 seconds.")
        
        df = conn.raw_sql(query)
        
        if df.empty:
            return None
        
        df['prc'] = df['prc'].abs()
        prices = df.pivot(index='date', columns='ticker', values='prc')
        
        return prices
    except Exception as e:
        st.error(f"WRDS fetch error: {e}")
        return None

# ----- Sidebar Controls -----
st.sidebar.header("🎮 Data Source & Controls")

data_source = st.sidebar.radio(
    "Select data source:",
    options=["Yahoo Finance", "WRDS (CRSP)", "Local CSV (Fallback)"],
    index=0
)

# Stock selection
st.sidebar.subheader("📋 Stock Selection")

if data_source == "WRDS (CRSP)":
    ticker_input = st.sidebar.text_input(
        "Enter tickers (comma-separated):",
        value="AAPL, MSFT, GOOGL, NVDA, JPM, TSLA"
    )
    tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
else:
    input_mode = st.sidebar.radio("Input mode:", ["Select from list", "Manual entry"])
    if input_mode == "Select from list":
        ticker_options = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "JPM", "NVDA", "META",
                          "WMT", "JNJ", "V", "PG", "UNH", "HD", "DIS", "MA", "BAC", "KO"]
        tickers = st.sidebar.multiselect(
            "Select stock tickers:",
            options=ticker_options,
            default=["AAPL", "MSFT", "GOOGL", "NVDA"]
        )
    else:
        ticker_input = st.sidebar.text_input(
            "Enter tickers (comma-separated):",
            value="AAPL, MSFT, GOOGL, NVDA"
        )
        tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

# Date range
start_date = st.sidebar.date_input("Start date", value=pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End date", value=datetime.today())

# Chart options
st.sidebar.subheader("📈 Chart Options")
indicator = st.sidebar.selectbox(
    "Select indicator:",
    options=["Adjusted Close Price", "Daily Returns (%)", "Cumulative Return (Base=1)", "Rolling Volatility (30-day)"],
    index=2
)

chart_type = st.sidebar.selectbox(
    "Select chart type:",
    options=["Line Chart", "Bar Chart (Latest Values)", "Correlation Heatmap", "Risk-Return Scatter"],
    index=0
)

normalize = st.sidebar.checkbox("Normalize to 100 at start", value=False)
if indicator == "Rolling Volatility (30-day)":
    window = st.sidebar.slider("Rolling window (days):", 5, 90, 30)
else:
    window = 30

analyze_button = st.sidebar.button("🚀 Fetch Data & Analyze")

# ----- Main Logic -----
if analyze_button:
    if not tickers:
        st.warning("Please select at least one ticker.")
    else:
        prices = None
        data_source_used = ""
        
        with st.spinner(f"Fetching data from {data_source}..."):
            if data_source == "WRDS (CRSP)" and WRDS_AVAILABLE:
                prices = get_stock_data_from_wrds(tickers, start_date, end_date)
                if prices is not None and not prices.empty:
                    data_source_used = f"WRDS CRSP ({len(prices)} trading days)"
                else:
                    st.warning("WRDS fetch failed. Falling back to Yahoo Finance...")
            
            if prices is None or prices.empty:
                if YFINANCE_AVAILABLE:
                    try:
                        data = yf.download(tickers, start=start_date, end=end_date, progress=False)
                        if 'Adj Close' in data.columns:
                            prices = data['Adj Close']
                        elif 'Close' in data.columns:
                            prices = data['Close']
                        else:
                            prices = data
                        if not prices.empty:
                            data_source_used = "Yahoo Finance (live data)"
                    except Exception as e:
                        st.info(f"Yahoo Finance failed: {e}")
                
            if prices is None or prices.empty:
                st.info("⚠️ Switching to local sample data.")
                fallback_df = load_fallback_data()
                if fallback_df is not None:
                    mask = (fallback_df.index >= pd.to_datetime(start_date)) & (fallback_df.index <= pd.to_datetime(end_date))
                    available = [t for t in tickers if t in fallback_df.columns]
                    if available:
                        prices = fallback_df.loc[mask, available]
                    data_source_used = "Local sample data (CSV)"
        
        if prices is not None and not prices.empty:
            st.success(f"✅ Data loaded: {data_source_used} | {len(prices)} days | {len(tickers)} stocks")
            
            returns = prices.pct_change().dropna()
            cum_returns = (1 + returns).cumprod()
            rolling_vol = returns.rolling(window=window).std() * np.sqrt(252) * 100
            
            if indicator == "Adjusted Close Price":
                plot_data = prices
                y_label = "Price (USD)"
            elif indicator == "Daily Returns (%)":
                plot_data = returns * 100
                y_label = "Daily Return (%)"
            elif indicator == "Cumulative Return (Base=1)":
                plot_data = cum_returns
                y_label = "Cumulative Return"
            else:
                plot_data = rolling_vol
                y_label = f"{window}-Day Rolling Volatility (%)"
            
            if normalize and indicator != "Daily Returns (%)":
                plot_data = plot_data / plot_data.iloc[0] * 100
                y_label = "Normalized Value"
            
            if chart_type == "Line Chart":
                fig = px.line(plot_data, title=f"{indicator} Over Time",
                             labels={"value": y_label, "index": "Date", "variable": "Ticker"})
                fig.update_layout(legend_title_text='', hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Bar Chart (Latest Values)":
                latest = plot_data.iloc[-1]
                fig = px.bar(x=latest.index, y=latest.values,
                            title=f"Latest {indicator}", color=latest.index, text_auto='.2f')
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Correlation Heatmap":
                corr = returns.corr()
                fig = px.imshow(corr, text_auto=True, aspect="auto",
                               title="Correlation Matrix", color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Risk-Return Scatter":
                ann = 252
                scatter = []
                for t in returns.columns:
                    avg = returns[t].mean() * ann * 100
                    vol = returns[t].std() * np.sqrt(ann) * 100
                    sharpe = avg / vol if vol != 0 else 0
                    scatter.append({"Ticker": t, "Return (%)": avg, "Volatility (%)": vol, "Sharpe": sharpe})
                sc_df = pd.DataFrame(scatter)
                fig = px.scatter(sc_df, x="Volatility (%)", y="Return (%)", text="Ticker",
                                title="Risk-Return Profile", color="Sharpe", color_continuous_scale="RdYlGn")
                fig.update_traces(textposition='top center', marker=dict(size=12))
                st.plotly_chart(fig, use_container_width=True)
            
            # Metrics Table
            st.subheader("📋 Risk & Return Summary")
            ann = 252
            metrics = []
            for t in returns.columns:
                avg = returns[t].mean()
                vol = returns[t].std()
                ann_ret = avg * ann * 100
                ann_vol = vol * np.sqrt(ann) * 100
                sharpe = (avg / vol) * np.sqrt(ann) if vol != 0 else 0
                total = (cum_returns[t].iloc[-1] - 1) * 100
                max_dd = (cum_returns[t] / cum_returns[t].cummax() - 1).min() * 100
                metrics.append({"Ticker": t, "Total Return (%)": round(total, 2),
                               "Ann. Return (%)": round(ann_ret, 2), "Ann. Vol (%)": round(ann_vol, 2),
                               "Sharpe": round(sharpe, 2), "Max DD (%)": round(max_dd, 2)})
            mdf = pd.DataFrame(metrics)
            st.dataframe(mdf.style.format({"{:.2f}": mdf.select_dtypes(float).columns})
                        .background_gradient(cmap='RdYlGn', subset=['Total Return (%)', 'Sharpe'])
                        .background_gradient(cmap='RdYlGn_r', subset=['Ann. Vol (%)', 'Max DD (%)']),
                        use_container_width=True)
            
            with st.expander("🔍 Raw data (last 10 rows)"):
                st.dataframe(prices.tail(10))
            
            csv = prices.to_csv()
            st.download_button("📥 Download CSV", csv, f"stock_data_{start_date}_{end_date}.csv", "text/csv")
        else:
            st.error("No data loaded. Check tickers, dates, or network.")
else:
    st.info("👈 Configure settings and click 'Fetch Data & Analyze' to begin.")
