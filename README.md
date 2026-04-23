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

- **TSLA** delivered the highest annualised return over the period but also exhibited the highest volatility and the deepest maximum drawdown, representing a classic high‑risk/high‑reward profile.
- **MSFT** and **GOOGL** achieved the highest Sharpe ratios, meaning they offered the best risk‑adjusted returns among the selected stocks.
- **JPM** showed the lowest correlation with the technology stocks (TSLA, AAPL, MSFT, GOOGL, AMZN), highlighting its potential diversification benefit in a multi‑sector portfolio.
- **AAPL** demonstrated the smallest maximum drawdown among the tech names, suggesting relatively better downside resilience.
- According to the 95% Value‑at‑Risk, **TSLA** had the largest expected daily loss, while **JPM** had the smallest, reflecting differences in inherent business risk.

## 5. How to Run
1. Clone the repository
2. Install dependencies: pip install -r requirements.txt
3. Run the app: streamlit run app.py
4. Open http://localhost:8502 in your browser

## 6. Product Link / Demo
(视频链接)

## 7. Limitations & Next Steps
- Only historical data, no forward‑looking predictions
- Small sample of stocks, may not represent the whole market
- Next step: add more stocks, enable real‑time data