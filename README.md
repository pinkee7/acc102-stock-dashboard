# Stock Risk & Return Dashboard

## 1. Problem & User
This tool helps individual investors compare the risk and return 
characteristics of selected stocks. The target audience includes 
finance students and retail investors who want a quick overview 
of historical performance and risk levels.

## 2. Data
- Source: Yahoo Finance (via CSV export)  
- Access date: [2026.4.22]  
- Tickers: AAPL, AMZN, GOOGL, JPM, MSFT, NVDA, TSLA, UNH
- Period: 2020-01-01 to 2024-12-31  

## 3. Methods
- Data loading with pandas  
- Calculation of annual return, volatility, Sharpe ratio, max drawdown, VaR  
- Interactive visualisation with Plotly  
- Streamlit app for user interaction  

## 4. Key Findings

- **NVDA** delivered the highest cumulative return by a wide margin, driven by the AI boom, but its volatility and maximum drawdown were also among the highest — a classic high-risk/high-reward profile.
- **TSLA** also achieved strong returns, though with significantly higher volatility, reflecting the speculative nature of the EV sector.
- **MSFT** and **GOOGL** offered a better balance between return and risk, resulting in the highest Sharpe ratios among the selected stocks.
- **UNH**, as the only healthcare stock, showed the lowest volatility and most stable growth, demonstrating the diversification benefit of including non-tech sectors.
- **JPM** (financials) exhibited moderate returns and volatility, with relatively low correlations to the tech-heavy tickers — useful for portfolio diversification.
- The correlation heatmap confirmed that most tech stocks were highly correlated with each other, while UNH and JPM offered lower correlations.

## 5. How to Run
1. Clone the repository
2. Install dependencies: pip install -r requirements.txt
3. Run the app: streamlit run app.py
4. Open https://acc102-stock-dashboard-hsufjpekifpp8vej8ywyfs.streamlit.app in your browser

## 6. Product Link / Demo
(视频链接)

## 7. Limitations & Next Steps
- Only historical data, no forward‑looking predictions
- Small sample of stocks, may not represent the whole market
- Next step: add more stocks, enable real‑time data