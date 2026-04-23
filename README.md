# Stock Analysis Dashboard (ACC102 Track 4)

## 1. Problem & Intended User
This interactive tool helps individual investors and finance students quickly compare historical performance and risk characteristics of multiple US stocks. The intended audience is retail investors with basic financial knowledge who want a simple, visual way to understand risk-return trade-offs.

## 2. Data Source
- **Source**: `sample_stock_data.csv` - Historical adjusted close price data for demonstration purposes.
- **Data Generation**: The dataset was compiled using price ranges derived from publicly available historical stock data (Yahoo Finance) to simulate realistic price movements. The data is intended solely for educational demonstration of the analytical workflow.
- **Access Date**: 21 April 2026
- **Key Fields**: Date (index), Adjusted Close Prices for 8 US stocks (AAPL, MSFT, GOOGL, AMZN, TSLA, JPM, NVDA, META)
- **Time Period Covered**: January 2024 to April 2024 (approximately 3 months of daily data)
- **Note**: This is a static sample dataset. In a production environment, the tool could be connected to a live data API such as Yahoo Finance or Alpha Vantage.

## 3. Methods (Python Workflow)
- **Data Loading**: `pandas.read_csv()` with date parsing and setting index.
- **Data Transformation**: Calculation of daily percentage returns, cumulative returns, rolling volatility.
- **Analysis**: Annualized return, annualized volatility, Sharpe ratio, maximum drawdown.
- **Visualization**: Interactive charts using Plotly (line, bar, heatmap, pie).
- **Interface**: Streamlit sidebar for user controls and real-time updates.

## 4. Key Findings (Illustrative Example)
- From Jan to Jun 2024, NVDA showed the highest cumulative return but also the highest volatility.
- MSFT and AAPL demonstrated more stable growth with lower volatility and higher Sharpe ratios.
- The correlation heatmap reveals strong positive correlation among tech stocks, especially between MSFT and AAPL.

## 5. How to Run Locally
1. Clone this repository: