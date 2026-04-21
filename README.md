# StockInsight – A-share Data Analysis Workbench

## 1. Problem & User

Retail investors and finance students need a simple, code‑based tool to evaluate risk‑return profiles of individual A‑shares (China market). This project provides an interactive Streamlit dashboard that computes key metrics – volatility, maximum drawdown, Sharpe ratio, and abnormal volume days – to support better investment decisions.

## 2. Data

- **Source:** baostock (http://baostock.com) – free, no registration, stable in China  
- **Access date:** 21 April 2026 (the date the notebook was last run)  
- **Example stock:** `000001` (Ping An Bank)  
- **Time range:** last 365 days (user‑adjustable in the app)  
- **Key fields:** `date`, `open`, `high`, `low`, `close`, `volume` (forward adjusted, `adjustflag=2`)

## 3. Methods

1. **Data acquisition** – Login to baostock, fetch historical daily data for any 6‑digit A‑share code.  
2. **Data cleaning** – Convert types, handle missing values, validate prices and volume.  
3. **Feature engineering** – Compute daily returns, cumulative returns, 20/50‑day moving averages, and flag abnormal volume days (> mean + 2 std).  
4. **Risk/return metrics** – Annualized volatility, maximum drawdown (with peak/trough dates), Sharpe ratio (risk‑free rate = 2%), total return.  
5. **Visualisation** – Interactive Plotly charts: price trend, return distribution, cumulative return, volume with anomalies.  
6. **Interactive dashboard** – Streamlit app wraps the same logic with user inputs (stock code, date range, moving average toggles).

## 4. Key Findings

Based on the analysis of `000001` (Ping An Bank) over the last 365 days (21 Apr 2025 – 21 Apr 2026):

- **Total return:** +5.89% – the stock gained value over the period.  
- **Annualized volatility:** 14.85% – relatively low, indicating stable price movements.  
- **Maximum drawdown:** –19.03% (from 2025-07-10 to 2026-03-23) – a significant peak‑to‑trough loss of nearly 20%.  
- **Sharpe ratio:** 0.34 – positive but modest risk‑adjusted return (exceeds risk‑free rate).  
- **Abnormal volume days:** 13 days with volume > mean + 2 standard deviations, often coinciding with news or earnings releases.

## 5. How to run

1. **Clone the repository**  
   ```bash
   git clone https://github.com/Staratjade/ACC102-assignment.git
   cd ACC102-assignment
2. **Install dependencies** 
   ```bash
   pip install -r requirements.txt
3. **Run the Streamlit app locally** 
   ```bash
   streamlit run app.py
4. **Explore the analysis notebook**
   Open Notebook.ipynb in VS Code to see the step‑by‑step workflow.
   
## 6. Product link / Demo

- **GitHub repository:** [https://github.com/Staratjade/ACC102-assignment](https://github.com/Staratjade/ACC102-assignment)  
- **Demo video (Mediasite):** [Insert your Mediasite link here]  
- **Streamlit app:** run locally as described above

## 7. Limitations & next steps

- **Data limitations:** baostock does not provide company names, dividends, or corporate actions beyond adjusted prices.  
- **Risk‑free rate:** fixed at 2%; using real‑time bond yields would improve Sharpe ratio accuracy.  
- **Single‑stock only:** current version analyses one stock at a time; future enhancement could add multi‑stock comparison and sector benchmarks.  
- **No fundamental data:** adding P/E, P/B, or financial ratios would enrich insights.  
- **Export feature:** planned PDF/CSV report export for user convenience.
