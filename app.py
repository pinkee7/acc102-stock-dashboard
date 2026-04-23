"""
ACC102 Track 4 - Advanced Interactive Stock Analysis Tool
Author: [Your Name]
Date: April 2026
Description: Stock analysis dashboard with WRDS (CRSP) as primary data source
             and local CSV as offline fallback. No Yahoo Finance dependency.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime
import os

# ----- Try to import WRDS -----
try:
    import wrds
    WRDS_AVAILABLE = True
except ImportError:
    WRDS_AVAILABLE = False

# ----- Page Config -----
st.set_page_config(page_title="Advanced Stock Analyzer", layout="wide")
st.title("📊 Advanced Stock Analysis Dashboard (WRDS + CSV)")
st.markdown("Multi-view analysis tool with comprehensive CRSP data via WRDS, plus local CSV fallback.")

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
@st.cache_data(ttl=3600)
def get_sp500_tickers_from_wrds(_conn):
    """Fetch S&P 500 constituents from CRSP via WRDS."""
    try:
        query = """
        SELECT DISTINCT a.permno, a.ticker, a.comnam
        FROM crsp.dsp500list_v2 AS sp500
        JOIN crsp.stocknames AS a
        ON sp500.permno = a.permno
        WHERE sp500.mbrenddt >= '2023-01-01'
        AND a.ticker IS NOT NULL
        AND a.ticker != ''
        ORDER BY a.ticker
        """
        df = _conn.raw_sql(query)
        return df, None
    except Exception as e:
        return None, f"WRDS query failed: {e}"

@st.cache_data(ttl=3600)
def get_stock_data_from_wrds(_conn, tickers, start_date, end_date):
    """Fetch daily stock prices from CRSP via WRDS."""
    if not tickers:
        return None
    
    ticker_str = "', '".join(tickers)
    
    query = f"""
    SELECT a.ticker, b.date, b.prc
    FROM crsp.stocknames AS a
    JOIN crsp.dsf AS b ON a.permno = b.permno
    WHERE a.ticker IN ('{ticker_str}')
    AND b.date >= '{start_date}'
    AND b.date <= '{end_date}'
    AND b.prc > 0
    ORDER BY a.ticker, b.date
    """
    
    try:
        df = _conn.raw_sql(query)
        if df.empty:
            return None
        df['prc'] = df['prc'].abs()
        prices = df.pivot(index='date', columns='ticker', values='prc')
        return prices
    except Exception as e:
        st.error(f"WRDS data fetch error: {e}")
        return None

@st.cache_data(ttl=3600)
def search_ticker_from_wrds(_conn, search_term):
    """Search for tickers by company name or ticker symbol."""
    search_term = search_term.upper()
    query = f"""
    SELECT DISTINCT ticker, comnam
    FROM crsp.stocknames
    WHERE UPPER(ticker) LIKE '%{search_term}%'
    OR UPPER(comnam) LIKE '%{search_term}%'
    LIMIT 100
    """
    try:
        df = _conn.raw_sql(query)
        return df
    except:
        return pd.DataFrame()

# ----- Session State Initialization -----
if 'wrds_conn' not in st.session_state:
    st.session_state['wrds_conn'] = None
if 'wrds_tickers' not in st.session_state:
    st.session_state['wrds_tickers'] = None
if 'ticker_options' not in st.session_state:
    st.session_state['ticker_options'] = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "JPM", "NVDA", "META"]

# ----- Sidebar Controls -----
st.sidebar.header("🎮 Data Source & Connection")

# Data source selection
data_source = st.sidebar.selectbox(
    "Select data source:",
    options=["WRDS (CRSP)", "Local CSV (Offline)"],
    index=0 if WRDS_AVAILABLE else 1
)

# WRDS Connection Panel
if data_source == "WRDS (CRSP)":
    if WRDS_AVAILABLE:
        st.sidebar.subheader("WRDS Connection")
        wrds_username = st.sidebar.text_input("Username")
        wrds_password = st.sidebar.text_input("Password", type="password")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🔗 Connect", use_container_width=True):
                if wrds_username and wrds_password:
                    with st.spinner("Connecting to WRDS..."):
                        try:
                            conn = wrds.Connection(wrds_username=wrds_username, wrds_password=wrds_password)
                            st.session_state['wrds_conn'] = conn
                            
                            # Fetch ticker list
                            ticker_df, error = get_sp500_tickers_from_wrds(conn)
                            if error:
                                st.sidebar.error(error)
                            else:
                                st.session_state['wrds_tickers'] = ticker_df
                                st.session_state['ticker_options'] = ticker_df['ticker'].tolist()
                                st.sidebar.success(f"✅ Connected! {len(ticker_df)} tickers loaded.")
                        except Exception as e:
                            st.sidebar.error(f"Connection failed: {e}")
                else:
                    st.sidebar.warning("Enter username and password.")
        
        with col2:
            if st.button("🔌 Disconnect", use_container_width=True):
                if st.session_state['wrds_conn']:
                    try:
                        st.session_state['wrds_conn'].close()
                    except:
                        pass
                st.session_state['wrds_conn'] = None
                st.session_state['wrds_tickers'] = None
                st.session_state['ticker_options'] = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "JPM", "NVDA", "META"]
                st.sidebar.info("Disconnected from WRDS.")
    else:
        st.sidebar.warning("⚠️ WRDS package not installed. Run: pip install wrds")
        st.sidebar.info("Using Local CSV mode.")

# Ticker Selection
st.sidebar.subheader("📋 Stock Selection")

if data_source == "WRDS (CRSP)" and st.session_state['wrds_conn'] is not None:
    # Search bar for tickers
    search_term = st.sidebar.text_input("🔍 Search ticker/company", placeholder="e.g., AAPL or Apple")
    if search_term:
        search_results = search_ticker_from_wrds(st.session_state['wrds_conn'], search_term)
        if not search_results.empty:
            st.sidebar.caption(f"Found {len(search_results)} results")
    
    # Input mode selection
    input_mode = st.sidebar.radio("Input mode:", ["Select from list", "Manual entry"])
    
    if input_mode == "Select from list":
        tickers = st.sidebar.multiselect(
            "Select tickers:",
            options=st.session_state['ticker_options'],
            default=["AAPL", "MSFT", "GOOGL", "NVDA"]
        )
    else:
        ticker_input = st.sidebar.text_input(
            "Enter tickers (comma-separated):",
            value="AAPL, MSFT, GOOGL, NVDA"
        )
        tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
else:
    # CSV mode - fixed 8 tickers
    tickers = st.sidebar.multiselect(
        "Select tickers:",
        options=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "JPM", "NVDA", "META"],
        default=["AAPL", "MSFT", "GOOGL", "NVDA"]
    )

# Date Range
st.sidebar.subheader("📅 Date Range")
start_date = st.sidebar.date_input("Start date", value=pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End date", value=datetime.today())

# Chart Options
st.sidebar.subheader("📈 Chart Options")
indicator = st.sidebar.selectbox(
    "Select indicator:",
    options=["Price", "Daily Returns (%)", "Cumulative Return", "Rolling Volatility"],
    index=2
)

chart_type = st.sidebar.selectbox(
    "Select chart type:",
    options=["Line Chart", "Bar Chart (Latest)", "Correlation Heatmap", "Risk-Return Scatter"],
    index=0
)

normalize = st.sidebar.checkbox("Normalize to 100 at start", value=False)
if indicator == "Rolling Volatility":
    window = st.sidebar.slider("Rolling window (days):", 5, 90, 30)
else:
    window = 30

analyze_button = st.sidebar.button("🚀 Fetch & Analyze", type="primary", use_container_width=True)

# ----- Main Logic -----
if analyze_button:
    if not tickers:
        st.warning("⚠️ Please select at least one ticker.")
    else:
        prices = None
        data_source_used = ""
        
        with st.spinner("Fetching data..."):
            # ---- WRDS Mode ----
            if data_source == "WRDS (CRSP)" and st.session_state['wrds_conn'] is not None:
                try:
                    prices = get_stock_data_from_wrds(
                        st.session_state['wrds_conn'],
                        tickers,
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d')
                    )
                    if prices is not None and not prices.empty:
                        data_source_used = f"WRDS CRSP ({len(prices)} trading days)"
                except Exception as e:
                    st.warning(f"WRDS fetch failed: {e}. Falling back to CSV...")
                    prices = None
            
            # ---- Fallback to CSV ----
            if prices is None or prices.empty:
                fallback_df = load_fallback_data()
                if fallback_df is not None:
                    mask = (fallback_df.index >= pd.to_datetime(start_date)) & \
                           (fallback_df.index <= pd.to_datetime(end_date))
                    available_tickers = [t for t in tickers if t in fallback_df.columns]
                    if available_tickers:
                        prices = fallback_df.loc[mask, available_tickers]
                        data_source_used = f"Local CSV ({len(prices)} trading days)"
                    else:
                        st.error(f"None of the selected tickers {tickers} found in CSV file.")
                        prices = None
        
        # ---- Process and Display ----
        if prices is not None and not prices.empty:
            st.success(f"✅ Data loaded: {data_source_used} | {len(tickers)} stocks")
            
            # Calculate metrics
            returns = prices.pct_change().dropna()
            cum_returns = (1 + returns).cumprod()
            rolling_vol = returns.rolling(window=window).std() * np.sqrt(252) * 100
            
            # Prepare plot data
            if indicator == "Price":
                plot_data = prices
                y_label = "Price (USD)"
            elif indicator == "Daily Returns (%)":
                plot_data = returns * 100
                y_label = "Daily Return (%)"
            elif indicator == "Cumulative Return":
                plot_data = cum_returns
                y_label = "Cumulative Return"
            else:
                plot_data = rolling_vol
                y_label = f"{window}-Day Rolling Volatility (Ann. %)"
            
            if normalize and indicator != "Daily Returns (%)":
                plot_data = plot_data / plot_data.iloc[0] * 100
                y_label = "Normalized Value"
            
            # Render Chart
            if chart_type == "Line Chart":
                fig = px.line(plot_data, title=f"{indicator} Over Time",
                             labels={"value": y_label, "index": "Date", "variable": "Ticker"})
                fig.update_layout(legend_title_text='', hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Bar Chart (Latest)":
                latest = plot_data.iloc[-1]
                fig = px.bar(x=latest.index, y=latest.values,
                            title=f"Latest {indicator} by Ticker",
                            labels={"x": "Ticker", "y": y_label},
                            color=latest.index, text_auto='.2f')
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Correlation Heatmap":
                corr = returns.corr()
                fig = px.imshow(corr, text_auto='.2f', aspect="auto",
                               title="Correlation Matrix of Daily Returns",
                               color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "Risk-Return Scatter":
                ann = 252
                scatter_data = []
                for t in returns.columns:
                    avg = returns[t].mean() * ann * 100
                    vol = returns[t].std() * np.sqrt(ann) * 100
                    sharpe = avg / vol if vol != 0 else 0
                    scatter_data.append({"Ticker": t, "Return (%)": avg, "Volatility (%)": vol, "Sharpe": sharpe})
                scatter_df = pd.DataFrame(scatter_data)
                fig = px.scatter(scatter_df, x="Volatility (%)", y="Return (%)", text="Ticker",
                                title="Risk-Return Profile", color="Sharpe",
                                color_continuous_scale="RdYlGn")
                fig.update_traces(textposition='top center', marker=dict(size=12))
                st.plotly_chart(fig, use_container_width=True)
            
            # Summary Table
            st.subheader("📋 Risk & Return Summary")
            ann = 252
            metrics = []
            for t in returns.columns:
                avg = returns[t].mean()
                vol = returns[t].std()
                ann_ret = avg * ann * 100
                ann_vol = vol * np.sqrt(ann) * 100
                sharpe = (avg / vol) * np.sqrt(ann) if vol != 0 else 0
                total_ret = (cum_returns[t].iloc[-1] - 1) * 100
                max_dd = (cum_returns[t] / cum_returns[t].cummax() - 1).min() * 100
                metrics.append({
                    "Ticker": t,
                    "Total Return (%)": round(total_ret, 2),
                    "Ann. Return (%)": round(ann_ret, 2),
                    "Ann. Volatility (%)": round(ann_vol, 2),
                    "Sharpe": round(sharpe, 2),
                    "Max DD (%)": round(max_dd, 2)
                })
            
            metrics_df = pd.DataFrame(metrics)
            st.dataframe(
                metrics_df.style.format({
                    "Total Return (%)": "{:.2f}",
                    "Ann. Return (%)": "{:.2f}",
                    "Ann. Volatility (%)": "{:.2f}",
                    "Sharpe": "{:.2f}",
                    "Max DD (%)": "{:.2f}"
                }).background_gradient(cmap='RdYlGn', subset=['Total Return (%)', 'Sharpe'])
                .background_gradient(cmap='RdYlGn_r', subset=['Ann. Volatility (%)', 'Max DD (%)']),
                use_container_width=True
            )
            
            # Quick Stats Cards
            st.subheader("📊 Quick Stats")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                best = metrics_df.loc[metrics_df['Total Return (%)'].idxmax()]
                st.metric("🏆 Best", best['Ticker'], f"{best['Total Return (%)']:.2f}%")
            with c2:
                worst = metrics_df.loc[metrics_df['Total Return (%)'].idxmin()]
                st.metric("📉 Worst", worst['Ticker'], f"{worst['Total Return (%)']:.2f}%")
            with c3:
                low_vol = metrics_df.loc[metrics_df['Ann. Volatility (%)'].idxmin()]
                st.metric("🛡️ Lowest Vol", low_vol['Ticker'], f"{low_vol['Ann. Volatility (%)']:.2f}%")
            with c4:
                best_sharpe = metrics_df.loc[metrics_df['Sharpe'].idxmax()]
                st.metric("⚖️ Best Sharpe", best_sharpe['Ticker'], f"{best_sharpe['Sharpe']:.2f}")
            
            # Raw Data & Download
            with st.expander("🔍 View raw price data (last 10 rows)"):
                st.dataframe(prices.tail(10))
            
            st.download_button("📥 Download CSV", prices.to_csv(),
                              f"stock_data_{start_date}_{end_date}.csv", "text/csv")
        else:
            st.error("❌ No data loaded. Check tickers, date range, or WRDS connection.")
else:
    st.info("👈 Configure data source and click 'Fetch & Analyze' to begin.")
    
    st.markdown("""
    ### 📌 Welcome to the Stock Analysis Dashboard
    
    **Data Sources:**
    - **WRDS (CRSP)**: Comprehensive historical data for all US stocks (requires XJTLU WRDS credentials)
    - **Local CSV**: Offline fallback using pre-loaded sample data
    
    **Features:**
    - 📈 Multiple chart types (Line, Bar, Heatmap, Risk-Return Scatter)
    - 📊 Selectable indicators (Price, Returns, Cumulative Return, Volatility)
    - 📋 Comprehensive risk metrics table with color coding
    - 📥 Data download capability
    """)