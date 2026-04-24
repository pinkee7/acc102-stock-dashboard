"""
Stock Risk & Return Dashboard - ACC102 Mini Assignment (Track 4)

This dashboard compares key risk and return metrics for selected stocks.
Data is loaded from a local CSV file (sample_stock_data.csv).
Stock selection is done via a dropdown multiselect, populated from the CSV file.
All tables are rendered as raw HTML to avoid Pandas Styler compatibility issues.

Author: [Your Name]
Date: April 2026
Version: 4.0.0 (Pure HTML table rendering)
Project: ACC102 Mini Assignment - Track 4 (Interactive Data Analysis Tool)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Stock Risk & Return Dashboard",
    layout="wide",
    page_icon="📊"
)

st.title("📊 Stock Risk & Return Dashboard")
st.markdown("Compare the risk and return characteristics of selected stocks.")
st.markdown("---")


# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

@st.cache_data
def load_sample_data() -> pd.DataFrame:
    """Load the sample stock price data from the local CSV file."""
    try:
        df = pd.read_csv("sample_stock_data.csv", index_col=0, parse_dates=True)
        df.columns = [col.upper() for col in df.columns]
        return df
    except FileNotFoundError:
        st.error("❌ sample_stock_data.csv not found. Place it in the same folder as app.py.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()


def compute_metrics(adj_close: pd.DataFrame, risk_free_rate: float = 0.02) -> dict:
    """Compute risk and return metrics for each stock."""
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


def build_html_colored_table(df: pd.DataFrame, metric_directions: dict) -> str:
    """
    Build a pure HTML table with red-to-green gradient backgrounds.
    `metric_directions`: keys = column names, values = 'higher_better' or 'lower_better'.
    """
    # Helper: map value to RGBA color using percentile within the column
    def color_for(value, col_name, min_val, max_val, direction):
        if pd.isna(value) or max_val == min_val:
            return "#f0f0f0"  # neutral grey
        # Normalize to 0-1
        ratio = (value - min_val) / (max_val - min_val)
        if direction == 'lower_better':
            ratio = 1 - ratio  # invert
        # Red (bad) at 0, Yellow at 0.5, Green (good) at 1
        if ratio < 0.5:
            # red to yellow: (255, 0, 0) -> (255, 255, 0)
            r = 255
            g = int(255 * (ratio * 2))
            b = 0
        else:
            # yellow to green: (255, 255, 0) -> (0, 255, 0)
            r = int(255 * (1 - (ratio - 0.5) * 2))
            g = 255
            b = 0
        return f"rgba({r}, {g}, {b}, 0.6)"

    # Format cell values
    def format_value(col_name, val):
        if pd.isna(val):
            return "N/A"
        if "Return" in col_name or "Volatility" in col_name or "Drawdown" in col_name or "VaR" in col_name:
            return f"{val:.2f}%"
        elif "Sharpe" in col_name:
            return f"{val:.3f}"
        return f"{val:.4f}"

    # Compute min/max for each column
    col_mins = {}
    col_maxs = {}
    for col in df.columns:
        col_mins[col] = df[col].min()
        col_maxs[col] = df[col].max()

    # Build HTML
    html = '<div style="overflow-x:auto;"><table style="border-collapse:collapse; width:100%;">'

    # Header
    html += '<thead><tr><th style="padding:8px; border:1px solid #ddd; background:#f2f2f2;">Ticker</th>'
    for col in df.columns:
        html += f'<th style="padding:8px; border:1px solid #ddd; background:#f2f2f2;">{col}</th>'
    html += '</tr></thead><tbody>'

    # Rows
    for ticker in df.index:
        html += '<tr>'
        html += f'<td style="padding:8px; border:1px solid #ddd; font-weight:bold;">{ticker}</td>'
        for col in df.columns:
            val = df.loc[ticker, col]
            direction = metric_directions.get(col, 'higher_better')
            bg_color = color_for(val, col, col_mins[col], col_maxs[col], direction)
            formatted = format_value(col, val)
            html += f'<td style="padding:8px; border:1px solid #ddd; background:{bg_color};">{formatted}</td>'
        html += '</tr>'

    html += '</tbody></table></div>'
    return html


def create_cumulative_returns_chart(cumulative_returns: pd.DataFrame) -> go.Figure:
    """Line chart of cumulative returns over time."""
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


def create_scatter_plot(annual_returns, annual_vol, sharpe) -> go.Figure:
    """Risk-return bubble chart."""
    sizes = np.maximum(sharpe.values + 2.5, 5)
    fig = px.scatter(
        x=annual_vol.values,
        y=annual_returns.values,
        text=annual_returns.index,
        size=sizes,
        size_max=25,
        color=sharpe.values,
        color_continuous_scale='RdYlGn',
        labels={'x': 'Annualized Volatility (%)', 'y': 'Annualized Return (%)', 'color': 'Sharpe Ratio'},
        title="Risk vs. Return (Bubble Size = Sharpe Ratio)"
    )
    fig.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='DarkSlateGrey')))
    fig.update_layout(height=500, xaxis_title="Annualized Volatility (%) (Risk)", yaxis_title="Annualized Return (%)",
                      hovermode='closest', margin=dict(l=20, r=20, t=50, b=20))
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    return fig


def create_radar_chart(adj_close: pd.DataFrame) -> go.Figure:
    """Spider chart comparing normalized metrics."""
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
        min_val, max_val = values.min(), values.max()
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
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickvals=[0, 25, 50, 75, 100],
                                ticktext=['0', '25', '50', '75', '100'])),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=550,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def create_correlation_heatmap(daily_returns: pd.DataFrame) -> go.Figure:
    """Correlation matrix heatmap."""
    corr_matrix = daily_returns.corr().round(3)
    fig = px.imshow(corr_matrix, text_auto=True, color_continuous_scale='RdBu_r', zmin=-1, zmax=1, aspect="auto")
    fig.update_layout(title=dict(text="Return Correlation Matrix", font=dict(size=16)),
                      height=500, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def create_returns_histogram(daily_returns: pd.DataFrame, selected_ticker: str) -> go.Figure:
    """Histogram of daily returns with normal curve overlay."""
    returns_series = daily_returns[selected_ticker].dropna()
    if returns_series.empty:
        return None
    fig = px.histogram(returns_series, nbins=50,
                       title=f"Daily Return Distribution — {selected_ticker}",
                       labels={'value': 'Daily Return', 'count': 'Frequency'},
                       opacity=0.7, color_discrete_sequence=['#1f77b4'])
    mean, std = returns_series.mean(), returns_series.std()
    x = np.linspace(mean - 3.5*std, mean + 3.5*std, 100)
    y = np.exp(-0.5 * ((x - mean)/std)**2) / (std * np.sqrt(2*np.pi))
    bin_width = (returns_series.max() - returns_series.min()) / 50
    y_scaled = y * len(returns_series) * bin_width
    fig.add_trace(go.Scatter(x=x, y=y_scaled, mode='lines', name='Normal Reference',
                             line=dict(color='red', width=2, dash='dash')))
    fig.update_layout(height=500, showlegend=True, yaxis_title="Frequency", xaxis_title="Daily Return",
                      margin=dict(l=20, r=20, t=50, b=20))
    return fig


# -----------------------------------------------------------------------------
# SIDEBAR CONFIGURATION
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Configuration")

# Load data early to get column names for multiselect
raw_data = load_sample_data()
all_tickers = raw_data.columns.tolist()

st.sidebar.subheader("📈 Stock Selection")
selected_tickers = st.sidebar.multiselect(
    "Choose stocks to compare:",
    options=all_tickers,
    default=all_tickers
)

if not selected_tickers:
    st.sidebar.warning("Please select at least one stock.")
else:
    st.sidebar.info(f"Selected: {', '.join(selected_tickers)}")

st.sidebar.subheader("📅 Date Range")
default_start = datetime(2023, 1, 1)
default_end = datetime(2025, 12, 31)
start_date = st.sidebar.date_input("Start Date", value=default_start)
end_date = st.sidebar.date_input("End Date", value=default_end)
if start_date >= end_date:
    st.sidebar.error("Start date must be before end date.")

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
    default=indicator_options
)

st.sidebar.subheader("📊 Chart Visibility")
show_line_chart = st.sidebar.checkbox("Cumulative Returns Line Chart", value=True)
show_table = st.sidebar.checkbox("Risk & Return Summary Table", value=True)
show_scatter = st.sidebar.checkbox("Risk-Return Scatter Plot", value=True)
show_radar = st.sidebar.checkbox("Radar Chart", value=True)
show_histogram = st.sidebar.checkbox("Daily Return Histogram", value=True)
show_heatmap = st.sidebar.checkbox("Correlation Heatmap", value=True)

st.sidebar.subheader("📈 Parameters")
risk_free_rate_pct = st.sidebar.slider("Risk-Free Rate (%)", 0.0, 10.0, 2.0, 0.5)
risk_free_rate = risk_free_rate_pct / 100

run_analysis = st.sidebar.button("🚀 Run Analysis", type="primary", use_container_width=True)


# -----------------------------------------------------------------------------
# MAIN CONTENT AREA
# -----------------------------------------------------------------------------
if run_analysis and selected_tickers:
    # Filter data
    adj_close = raw_data.loc[(raw_data.index >= pd.Timestamp(start_date)) &
                             (raw_data.index <= pd.Timestamp(end_date)), selected_tickers].copy()

    if adj_close.empty:
        st.error("No data available for the selected date range.")
        st.stop()

    with st.spinner("⏳ Computing risk and return metrics..."):
        metrics = compute_metrics(adj_close, risk_free_rate)

    daily_returns = metrics['daily_returns']
    annual_return = metrics['annual_return'] * 100
    annual_volatility = metrics['annual_volatility'] * 100
    sharpe_ratio = metrics['sharpe_ratio']
    max_drawdown = metrics['max_drawdown'] * 100
    var_95 = metrics['var_95'] * 100
    cumulative_returns = metrics['cumulative_returns']

    # Build summary DataFrame (only selected indicators)
    indicator_map = {
        "Annual Return (%)": annual_return,
        "Annual Volatility (%)": annual_volatility,
        "Sharpe Ratio": sharpe_ratio,
        "Max Drawdown (%)": max_drawdown,
        "VaR 95%": var_95
    }
    summary_data = {k: indicator_map[k] for k in selected_indicators}
    summary_df = pd.DataFrame(summary_data, index=annual_return.index)
    if "Annual Return (%)" in summary_df.columns:
        summary_df = summary_df.sort_values("Annual Return (%)", ascending=False)

    # Directions for coloring
    metric_directions = {
        "Annual Return (%)": "higher_better",
        "Sharpe Ratio": "higher_better",
        "Annual Volatility (%)": "lower_better",
        "Max Drawdown (%)": "lower_better",
        "VaR 95%": "lower_better"
    }

    # ==========================
    # DISPLAY CHARTS
    # ==========================
    st.markdown("## 📊 Analysis Results")

    if show_line_chart:
        with st.container():
            st.markdown("### 📈 Cumulative Returns")
            st.plotly_chart(create_cumulative_returns_chart(cumulative_returns), use_container_width=True)
            st.markdown("---")

    if show_table and not summary_df.empty:
        with st.container():
            st.markdown("### 📋 Risk & Return Summary")
            html_table = build_html_colored_table(summary_df, metric_directions)
            st.markdown(html_table, unsafe_allow_html=True)
            st.markdown("---")

    if show_scatter and len(selected_tickers) >= 1:
        with st.container():
            st.markdown("### 🫧 Risk-Return Scatter Plot")
            st.plotly_chart(create_scatter_plot(annual_return, annual_volatility, sharpe_ratio), use_container_width=True)
            st.markdown("*Each point represents a stock. Bubble size reflects the Sharpe Ratio.*")
            st.markdown("---")

    if show_radar and len(selected_tickers) >= 1:
        with st.container():
            st.markdown("### 🕸️ Radar Chart — Metric Comparison")
            st.plotly_chart(create_radar_chart(adj_close), use_container_width=True)
            st.markdown("*Radar values normalized to 0–100. Higher is better; for volatility, drawdown, and VaR the scale is inverted.*")
            st.markdown("---")

    if show_histogram or show_heatmap:
        col_left, col_right = st.columns(2, gap="medium")
        with col_left:
            if show_histogram and len(selected_tickers) >= 1:
                st.markdown("### 📊 Daily Return Distribution")
                sel_ticker = st.selectbox("Select ticker for histogram:", options=selected_tickers, key="hist")
                fig_hist = create_returns_histogram(daily_returns, sel_ticker)
                if fig_hist:
                    st.plotly_chart(fig_hist, use_container_width=True)
        with col_right:
            if show_heatmap and len(selected_tickers) >= 2:
                st.markdown("### 🔥 Correlation Heatmap")
                st.plotly_chart(create_correlation_heatmap(daily_returns), use_container_width=True)
                st.markdown("*A value of 1 means perfect positive correlation; -1 means perfect negative correlation.*")

    if not any([show_line_chart, show_table, show_scatter, show_radar, show_histogram, show_heatmap]):
        st.info("All charts are currently hidden. Tick the boxes in the sidebar to display them.")

elif run_analysis and not selected_tickers:
    st.warning("Please select at least one stock from the sidebar.")
else:
    st.info("👈 Configure the parameters in the left sidebar and click **Run Analysis** to begin.")
    st.markdown("""
    ### 📌 How to Use This Dashboard

    1. **Select stocks** from the dropdown (populated from your CSV file).
    2. **Set the date range** for analysis.
    3. **Choose indicators** to display in the summary table.
    4. **Toggle charts** on/off as needed.
    5. Click **Run Analysis** to generate the dashboard.

    The app computes:
    - Annualized return & volatility
    - Sharpe ratio
    - Maximum drawdown
    - Value at Risk (95%)
    """)
