"""
StockInsight - A-share Data Analysis Workbench (baostock)
Data source: baostock (free, no registration, direct connection in China)
Supports: A-shares (6-digit codes, e.g., 000001, 600519)
"""

import streamlit as st
import baostock as bs
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# ==================== Page Configuration ====================
st.set_page_config(
    page_title="StockInsight - A-share Data Analysis Workbench",
    page_icon="📈",
    layout="wide"
)

# ==================== Data Fetching Functions (baostock) ====================

@st.cache_data(ttl=600)
def fetch_a_stock_data(symbol, start_date, end_date):
    """
    Fetch A-share historical daily data (forward adjusted) using baostock.
    symbol: 6-digit stock code, e.g., '000001'
    start_date, end_date: 'YYYY-MM-DD' strings
    Returns: (DataFrame, stock_name) or (None, None)
    """
    try:
        # Login to baostock
        lg = bs.login()
        if lg.error_code != '0':
            st.error(f"baostock login failed: {lg.error_msg}")
            return None, None
        
        # Format code: sh.xxxxxx for Shanghai, sz.xxxxxx for Shenzhen
        if symbol.startswith('6'):
            code = f"sh.{symbol}"
        else:
            code = f"sz.{symbol}"
        
        # Query historical data (forward adjusted adjustflag=2)
        rs = bs.query_history_k_data_plus(
            code=code,
            fields="date,open,high,low,close,volume",
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="2"   # 2 = forward adjusted
        )
        
        # Collect data
        data_list = []
        while rs.next():
            data_list.append(rs.get_row_data())
        
        # Logout
        bs.logout()
        
        if not data_list:
            return None, None
        
        # Convert to DataFrame
        df = pd.DataFrame(data_list, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        
        # Stock name is not directly provided by baostock; use code as placeholder
        stock_name = symbol
        
        return df, stock_name
        
    except Exception as e:
        st.error(f"baostock data fetch failed: {str(e)}")
        return None, None

def compute_metrics(data):
    """Calculate various risk/return metrics"""
    if data is None or data.empty:
        return {}
    
    df = data.copy()
    df['Daily_Return'] = df['Close'].pct_change()
    df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod() - 1
    
    # Annualized volatility
    daily_vol = df['Daily_Return'].std()
    annual_vol = daily_vol * np.sqrt(252)
    
    # Maximum drawdown
    cumulative = (1 + df['Daily_Return']).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    if max_drawdown < 0:
        end_idx = drawdown.idxmin()
        start_idx = cumulative[:end_idx].idxmax()
        max_dd_start = start_idx.strftime('%Y-%m-%d')
        max_dd_end = end_idx.strftime('%Y-%m-%d')
    else:
        max_dd_start = max_dd_end = None
    
    # Sharpe ratio
    risk_free_rate = 0.02
    excess_return = df['Daily_Return'].mean() * 252 - risk_free_rate
    sharpe_ratio = excess_return / annual_vol if annual_vol != 0 else np.nan
    
    # High volume days
    vol_mean = df['Volume'].mean()
    vol_std = df['Volume'].std()
    high_volume_days = df[df['Volume'] > vol_mean + 2*vol_std].index.tolist()
    
    metrics = {
        'annual_volatility': annual_vol,
        'max_drawdown': max_drawdown,
        'max_dd_start': max_dd_start,
        'max_dd_end': max_dd_end,
        'sharpe_ratio': sharpe_ratio,
        'total_return': df['Cumulative_Return'].iloc[-1] if not df.empty else 0,
        'high_volume_days': high_volume_days,
        'start_date': df.index[0],
        'end_date': df.index[-1]
    }
    return metrics, df

def generate_insights(metrics, symbol, stock_name):
    """Generate automated analysis summary in English"""
    if not metrics or metrics.get('start_date') is None:
        return f"**{stock_name or symbol}** has insufficient data."
    
    insights = []
    insights.append(f"**{stock_name or symbol}** ({symbol})")
    start_str = metrics['start_date'].strftime('%Y-%m-%d')
    end_str = metrics['end_date'].strftime('%Y-%m-%d')
    insights.append(f"During the period from {start_str} to {end_str}:")
    
    total_ret = metrics['total_return']
    if total_ret > 0:
        insights.append(f"- 📈 Cumulative return: **{total_ret:.2%}** (positive performance).")
    else:
        insights.append(f"- 📉 Cumulative return: **{total_ret:.2%}** (negative performance).")
    
    vol = metrics['annual_volatility']
    if vol < 0.15:
        insights.append(f"- ⚖️ Annualized volatility: **{vol:.2%}** (low).")
    elif vol < 0.30:
        insights.append(f"- ⚠️ Annualized volatility: **{vol:.2%}** (moderate).")
    else:
        insights.append(f"- 🔥 Annualized volatility: **{vol:.2%}** (high).")
    
    dd = metrics['max_drawdown']
    if dd is not None and dd < -0.2:
        insights.append(f"- 📉 Maximum drawdown: **{dd:.2%}** ({metrics['max_dd_start']} ~ {metrics['max_dd_end']}).")
    elif dd is not None:
        insights.append(f"- 📉 Maximum drawdown: **{dd:.2%}**.")
    
    sr = metrics['sharpe_ratio']
    if not np.isnan(sr):
        if sr > 1:
            insights.append(f"- 🎯 Sharpe ratio: **{sr:.2f}** (excellent).")
        elif sr > 0:
            insights.append(f"- 🎯 Sharpe ratio: **{sr:.2f}** (positive).")
        else:
            insights.append(f"- ⚠️ Sharpe ratio: **{sr:.2f}** (negative).")
    return "\n".join(insights)

# ==================== UI Layout ====================
st.title("📈 StockInsight – A-share Data Analysis Workbench (baostock)")
st.markdown("Enter a 6-digit A-share code and time range to fetch data and analyze.")

with st.sidebar:
    st.header("⚙️ Control Panel")
    symbol = st.text_input("A-share Code (6 digits)", value="000001", help="e.g., 000001 (Ping An Bank), 600519 (Kweichow Moutai)")
    start_date = st.date_input("Start Date", datetime.today() - timedelta(days=365))
    end_date = st.date_input("End Date", datetime.today())
    show_ma = st.checkbox("Show Moving Averages", value=True)
    if show_ma:
        ma_20 = st.checkbox("20-day MA", value=True)
        ma_50 = st.checkbox("50-day MA", value=True)
    else:
        ma_20 = ma_50 = False
    analyze_btn = st.button("🚀 Start Analysis", type="primary", use_container_width=True)

if analyze_btn:
    if start_date >= end_date:
        st.error("Start date must be earlier than end date.")
        st.stop()
    
    symbol = symbol.strip().zfill(6)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    with st.spinner(f"Fetching data for {symbol} from baostock..."):
        data, stock_name = fetch_a_stock_data(symbol, start_str, end_str)
    
    if data is None or data.empty:
        st.error(f"No data found for {symbol} between {start_date} and {end_date}.")
        st.info("Hint: A-share codes are 6 digits, e.g., 000001. Check the code or date range (non-trading days have no data).")
        st.stop()
    
    metrics, data_with_returns = compute_metrics(data)
    
    # Basic Information
    st.subheader("🏢 Basic Information")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Stock Code", symbol)
    with col2:
        st.metric("Stock Name", stock_name)
    with col3:
        st.metric("Latest Close Price", f"¥{data['Close'].iloc[-1]:.2f}")
    
    # Automated Analysis Summary
    st.subheader("💡 Automated Analysis Summary")
    st.info(generate_insights(metrics, symbol, stock_name))
    
    # Price Trend
    st.subheader("📊 Price Trend")
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Close Price', line=dict(color='blue')))
    if show_ma and ma_20 and len(data) >= 20:
        data['MA20'] = data['Close'].rolling(20).mean()
        fig_price.add_trace(go.Scatter(x=data.index, y=data['MA20'], mode='lines', name='20-day MA', line=dict(color='orange', dash='dash')))
    if show_ma and ma_50 and len(data) >= 50:
        data['MA50'] = data['Close'].rolling(50).mean()
        fig_price.add_trace(go.Scatter(x=data.index, y=data['MA50'], mode='lines', name='50-day MA', line=dict(color='green', dash='dash')))
    fig_price.update_layout(title=f"{symbol} Close Price Trend (Adjusted)", xaxis_title="Date", yaxis_title="Price (CNY)")
    st.plotly_chart(fig_price, use_container_width=True)
    
    # Return Analysis
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("📉 Daily Return Distribution")
        returns = data_with_returns['Daily_Return'].dropna()
        if not returns.empty:
            fig_hist = px.histogram(returns, nbins=50, title="Histogram of Daily Returns", histnorm='probability density')
            fig_hist.add_vline(x=0, line_dash="dash", line_color="red")
            fig_hist.update_layout(xaxis_title="Daily Return", yaxis_title="Probability Density")
            st.plotly_chart(fig_hist, use_container_width=True)
    with col_right:
        st.subheader("📈 Cumulative Return")
        fig_cum = go.Figure()
        fig_cum.add_trace(go.Scatter(x=data_with_returns.index, y=data_with_returns['Cumulative_Return']*100, mode='lines', fill='tozeroy'))
        fig_cum.update_layout(title="Cumulative Return (%)", xaxis_title="Date", yaxis_title="Cumulative Return (%)")
        st.plotly_chart(fig_cum, use_container_width=True)
    
    # Risk Metrics
    st.subheader("⚠️ Risk Metrics")
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.metric("Annual Volatility", f"{metrics['annual_volatility']:.2%}")
    with col_b:
        dd_val = f"{metrics['max_drawdown']:.2%}" if metrics['max_drawdown'] is not None else "N/A"
        st.metric("Max Drawdown", dd_val)
    with col_c:
        sr_val = f"{metrics['sharpe_ratio']:.2f}" if not np.isnan(metrics['sharpe_ratio']) else "N/A"
        st.metric("Sharpe Ratio", sr_val)
    with col_d:
        st.metric("Total Return", f"{metrics['total_return']:.2%}")
    if metrics['max_dd_start']:
        st.caption(f"Max drawdown period: {metrics['max_dd_start']} to {metrics['max_dd_end']}")
    
    # Volume Analysis
    st.subheader("📊 Volume Analysis")
    fig_vol = go.Figure()
    fig_vol.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volume', marker_color='lightblue'))
    if metrics.get('high_volume_days'):
        high_vol_data = data.loc[metrics['high_volume_days']]
        fig_vol.add_trace(go.Scatter(x=high_vol_data.index, y=high_vol_data['Volume'], mode='markers', name='Abnormally High Volume', marker=dict(color='red', size=8)))
    fig_vol.update_layout(title="Daily Trading Volume", xaxis_title="Date", yaxis_title="Volume (Shares)")
    st.plotly_chart(fig_vol, use_container_width=True)
    
    # Data Preview
    st.subheader("📋 Raw Data Preview (last 10 days)")
    st.dataframe(data[['Open', 'High', 'Low', 'Close', 'Volume']].tail(10).style.format({
        'Open': '¥{:.2f}', 'High': '¥{:.2f}', 'Low': '¥{:.2f}', 'Close': '¥{:.2f}'
    }))
else:
    st.info("👈 Enter an A-share code and date range on the left, then click 'Start Analysis'.")
    st.markdown("""
    **Example codes:**
    - Ping An Bank: `000001`
    - Kweichow Moutai: `600519`
    - Wuliangye: `000858`
    
    **Data source:** baostock (free, stable, no registration required)
    """)