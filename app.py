"""
Stock Risk & Return Dashboard - ACC102 Mini Assignment (Track 4)

This dashboard compares key risk and return metrics for selected stocks.
Data is loaded from a local CSV file (sample_stock_data.csv).

Author: [Your Name]
Date: April 2026
Version: 2.0.0
Project: ACC102 Mini Assignment - Track 4 (Interactive Data Analysis Tool)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Configure the Streamlit page
st.set_page_config(
    page_title="Stock Risk & Return Dashboard",
    layout="wide",
    page_icon="📊"
)

st.title("📊 Stock Risk & Return Dashboard")
st.markdown("Compare the risk and return characteristics of selected stocks.")
st.markdown("---")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

@st.cache_data
def load_sample_data() -> pd.DataFrame:
    """
    Load the sample stock price data from the local CSV file.
    """
    try:
        df = pd.read_csv("sample_stock_data.csv", index_col=0, parse_dates=True)
        df.columns = [col.upper() for col in df.columns]
        return df
    except FileNotFoundError:
        st.error("❌ sample_stock_data.csv not found. Please ensure the file is in the same directory as app.py.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()


def compute_metrics(adj_close: pd.DataFrame, risk_free_rate: float = 0.02) -> dict:
    """
    Compute risk and return metrics for each stock.
    """
    daily_returns = adj_close.pct_change().dropna(how='all')
    trading_days = len(adj_close)

    annual_return = (adj_close.iloc[-1] / adj_close.iloc[0]) ** (252 / trading_days) - 1
    annual_volatility = daily_returns.std() * np.sqrt(252)
    sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility

    def max_drawdown_func(price_series):
        cumulative_max = price_series.cummax()
        drawdown = (price_series - cumulative_max) / cumulative_max
        return drawdown.min()

    max_drawdown = adj_close.apply(max_drawdown_func)
    var_95 = daily_returns.quantile(0.05)
    cumulative_returns = (1 + daily_returns).cumprod()

    return {
        'daily_returns': daily_returns,
        'annual_return': annual_return,
        'annual_volatility': annual_volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'var_95': var_95,
        'cumulative_returns': cumulative_returns
    }


def style_summary_table(df: pd.DataFrame):
    """
    Apply conditional gradient formatting only to columns that actually exist.
    """
    styled = df.style

    def safe_background_gradient(styler, columns, cmap, low=0.2, high=0.8, reverse=False):
        existing_cols = [col for col in columns if col in df.columns]
        if existing_cols:
            cmap_actual = cmap + '_r' if reverse else cmap
            return styler.background_gradient(subset=existing_cols, cmap=cmap_actual, low=low, high=high)
        return styler

    high_good_cols = ["Annual Return (%)", "Sharpe Ratio"]
    styled = safe_background_gradient(styled, high_good_cols, cmap='RdYlGn', low=0.2, high=0.8)

    low_good_cols = ["Annual Volatility (%)", "Max Drawdown (%)", "VaR 95%"]
    styled = safe_background_gradient(styled, low_good_cols, cmap='RdYlGn', low=0.2, high=0.8, reverse=True)

    format_dict = {}
    if "Annual Return (%)" in df.columns:
        format_dict["Annual Return (%)"] = "{:.2f}%"
    if "Annual Volatility (%)" in df.columns:
        format_dict["Annual Volatility (%)"] = "{:.2f}%"
    if "Sharpe Ratio" in df.columns:
        format_dict["Sharpe Ratio"] = "{:.3f}"
    if "Max Drawdown (%)" in df.columns:
        format_dict["Max Drawdown (%)"] = "{:.2f}%"
    if "VaR 95%" in df.columns:
        format_dict["VaR 95%"] = "{:.2f}%"

    if format_dict:
        styled = styled.format(format_dict)

    return styled


def create_cumulative_returns_chart(cumulative_returns: pd.DataFrame) -> go.Figure:
    """
    Create a line chart showing cumulative returns over time.
    """
    fig = go.Figure()
    for ticker in cumulative_returns.columns:
        fig.add_trace(go.Scatter(
            x=cumulative_returns.index,
            y=cumulative_returns[ticker],
            name=ticker,
            mode='lines',
            line=dict(width=2.5)
        ))

    fig.add_hline(y=1, line_dash='dot', line_color='gray', opacity=0.5)

    fig.update_layout(
        title=dict(text="Cumulative Returns (Rebased to 1)", font=dict(size=18)),
        xaxis_title="Date",
        yaxis_title="Cumulative Return",
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', tickformat=".2f")
    return fig


def create_scatter_plot(annual_returns: pd.Series, annual_vol: pd.Series, sharpe: pd.Series) -> go.Figure:
    """
    Create a risk-return scatter plot (bubble chart).
    X-axis: Annual Volatility (risk), Y-axis: Annual Return, Bubble size: Sharpe Ratio.
    """
    # Convert to percent for display
    returns_pct = annual_returns.values
    vols_pct = annual_vol.values
    sharpe_vals = sharpe.values
    tickers = annual_returns.index.tolist()

    # Scale bubble size (Sharpe can be negative, so shift to positive or use absolute)
    # Use a min size for better visibility
    sizes = np.maximum(sharpe_vals + 2.5, 5)  # ensure positive size, scaled

    fig = px.scatter(
        x=vols_pct,
        y=returns_pct,
        text=tickers,
        size=sizes,
        size_max=25,
        color=sharpe_vals,
        color_continuous_scale='RdYlGn',
        labels={
            'x': 'Annualized Volatility (%)',
            'y': 'Annualized Return (%)',
            'color': 'Sharpe Ratio'
        },
        title="Risk vs. Return (Bubble Size = Sharpe Ratio)"
    )

    fig.update_traces(
        textposition='top center',
        marker=dict(line=dict(width=1, color='DarkSlateGrey'))
    )

    fig.update_layout(
        height=500,
        xaxis_title="Annualized Volatility (%) (Risk)",
        yaxis_title="Annualized Return (%)",
        hovermode='closest',
        margin=dict(l=20, r=20, t=50, b=20)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')

    return fig


def create_radar_chart(adj_close: pd.DataFrame) -> go.Figure:
    """
    Create an interactive radar (spider) chart comparing multiple metrics.
    """
    metrics = compute_metrics(adj_close)
    tickers = adj_close.columns.tolist()

    metric_vars = {
        'Return': {'series': metrics['annual_return'], 'higher_better': True},
        'Volatility': {'series': metrics['annual_volatility'], 'higher_better': False},
        'Sharpe': {'series': metrics['sharpe_ratio'], 'higher_better': True},
        'Drawdown': {'series': metrics['max_drawdown'], 'higher_better': False},
        'VaR': {'series': metrics['var_95'], 'higher_better': False}
    }

    normalized_df = pd.DataFrame(index=tickers)
    for name, info in metric_vars.items():
        values = info['series'].fillna(0)
        min_val = values.min()
        max_val = values.max()

        if max_val == min_val:
            normalized = pd.Series(50, index=values.index)
        else:
            if info['higher_better']:
                normalized = (values - min_val) / (max_val - min_val) * 100
            else:
                normalized = (max_val - values) / (max_val - min_val) * 100

        normalized_df[name] = normalized

    categories = list(metric_vars.keys())
    categories_closed = categories + [categories[0]]

    fig = go.Figure()
    colors = px.colors.qualitative.Plotly
    for i, ticker in enumerate(tickers):
        values = normalized_df.loc[ticker].tolist()
        values_closed = values + [values[0]]

        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            name=ticker,
            fill='toself',
            line=dict(color=colors[i % len(colors)], width=2)
        ))

    fig.update_layout(
        title=dict(text="Radar Chart — Normalized Metric Comparison", font=dict(size=18)),
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[0, 25, 50, 75, 100],
                ticktext=['0', '25', '50', '75', '100']
            )
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=550,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def create_correlation_heatmap(daily_returns: pd.DataFrame) -> go.Figure:
    """
    Create a correlation heatmap for stock returns.
    """
    corr_matrix = daily_returns.corr().round(3)

    fig = px.imshow(
        corr_matrix,
        text_auto=True,
        color_continuous_scale='RdBu_r',
        zmin=-1,
        zmax=1,
        aspect="auto"
    )

    fig.update_layout(
        title=dict(text="Return Correlation Matrix", font=dict(size=16)),
        height=500,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def create_returns_histogram(daily_returns: pd.DataFrame,
                             selected_ticker: str) -> go.Figure:
    """
    Create a histogram of daily returns for a selected stock.
    """
    returns_series = daily_returns[selected_ticker].dropna()
    if returns_series.empty:
        return None

    fig = px.histogram(
        returns_series,
        nbins=50,
        title=f"Daily Return Distribution — {selected_ticker}",
        labels={'value': 'Daily Return', 'count': 'Frequency'},
        opacity=0.7,
        color_discrete_sequence=['#1f77b4']
    )

    mean = returns_series.mean()
    std = returns_series.std()
    x = np.linspace(mean - 3.5*std, mean + 3.5*std, 100)
    y = np.exp(-0.5 * ((x - mean)/std)**2) / (std * np.sqrt(2*np.pi))
    bin_width = (returns_series.max() - returns_series.min()) / 50
    y_scaled = y * len(returns_series) * bin_width

    fig.add_trace(go.Scatter(
        x=x,
        y=y_scaled,
        mode='lines',
        name='Normal Reference',
        line=dict(color='red', width=2, dash='dash')
    ))

    fig.update_layout(
        height=500,
        showlegend=True,
        yaxis_title="Frequency",
        xaxis_title="Daily Return",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


# =============================================================================
# SIDEBAR CONFIGURATION (Left Panel)
# =============================================================================

st.sidebar.header("⚙️ Configuration")

# ---- Stock Ticker Selection ------------------------------------------------
st.sidebar.subheader("📈 Stock Selection")
default_tickers = "AAPL, MSFT, GOOGL, AMZN, TSLA, JPM"
ticker_input = st.sidebar.text_input(
    "Stock Tickers (comma-separated)",
    value=default_tickers,
    help="Example: AAPL, MSFT, GOOGL"
)
tickers = [t.strip().upper() for t in ticker_input.split(',') if t.strip()]
if tickers:
    st.sidebar.info(f"Selected: {', '.join(tickers)}")

# ---- Date Range Selection --------------------------------------------------
st.sidebar.subheader("📅 Date Range")
default_start = datetime(2020, 1, 1)
default_end = datetime(2024, 12, 31)
start_date = st.sidebar.date_input("Start Date", value=default_start)
end_date = st.sidebar.date_input("End Date", value=default_end)
if start_date >= end_date:
    st.sidebar.error("Start date must be before end date.")

# ---- Indicator Selection (for Summary Table) -------------------------------
st.sidebar.subheader("📋 Indicators")
indicator_options = [
    "Annual Return (%)",
    "Annual Volatility (%)",
    "Sharpe Ratio",
    "Max Drawdown (%)",
    "VaR 95%"
]
selected_indicators = st.sidebar.multiselect(
    "Select indicators to display:",
    options=indicator_options,
    default=["Annual Return (%)", "Annual Volatility (%)", "Sharpe Ratio"]
)

# ---- Chart Type Selection --------------------------------------------------
st.sidebar.subheader("📊 Chart Visibility")
show_line_chart = st.sidebar.checkbox("Cumulative Returns Line Chart", value=True)
show_table = st.sidebar.checkbox("Risk & Return Summary Table", value=True)
show_scatter = st.sidebar.checkbox("Risk-Return Scatter Plot", value=True)   # <-- NEW
show_radar = st.sidebar.checkbox("Radar Chart", value=True)
show_histogram = st.sidebar.checkbox("Daily Return Histogram", value=True)
show_heatmap = st.sidebar.checkbox("Correlation Heatmap", value=True)

# ---- Risk-Free Rate Adjustment ---------------------------------------------
st.sidebar.subheader("📈 Parameters")
risk_free_rate_pct = st.sidebar.slider(
    "Risk-Free Rate (%)",
    min_value=0.0,
    max_value=10.0,
    value=2.0,
    step=0.5
)
risk_free_rate = risk_free_rate_pct / 100

# ---- Run Button ------------------------------------------------------------
run_analysis = st.sidebar.button("🚀 Run Analysis", type="primary", use_container_width=True)

# =============================================================================
# LOAD DATA (Always from local sample_stock_data.csv)
# =============================================================================
raw_data = load_sample_data()

# =============================================================================
# MAIN CONTENT AREA (Right Panel)
# =============================================================================

if run_analysis:
    # Filter data by date range
    adj_close = raw_data.loc[(raw_data.index >= pd.Timestamp(start_date)) &
                             (raw_data.index <= pd.Timestamp(end_date))]

    available_tickers = [t for t in tickers if t in adj_close.columns]
    if not available_tickers:
        st.error(f"None of the requested tickers {tickers} found in the data.")
        st.stop()
    adj_close = adj_close[available_tickers]

    # Compute metrics
    with st.spinner("⏳ Computing risk and return metrics..."):
        metrics_data = compute_metrics(adj_close, risk_free_rate)

    daily_returns = metrics_data['daily_returns']
    annual_return = metrics_data['annual_return'] * 100
    annual_volatility = metrics_data['annual_volatility'] * 100
    sharpe_ratio = metrics_data['sharpe_ratio']
    max_drawdown = metrics_data['max_drawdown'] * 100
    var_95 = metrics_data['var_95'] * 100
    cumulative_returns = metrics_data['cumulative_returns']

    # Build Summary Table
    indicator_map = {
        "Annual Return (%)": annual_return,
        "Annual Volatility (%)": annual_volatility,
        "Sharpe Ratio": sharpe_ratio,
        "Max Drawdown (%)": max_drawdown,
        "VaR 95%": var_95
    }
    summary_data = {ind: indicator_map[ind] for ind in selected_indicators}
    if summary_data:
        summary_df = pd.DataFrame(summary_data).round(4)
        if "Annual Return (%)" in summary_df.columns:
            summary_df = summary_df.sort_values("Annual Return (%)", ascending=False)
    else:
        summary_df = None

    # =========================================================================
    # DISPLAY CHARTS
    # =========================================================================
    st.markdown("## 📊 Analysis Results")

    # ---- Cumulative Returns Line Chart ----
    if show_line_chart:
        with st.container():
            st.markdown("### 📈 Cumulative Returns")
            fig_line = create_cumulative_returns_chart(cumulative_returns)
            st.plotly_chart(fig_line, use_container_width=True)
            st.markdown("---")

    # ---- Risk & Return Summary Table with Color ----
    if show_table and summary_df is not None:
        with st.container():
            st.markdown("### 📋 Risk & Return Summary")
            styled_table = style_summary_table(summary_df)
            st.dataframe(
                styled_table,
                use_container_width=True
            )
            st.markdown("---")

    # ---- NEW: Risk-Return Scatter Plot ----
    if show_scatter and len(available_tickers) >= 1:
        with st.container():
            st.markdown("### 🫧 Risk-Return Scatter Plot")
            fig_scatter = create_scatter_plot(annual_return, annual_volatility, sharpe_ratio)
            st.plotly_chart(fig_scatter, use_container_width=True)
            st.markdown("*Each point represents a stock. Bubble size reflects the Sharpe Ratio.*")
            st.markdown("---")

    # ---- Radar Chart ----
    if show_radar and len(available_tickers) >= 1:
        with st.container():
            st.markdown("### 🕸️ Radar Chart — Metric Comparison")
            fig_radar = create_radar_chart(adj_close)
            st.plotly_chart(fig_radar, use_container_width=True)
            st.markdown("*Radar chart values are normalized to 0–100. Higher is better; for volatility, drawdown, and VaR, the scale is inverted.*")
            st.markdown("---")

    # ---- Side-by-side: Histogram + Correlation Heatmap ----
    if show_histogram or show_heatmap:
        col_left, col_right = st.columns(2, gap="medium")

        with col_left:
            if show_histogram and len(available_tickers) >= 1:
                st.markdown("### 📊 Daily Return Distribution")
                selected_ticker_hist = st.selectbox(
                    "Select ticker for histogram:",
                    options=available_tickers,
                    key="hist_ticker"
                )
                fig_hist = create_returns_histogram(daily_returns, selected_ticker_hist)
                if fig_hist:
                    st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.empty()

        with col_right:
            if show_heatmap and len(available_tickers) >= 2:
                st.markdown("### 🔥 Correlation Heatmap")
                fig_heatmap = create_correlation_heatmap(daily_returns)
                st.plotly_chart(fig_heatmap, use_container_width=True)
                st.markdown("*A value of 1 means perfect positive correlation; -1 means perfect negative correlation.*")
            else:
                st.empty()

    # If all charts are hidden
    if not any([show_line_chart, show_table, show_scatter, show_radar, show_histogram, show_heatmap]):
        st.info("All charts are currently hidden. Please tick the checkboxes in the sidebar to display them.")

else:
    st.info("👈 Configure the parameters in the left sidebar and click **Run Analysis** to begin.")
    st.markdown("""
    ### 📌 How to Use This Dashboard

    1. **Select stock tickers** (e.g., AAPL, MSFT, GOOGL).
    2. **Set the date range** for analysis.
    3. **Choose which indicators** to display in the summary table.
    4. **Toggle charts** on/off as needed.
    5. Click **Run Analysis** to generate the dashboard.

    The app computes the following metrics for each selected stock:
    - Annualized return and volatility
    - Sharpe ratio (risk-adjusted return)
    - Maximum drawdown
    - Value at Risk (95%)

    **Data source**: The dashboard uses the local file `sample_stock_data.csv`.
    """)