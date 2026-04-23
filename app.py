"""
ACC102 Track 4 - Interactive Stock Analysis Tool (Local Data Version)
Author: [Your Name]
Date: April 2026
Description: Multi-view stock analysis dashboard using local CSV sample data.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime
import os

# ----- Page Config -----
st.set_page_config(page_title="Stock Analysis Dashboard", layout="wide")
st.title("📊 Stock Analysis Dashboard")
st.markdown("Interactive multi-view analysis of US tech stocks using sample historical data.")

# ----- Helper function to load local data -----
@st.cache_data
def load_data():
    """Load sample stock data from local CSV file."""
    file_path = os.path.join(os.path.dirname(__file__), "sample_stock_data.csv")
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        # Force first column to be datetime index
        df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
        df.set_index(df.columns[0], inplace=True)
        df.index.name = 'Date'
        return df
    else:
        st.error("Sample data file 'sample_stock_data.csv' not found in project folder.")
        return None

# ----- Sidebar Controls -----
st.sidebar.header("🎮 User Controls")

# Stock selection (from available columns in data)
data = load_data()
if data is not None:
    available_tickers = list(data.columns)
else:
    available_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "JPM", "NVDA", "META"]

tickers = st.sidebar.multiselect(
    "Select stock tickers:",
    options=available_tickers,
    default=available_tickers[:4] if len(available_tickers) >= 4 else available_tickers
)

# Date range
if data is not None:
    min_date = data.index.min().date()
    max_date = data.index.max().date()
else:
    min_date = pd.to_datetime("2024-01-01").date()
    max_date = datetime.today().date()

start_date = st.sidebar.date_input("Start date", value=min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End date", value=max_date, min_value=min_date, max_value=max_date)

# Indicator selection
st.sidebar.subheader("📈 Chart Options")
indicator = st.sidebar.selectbox(
    "Select indicator:",
    options=["Adjusted Close Price", "Daily Returns (%)", "Cumulative Return (Base=1)", "Rolling Volatility (30-day)"],
    index=2
)

# Chart type selection
chart_type = st.sidebar.selectbox(
    "Select chart type:",
    options=["Line Chart", "Bar Chart (Latest Values)", "Correlation Heatmap", "Portfolio Pie"],
    index=0
)

# Rolling window for volatility
if indicator == "Rolling Volatility (30-day)":
    window = st.sidebar.slider("Rolling window (days):", min_value=5, max_value=60, value=30)
else:
    window = 30

# Normalize toggle
normalize = st.sidebar.checkbox("Normalize to 100 at start", value=False)

analyze_button = st.sidebar.button("🚀 Analyze")

# ----- Main Logic -----
if analyze_button:
    if not tickers:
        st.warning("Please select at least one ticker.")
    else:
        prices = None
        
        if data is not None:
            # Filter by date and selected tickers
            mask = (data.index >= pd.to_datetime(start_date)) & (data.index <= pd.to_datetime(end_date))
            available = [t for t in tickers if t in data.columns]
            if available:
                prices = data.loc[mask, available]
            else:
                st.error("Selected tickers not found in data.")
        else:
            st.error("Data file not loaded.")
        
        if prices is not None and not prices.empty:
            st.success("✅ Data loaded successfully from local sample file.")
            
            # Calculate returns and volatility
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
            
            # Render chart
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
            
            elif chart_type == "Portfolio Pie":
                weights = [1/len(tickers)] * len(tickers)
                fig = px.pie(
                    names=tickers,
                    values=weights,
                    title="Equal-Weight Portfolio Allocation (Illustrative)",
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            
            # Risk & Return Metrics Table
            st.subheader("📋 Risk & Return Summary")
            ann_factor = 252
            metrics_list = []
            for ticker in returns.columns:
                avg_return = returns[ticker].mean()
                vol = returns[ticker].std()
                ann_return = avg_return * ann_factor * 100
                ann_vol = vol * (ann_factor ** 0.5) * 100
                sharpe = (avg_return / vol) * (ann_factor ** 0.5) if vol != 0 else 0
                total_return = (cum_returns[ticker].iloc[-1] - 1) * 100
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
            
            # Quick Stats Cards
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
            
            # Raw data expander
            with st.expander("🔍 Show raw price data (last 10 rows)"):
                st.dataframe(prices.tail(10))
            
            # Download button
            csv = prices.to_csv()
            st.download_button(
                label="📥 Download data as CSV",
                data=csv,
                file_name=f"stock_data_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
        else:
            st.error("No data available for the selected date range or tickers.")
else:
    st.info("👈 Select tickers and date range, then click 'Analyze' to begin.")
    st.markdown("""
    ### Welcome to the Stock Analysis Dashboard!
    
    **Features:**
    - 📈 Multiple chart types (Line, Bar, Heatmap, Pie)
    - 📊 Selectable indicators (Price, Returns, Cumulative Return, Volatility)
    - 🔥 Correlation analysis
    - 📋 Comprehensive risk/return metrics with color-coded table
    - 📥 Download data capability
    
    *Data source: local sample file (`sample_stock_data.csv`).*
    """)