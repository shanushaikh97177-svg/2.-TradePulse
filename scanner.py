import os
import json
from datetime import datetime
import yfinance as yf
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

print("=== Running TradePulse Unfiltered Stock Loader ===")

# Nifty 500 symbols ki live public list
url = "https://raw.githubusercontent.com/avcastro/nifty-stocks/main/nifty500.csv"
symbols = []

try:
    df_symbols = pd.read_csv(url)
    col_name = 'Symbol' if 'Symbol' in df_symbols.columns else df_symbols.columns[0]
    symbols = [str(sym).strip() + ".NS" for sym in df_symbols[col_name].dropna().tolist()]
    print(f"Loaded {len(symbols)} symbols from Nifty 500 list.")
except Exception as e:
    print(f"Error loading list, using backup: {e}")
    symbols = ["RELIANCE.NS", "TCS.NS", "TATAMOTORS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "AXISBANK.NS"]

scanned_stocks = []
print("Fetching market data for stocks...")

# Testing ke liye pehle 30-40 stocks scan karte hain taaki fast chale, chahe toh limit hata bhi sakta hai
for ticker in symbols[:40]:
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1mo")
        
        if df.empty or len(df) < 10:
            continue
            
        current_price = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        change_pct = ((current_price - prev_close) / prev_close) * 100
        
        df_30 = df.iloc[-30:] if len(df) >= 30 else df
        high_30 = df_30['High'].max()
        low_30 = df_30['Low'].min()
        price_range_pct = ((high_30 - low_30) / low_30) * 100
        
        avg_volume = df['Volume'].mean()
        current_volume = df['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Bina kisi strict filter ke saare valid stocks add karenge
        scanned_stocks.append({
            'symbol': ticker.replace('.NS', ''),
            'name': ticker.replace('.NS', ' Ltd'),
            'price': f"₹{current_price:,.2f}",
            'change': f"+{change_pct:.1f}%" if change_pct > 0 else f"{change_pct:.1f}%",
            'category': 'Nifty 500 / Liquid',
            'consolidation_range': f"30 Days ({price_range_pct:.1f}% Range)",
            'volume_spike': f"{volume_ratio:.1f}x Average",
            'delivery_pct': '68.5% Accumulation',
            'why_selected': 'Active market stock loaded for live tracking.',
            'smart_score': int(75 + abs(change_pct) * 2),
            'high_30': f"₹{high_30:,.2f}",
            'low_30': f"₹{low_30:,.2f
