"""
ACC102 Track 4 - Advanced Interactive Stock Analysis Tool
Author: [Your Name]
Date: April 2026
Description: Multi-view stock analysis dashboard with WRDS (CRSP) and Yahoo Finance support.
             Allows selection from virtually all US stocks when using WRDS.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
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
st.title("📊 Advanced Stock Analysis Dashboard (WRDS + Yahoo Finance)")
st.markdown("Multi-view analysis tool with access to comprehensive CRSP data via WRDS, plus Yahoo Finance fallback.")

# ----- Helper function to load local fallback data -----
@st.cache_data
def load_fallback_data():
    file_path = os.path.join(os.path.dirname(__file__), "sample_stock_data.csv")
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        return df
    else:
        return None

# ----- WRDS Data Fetching Functions -----
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_sp500_tickers_from_wrds():
    """Fetch S&P 500 constituents from CRSP via WRDS."""
    if not WRDS_AVAILABLE:
        return None, "WRDS package not installed. Run: pip install wrds"
    
    try:
        conn = wrds.Connection()
        # Query S&P 500 constituents - use recent date
        query = """
        SELECT DISTINCT a.permno, a.ticker, a.comnam
        FROM crsp.dsp500list_v2 AS sp500
        JOIN crsp.stocknames AS a
        ON sp500.permno = a.permno
        WHERE sp500.mbrenddt >= '2023-01-01'
        AND a.ticker IS NOT NULL
        ORDER BY a.ticker
        """
        df = conn.raw_sql(query)
        conn.close()
        return df, None
    except Exception as e:
        return None, f"WRDS connection failed: {e}"

@st.cache_data(ttl=3600)
def get_stock_data_from_wrds(tickers, start_date, end_date):
    """Fetch daily stock prices from CRSP via WRDS."""
    if not tickers:
        return None
    
    try:
        conn = wrds.Connection()
        
        # Convert ticker list to SQL IN clause format
        ticker_str = "', '".join(tickers)
        
        # Query daily stock data from CRSP
        query = f"""
        SELECT a.ticker, b.date, b.prc, b.ret
        FROM crsp.stocknames AS a
        JOIN crsp.dsf AS b ON a.permno = b.permno
        WHERE a.ticker IN ('{ticker_str}')
        AND b.date >= '{start_date}'
        AND b.date <= '{end_date}'
        AND b.prc > 0
        ORDER BY a.ticker, b.date
        """
        
        df = conn.raw_sql(query)
        conn.close()
        
        if df.empty:
            return None
        
        # Pivot to get prices (prc is price, taking absolute value for negative prices)
        df['prc'] = df['prc'].abs()
        prices = df.pivot(index='date', columns='ticker', values='prc')
        
        return prices
    except Exception as e:
        st.error(f"WRDS data fetch error: {e}")
        return None

# ----- Sidebar Controls (Enhanced) -----
st.sidebar.header("🎮 Data Source & User Controls")

# Data source selection
data_source = st.sidebar.radio(
    "Select data source:",
    options=["Yahoo Finance", "WRDS (CRSP)", "Local CSV (Fallback)"],
    index=0,
    help="WRDS requires valid credentials and university subscription. Yahoo Finance is free but may be blocked in some regions."
)

# WRDS credentials if selected
wrds_connected = False
if data_source == "WRDS (CRSP)" and WRDS_AVAILABLE:
    st.sidebar.subheader("WRDS Credentials")
    wrds_username = st.sidebar.text_input("WRDS Username")
    wrds_password = st.sidebar.text_input("WRDS Password", type="password")
    
    if st.sidebar.button("Connect to WRDS"):
        if wrds_username and wrds_password:
            with st.spinner("Connecting to WRDS and fetching S&P 500 tickers..."):
                # Test connection and get ticker list
                ticker_df, error = get_sp500_tickers_from_wrds()
                if error:
                    st.sidebar.error(error)
                else:
                    st.sidebar.success(f"Connected! Loaded {len(ticker_df)} tickers.")
                    wrds_connected = True
                    st.session_state['wrds_tickers'] = ticker_df
        else:
            st.sidebar.warning("Please enter WRDS credentials.")

# Stock selection
st.sidebar.subheader("📋 Stock Selection")

# Different ticker input based on data source
if data_source == "WRDS (CRSP)" and 'wrds_tickers' in st.session_state:
    ticker_options = st.session_state['wrds_tickers']['ticker'].tolist()
    default_tickers = ["AAPL", "MSFT", "GOOGL", "NVDA"] if all(t in ticker_options for t in ["AAPL", "MSFT", "GOOGL", "NVDA"]) else ticker_options[:4]
else:
    ticker_options = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "JPM", "NVDA", "META"]
    default_tickers = ["AAPL", "MSFT", "GOOGL", "NVDA"]

# Two input modes: select from list OR manual entry
input_mode = st.sidebar.radio("Input mode:", ["Select from list", "Manual entry (comma-separated)"])

if input_mode == "Select from list":
    tickers = st.sidebar.multiselect(
        "Select stock tickers:",
        options=ticker_options,
        default=[t for t in default_tickers if t in ticker_options]
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

# Indicator selection
st.sidebar.subheader("📈 Chart Options")
indicator = st.sidebar.selectbox(
    "Select indicator:",
    options=["Adjusted Close Price", "Daily Returns (%)", "Cumulative Return (Base=1)", "Rolling Volatility (30-day)"],
    index=2
)

chart_type = st.sidebar.selectbox(
    "Select chart type:",
    options=["Line Chart", "Bar Chart (Latest Values)", "Correlation Heatmap", "Portfolio Pie (Equal Weight)", "Risk-Return Scatter"],
    index=0
)

# Additional options
normalize = st.sidebar.checkbox("Normalize to 100 at start", value=False)
if indicator == "Rolling Volatility (30-day)":
    window = st.sidebar.slider("Rolling window (days):", min_value=5, max_value=90, value=30)
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
        
        # ---- Data fetching based on selected source ----
        with st.spinner(f"Fetching data from {data_source}..."):
            if data_source == "WRDS (CRSP)" and WRDS_AVAILABLE:
                # Try WRDS
                prices = get_stock_data_from_wrds(tickers, start_date, end_date)
                if prices is not None and not prices.empty:
                    data_source_used = f"WRDS CRSP ({len(prices)} trading days)"
                else:
                    st.warning("WRDS fetch failed or returned no data. Falling back to Yahoo Finance...")
            
            # Fallback to Yahoo Finance
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
                        st.info(f"Yahoo Finance download failed: {e}")
                
            # Final fallback to local CSV
            if prices is None or prices.empty:
                st.info("⚠️ Switching to local sample data (offline mode).")
                fallback_df = load_fallback_data()
                if fallback_df is not None:
                    mask = (fallback_df.index >= pd.to_datetime(start_date)) & (fallback_df.index <= pd.to_datetime(end_date))
                    available_in_fallback = [t for t in tickers if t in fallback_df.columns]
                    if available_in_fallback:
                        prices = fallback_df.loc[mask, available_in_fallback]
                    data_source_used = "Local sample data (CSV file)"
        
        # ---- Process and display ----
        if prices is not None and not prices.empty:
            st.success(f"✅ Data loaded from: {data_source_used} | {len(prices)} trading days | {len(tickers)} stocks")
            
            # Calculate metrics
            returns = prices.pct_change().dropna()
            cum_returns = (1 + returns).cumprod()
            rolling_vol = returns.rolling(window=window).std() * np.sqrt(252) * 100
            
            # Prepare plot data
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
                y_label = f"{window}-Day Rolling Volatility (Annualized %)"
            
            if normalize and indicator != "Daily Returns (%)":
                plot_data = plot_data / plot_data.iloc[0] * 100
                y_label = "Normalized Value (Base=100)"
            
            # Render selected chart
            if chart_type == "Line Chart":
                fig = px.line(plot_data, title=f"{indicator} Over Time",
                             labels={"value": y_label, "index": "Date", "variable": "Ticker"})
                fig.update_layout(legend_title_text='', hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Bar Chart (Latest Values)":
                latest_vals = plot_data.iloc[-1]
                fig = px.bar(x=latest_vals.index, y=latest_vals.values,
                            title=f"Latest {indicator} by Ticker",
                            labels={"x": "Ticker", "y": y_label},
                            color=latest_vals.index, text_auto='.2f')
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Correlation Heatmap":
                corr_matrix = returns.corr()
                fig = px.imshow(corr_matrix, text_auto=True, aspect="auto",
                               title="Correlation Matrix of Daily Returns",
                               color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Portfolio Pie (Equal Weight)":
                weights = [1/len(tickers)] * len(tickers)
                fig = px.pie(names=tickers, values=weights,
                            title="Equal-Weight Portfolio Allocation (Illustrative)", hole=0.4)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Risk-Return Scatter":
                ann_factor = 252
                scatter_data = []
                for t in returns.columns:
                    avg_ret = returns[t].mean() * ann_factor * 100
                    vol = returns[t].std() * np.sqrt(ann_factor) * 100
                    sharpe = avg_ret / vol if vol != 0 else 0
                    scatter_data.append({"Ticker": t, "Annualized Return (%)": avg_ret,
                                        "Annualized Volatility (%)": vol, "Sharpe": sharpe})
                scatter_df = pd.DataFrame(scatter_data)
                fig = px.scatter(scatter_df, x="Annualized Volatility (%)", y="Annualized Return (%)",
                                text="Ticker", title="Risk-Return Profile",
                                color="Sharpe", color_continuous_scale="RdYlGn")
                fig.update_traces(textposition='top center', marker=dict(size=12))
                st.plotly_chart(fig, use_container_width=True)
            
            # Risk & Return Metrics Table
            st.subheader("📋 Risk & Return Summary Statistics")
            ann_factor = 252
            metrics_list = []
            for ticker in returns.columns:
                avg_return = returns[ticker].mean()
                vol = returns[ticker].std()
                ann_return = avg_return * ann_factor * 100
                ann_vol = vol * (ann_factor ** 0.5) * 100
                sharpe = (avg_return / vol) * (ann_factor ** 0.5) if vol != 0 else 0
                total_return = (cum_returns[ticker].iloc[-1] - 1) * 100 if not cum_returns.empty else 0
                max_dd = (cum_returns[ticker] / cum_returns[ticker].cummax() - 1).min() * 100
                
                metrics_list.append({
                    "Ticker": ticker,
                    "Total Return (%)": round(total_return, 2),
                    "Annualized Return (%)": round(ann_return, 2),
                    "Annualized Volatility (%)": round(ann_vol, 2),
                    "Sharpe Ratio": round(sharpe, 2),
                    "Max Drawdown (%)": round(max_dd, 2)
                })
            
            metrics_df = pd.DataFrame(metrics_list)
            st.dataframe(
                metrics_df.style.format({
                    "Total Return (%)": "{:.2f}",
                    "Annualized Return (%)": "{:.2f}",
                    "Annualized Volatility (%)": "{:.2f}",
                    "Sharpe Ratio": "{:.2f}",
                    "Max Drawdown (%)": "{:.2f}"
                }).background_gradient(cmap='RdYlGn', subset=['Total Return (%)', 'Sharpe Ratio'])
                .background_gradient(cmap='RdYlGn_r', subset=['Annualized Volatility (%)', 'Max Drawdown (%)']),
                use_container_width=True
            )
            
            # Summary Cards
            st.subheader("📊 Quick Stats")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                best_idx = metrics_df['Total Return (%)'].idxmax()
                st.metric("🏆 Best Performer", metrics_df.loc[best_idx, 'Ticker'],
                         f"{metrics_df.loc[best_idx, 'Total Return (%)']:.2f}%")
            with col2:
                worst_idx = metrics_df['Total Return (%)'].idxmin()
                st.metric("📉 Worst Performer", metrics_df.loc[worst_idx, 'Ticker'],
                         f"{metrics_df.loc[worst_idx, 'Total Return (%)']:.2f}%")
            with col3:
                low_vol_idx = metrics_df['Annualized Volatility (%)'].idxmin()
                st.metric("🛡️ Lowest Volatility", metrics_df.loc[low_vol_idx, 'Ticker'],
                         f"{metrics_df.loc[low_vol_idx, 'Annualized Volatility (%)']:.2f}%")
            with col4:
                sharpe_idx = metrics_df['Sharpe Ratio'].idxmax()
                st.metric("⚖️ Best Sharpe", metrics_df.loc[sharpe_idx, 'Ticker'],
                         f"{metrics_df.loc[sharpe_idx, 'Sharpe Ratio']:.2f}")
            
            # Download button
            with st.expander("🔍 Show raw price data (last 10 rows)"):
                st.dataframe(prices.tail(10))
            
            csv = prices.to_csv()
            st.download_button(label="📥 Download price data as CSV",
                              data=csv, file_name=f"stock_data_{start_date}_{end_date}.csv", mime="text/csv")
        else:
            st.error("No data could be loaded. Please check your network, ticker symbols, or WRDS credentials.")
else:
    st.info("👈 Configure data source and analysis parameters in the sidebar, then click 'Fetch Data & Analyze' to begin.")
    
    st.markdown("""
    ### 📌 Data Source Options:
    - **Yahoo Finance**: Free, no login required. May be blocked in some regions.
    - **WRDS (CRSP)**: Comprehensive historical data for all US stocks. Requires university subscription and credentials.
    - **Local CSV**: Offline fallback using sample data included in the repository.
    
    *The app automatically falls back to the next available source if one fails.*
    """)
