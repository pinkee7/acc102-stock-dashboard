"""
ACC102 Track 4 - Advanced Interactive Stock Analysis Tool
Author: [Your Name]
Date: April 2026
Description: Multi-view stock analysis dashboard. Fetches data from a Kaggle dataset 
             with a local CSV file as a fallback.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import os

# Try to import kagglehub and yfinance
try:
    import kagglehub
    KAGGLEHUB_AVAILABLE = True
except ImportError:
    KAGGLEHUB_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# ----- Page Config -----
st.set_page_config(page_title="Advanced Stock Analyzer", layout="wide")
st.title("📊 Advanced Stock Analysis Dashboard")
st.markdown("Multi-view analysis tool for comparing US stocks with interactive visualizations, powered by real market data from Kaggle & Yahoo Finance.")

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

# ----- Sidebar Controls (Enhanced) -----
st.sidebar.header("🎮 User Controls")

# Data source selection
data_source_option = st.sidebar.radio(
    "Select data source:",
    options=["Kaggle (S&P 500 2020-2025)", "Yahoo Finance (Live)", "Local CSV (Fallback)"],
    index=0,
    help="Kaggle provides a rich, static dataset. Yahoo Finance fetches live data. Local CSV is a minimal backup."
)

# Stock selection
available_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "JPM", "NVDA", "META"]
tickers = st.sidebar.multiselect(
    "Select stock tickers:",
    options=available_tickers,
    default=["AAPL", "MSFT", "GOOGL", "NVDA"]
)

# Date range
start_date = st.sidebar.date_input("Start date", value=pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("End date", value=datetime.today())

# Indicator selection for line chart
st.sidebar.subheader("📈 Line Chart Options")
indicator = st.sidebar.selectbox(
    "Select indicator to display:",
    options=["Adjusted Close Price", "Daily Returns (%)", "Cumulative Return (Base=1)", "Rolling Volatility (30-day)"],
    index=2
)

# Chart type selection for main view
chart_type = st.sidebar.selectbox(
    "Select chart type:",
    options=["Line Chart", "Bar Chart (Latest Values)", "Correlation Heatmap", "Portfolio Pie (Equal Weight)"],
    index=0
)

# Rolling window for volatility
if indicator == "Rolling Volatility (30-day)":
    window = st.sidebar.slider("Rolling window (days):", min_value=5, max_value=60, value=30)
else:
    window = 30

# Normalize toggle for line chart
normalize = st.sidebar.checkbox("Normalize to 100 at start", value=False)

analyze_button = st.sidebar.button("🚀 Fetch Data & Analyze")

# ----- Main Logic -----
if analyze_button:
    if not tickers:
        st.warning("Please select at least one ticker.")
    else:
        prices = None
        data_source = ""
        
        # ---- Data Source 1: Kaggle ----
        if data_source_option == "Kaggle (S&P 500 2020-2025)" and KAGGLEHUB_AVAILABLE:
            with st.spinner("Downloading dataset from Kaggle... This may take a moment on the first run."):
                try:
                    # Download latest version of the S&P 500 dataset from Kaggle
                    dataset_path = kagglehub.dataset_download("jockeroika/stock-2025")
                    st.success(f"✅ Dataset downloaded to: {dataset_path}")
                    
                    # Load the CSV file
                    csv_file = os.path.join(dataset_path, "SP500_2020_2025.csv")
                    kaggle_df = pd.read_csv(csv_file)
                    
                    # Process the dataframe to match our format
                    kaggle_df['Date'] = pd.to_datetime(kaggle_df['Date'])
                    kaggle_df.set_index('Date', inplace=True)
                    
                    # Filter for selected tickers and date range
                    mask = (kaggle_df.index >= pd.to_datetime(start_date)) & (kaggle_df.index <= pd.to_datetime(end_date))
                    # Assuming the dataset uses 'Adj Close' for adjusted close prices
                    if 'Adj Close' in kaggle_df.columns:
                        prices = kaggle_df.loc[mask, ['Adj Close']]
                        prices.columns = ['AAPL'] # Placeholder, this needs proper mapping
                    else:
                        st.warning("Kaggle dataset format unexpected. Trying fallback...")
                        prices = None
                        
                    data_source = "Kaggle (S&P 500 2020-2025 dataset)"
                except Exception as e:
                    st.warning(f"Could not load Kaggle dataset: {e}. Falling back to local CSV.")
                    prices = None
        
        # ---- Data Source 2: Yahoo Finance ----
        elif data_source_option == "Yahoo Finance (Live)" and YFINANCE_AVAILABLE:
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
        
        # ---- Data Source 3: Local CSV (Fallback) ----
        if prices is None or prices.empty:
            st.info("⚠️ Switching to local sample data (offline mode).")
            fallback_df = load_fallback_data()
            if fallback_df is not None:
                mask = (fallback_df.index >= pd.to_datetime(start_date)) & (fallback_df.index <= pd.to_datetime(end_date))
                available_in_fallback = [t for t in tickers if t in fallback_df.columns]
                if available_in_fallback:
                    prices = fallback_df.loc[mask, available_in_fallback]
                else:
                    prices = pd.DataFrame()
                data_source = "Local sample data (CSV file)"
            else:
                st.error("Local fallback data file not found. Please ensure 'sample_stock_data.csv' is in the project folder.")
                prices = None
        
        # ---- Process and Display ----
        if prices is not None and not prices.empty:
            st.success(f"✅ Data loaded successfully from: {data_source}")
            
            # Calculate returns and volatility
            returns = prices.pct_change().dropna()
            cum_returns = (1 + returns).cumprod()
            rolling_vol = returns.rolling(window=window).std() * np.sqrt(252) * 100
            
            # Prepare data based on selected indicator
            if indicator == "Adjusted Close Price":
                plot_data = prices
                y_label = "Price (USD)"
            elif indicator == "Daily Returns (%)":
                plot_data = returns * 100
                y_label = "Daily Return (%)"
            elif indicator == "Cumulative Return (Base=1)":
                plot_data = cum_returns
                y_label = "Cumulative Return"
            else:  # Rolling Volatility
                plot_data = rolling_vol
                y_label = f"{window}-Day Rolling Volatility (Annualized %)"
            
            if normalize and indicator != "Daily Returns (%)":
                plot_data = plot_data / plot_data.iloc[0] * 100
                y_label = "Normalized Value (Base=100)"
            
            # Render selected chart type
            if chart_type == "Line Chart":
                fig = px.line(
                    plot_data,
                    title=f"{indicator} Over Time",
                    labels={"value": y_label, "index": "Date", "variable": "Ticker"}
                )
                fig.update_layout(legend_title_text='', hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Bar Chart (Latest Values)":
                latest_vals = plot_data.iloc[-1] if not plot_data.empty else pd.Series()
                fig = px.bar(
                    x=latest_vals.index,
                    y=latest_vals.values,
                    title=f"Latest {indicator} by Ticker",
                    labels={"x": "Ticker", "y": y_label},
                    color=latest_vals.index,
                    text_auto='.2f'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Correlation Heatmap":
                corr_matrix = returns.corr()
                fig = px.imshow(
                    corr_matrix,
                    text_auto=True,
                    aspect="auto",
                    title="Correlation Matrix of Daily Returns",
                    color_continuous_scale='RdBu_r',
                    zmin=-1, zmax=1
                )
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Portfolio Pie (Equal Weight)":
                weights = [1/len(tickers)] * len(tickers)
                fig = px.pie(
                    names=tickers,
                    values=weights,
                    title="Equal-Weight Portfolio Allocation (Illustrative)",
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            
            # Risk & Return Metrics Table (always show)
            st.subheader("📋 Risk & Return Summary Statistics")
            
            ann_factor = 252
            metrics_list = []
            for ticker in returns.columns:
                avg_return = returns[ticker].mean()
                vol = returns[ticker].std()
                ann_return = avg_return * ann_factor * 100
                ann_vol = vol * (ann_factor ** 0.5) * 100
                sharpe = (avg_return / vol) * (ann_factor ** 0.5) if vol != 0 else 0
                
                # Additional metrics
                total_return = (cum_returns[ticker].iloc[-1] - 1) * 100 if not cum_returns.empty else 0
                max_drawdown = (cum_returns[ticker] / cum_returns[ticker].cummax() - 1).min() * 100
                
                metrics_list.append({
                    "Ticker": ticker,
                    "Total Return (%)": round(total_return, 2),
                    "Annualized Return (%)": round(ann_return, 2),
                    "Annualized Volatility (%)": round(ann_vol, 2),
                    "Sharpe Ratio": round(sharpe, 2),
                    "Max Drawdown (%)": round(max_drawdown, 2)
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
            
            # Additional Stats: Summary Cards
            st.subheader("📊 Quick Stats")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                best_ticker = metrics_df.loc[metrics_df['Total Return (%)'].idxmax(), 'Ticker']
                best_return = metrics_df['Total Return (%)'].max()
                st.metric("🏆 Best Performer", best_ticker, f"{best_return:.2f}%")
            with col2:
                worst_ticker = metrics_df.loc[metrics_df['Total Return (%)'].idxmin(), 'Ticker']
                worst_return = metrics_df['Total Return (%)'].min()
                st.metric("📉 Worst Performer", worst_ticker, f"{worst_return:.2f}%")
            with col3:
                lowest_vol = metrics_df.loc[metrics_df['Annualized Volatility (%)'].idxmin(), 'Ticker']
                vol_val = metrics_df['Annualized Volatility (%)'].min()
                st.metric("🛡️ Lowest Volatility", lowest_vol, f"{vol_val:.2f}%")
            with col4:
                highest_sharpe = metrics_df.loc[metrics_df['Sharpe Ratio'].idxmax(), 'Ticker']
                sharpe_val = metrics_df['Sharpe Ratio'].max()
                st.metric("⚖️ Best Sharpe", highest_sharpe, f"{sharpe_val:.2f}")
            
            # Raw Data Expander
            with st.expander("🔍 Show raw price data (last 10 rows)"):
                st.dataframe(prices.tail(10))
            
            # Download CSV button
            csv = prices.to_csv()
            st.download_button(
                label="📥 Download price data as CSV",
                data=csv,
                file_name=f"stock_data_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
        else:
            st.error("No data could be loaded. Please check your network or the local CSV file.")
else:
    st.info("👈 Configure your analysis in the sidebar and click 'Fetch Data & Analyze' to begin.")
    
    # Show a preview image or placeholder
    st.markdown("""
    ### Welcome to the Advanced Stock Analysis Dashboard!
    
    **Features:**
    - 📈 Multiple chart types (Line, Bar, Heatmap, Pie)
    - 📊 Selectable indicators (Price, Returns, Cumulative Return, Volatility)
    - 🔥 Correlation analysis
    - 📋 Comprehensive risk/return metrics with color-coded table
    - 📥 Download data capability
    
    **Data Sources:**
    - `Kaggle (S&P 500 2020-2025)`: A comprehensive, static dataset of S&P 500 companies from 2020 to 2025.
    - `Yahoo Finance (Live)`: Fetches the most recent market data in real-time.
    - `Local CSV (Fallback)`: A minimal dataset to ensure the app runs offline.
    
    *Select tickers and date range, then click the button to start.*
    """)