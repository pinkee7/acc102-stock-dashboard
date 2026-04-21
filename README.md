# Stock Return & Volatility Comparison Tool (ACC102 Track 4)

## 1. Problem & Intended User
This interactive tool helps individual investors and finance students quickly compare the historical performance and risk characteristics of multiple US stocks without using complex financial terminals. The intended audience is retail investors with basic financial knowledge.

## 2. Data Source
## 2. Data Source
The application intelligently sources financial data through multiple layers to ensure reliability:
1.  **Kaggle (Primary)**: Leverages the "Stock 2025" dataset, a comprehensive collection of S&P 500 company data from 2020 to 2025. This provides a rich, static foundation for analysis.
2.  **Yahoo Finance (Secondary)**: Fetches real-time market data via the `yfinance` library, offering the most up-to-date information when an internet connection is available.
3.  **Local CSV (Fallback)**: A local, pre-loaded dataset (`sample_stock_data.csv`) serves as a fail-safe, guaranteeing the application remains functional and demonstrable even without internet access or if upstream data sources encounter issues.
- **Access Date**: 21 April 2026
- **Key Fields**: Adjusted Close Price, Ticker Symbols (AAPL, MSFT, GOOGL, AMZN, TSLA, JPM, NVDA, META)

## 3. Methods (Python Workflow)
- **Data Acquisition**: `yfinance.download()` retrieves adjusted close prices for selected tickers.
- **Data Transformation**: Calculation of daily percentage returns and cumulative return series.
- **Analysis**: Computation of annualized return, annualized volatility, and Sharpe ratio (assuming risk-free rate = 0 for simplicity).
- **Visualization**: Interactive line chart using Plotly.
- **Interface**: Streamlit provides user controls (multiselect, date inputs) and real-time output updates.

## 4. Key Findings (Illustrative Example)
- From Jan 2024 to Apr 2026, NVDA showed the highest cumulative return but also the highest volatility.
- MSFT and AAPL demonstrated more stable growth with lower volatility.
- The dashboard allows users to test their own date ranges and ticker combinations.

## 5. How to Run Locally
1. Clone this repository (replace pinkee7 after Step 7):