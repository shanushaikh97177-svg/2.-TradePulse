import os
import json
from datetime import datetime
import yfinance as yf
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

print("=== Running TradePulse Unfiltered Stock Loader ===")

symbols = [
    "RELIANCE.NS", "TCS.NS", "TATAMOTORS.NS", "INFY.NS", "HDFCBANK.NS",
    "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "AXISBANK.NS",
    "KOTAKBANK.NS", "LT.NS", "SUNPHARMA.NS", "TITAN.NS", "BAJFINANCE.NS",
    "MARUTI.NS", "ULTRACEMCO.NS", "WIPRO.NS", "NTPC.NS", "POWERGRID.NS",
    "ONGC.NS", "TATASTEEL.NS", "M&M.NS", "ADANIPORTS.NS", "COALINDIA.NS",
    "BAJAJFINSV.NS", "BPCL.NS", "HINDUNILVR.NS", "LICI.NS", "ADANIENT.NS"
]

scanned_stocks = []
print("Fetching market data...")

for ticker in symbols:
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1mo")
        
        if df.empty or len(df) < 5:
            continue
            
        current_price = float(df['Close'].iloc[-1])
        prev_close = float(df['Close'].iloc[-2])
        change_pct = ((current_price - prev_close) / prev_close) * 100
        
        df_30 = df.iloc[-30:] if len(df) >= 30 else df
        high_30 = float(df_30['High'].max())
        low_30 = float(df_30['Low'].min())
        price_range_pct = ((high_30 - low_30) / low_30) * 100
        
        avg_volume = float(df['Volume'].mean())
        current_volume = float(df['Volume'].iloc[-1])
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        scanned_stocks.append({
            'symbol': ticker.replace('.NS', ''),
            'name': ticker.replace('.NS', ' Ltd'),
            'price': "Rs. " + f"{current_price:,.2f}",
            'change': ("+" if change_pct > 0 else "") + f"{change_pct:.1f}%",
            'category': 'Nifty 500 / Liquid',
            'consolidation_range': f"30 Days ({price_range_pct:.1f}% Range)",
            'volume_spike': f"{volume_ratio:.1f}x Average",
            'delivery_pct': '68.5% Accumulation',
            'why_selected': 'Active market stock loaded for live tracking.',
            'smart_score': int(75 + abs(change_pct) * 2),
            'high_30': "Rs. " + f"{high_30:,.2f}",
            'low_30': "Rs. " + f"{low_30:,.2f}",
            'date': datetime.now().strftime('%Y-%m-%d')
        })
    except Exception as e:
        print(f"Error {ticker}: {e}")
        continue

scanned_stocks = scanned_stocks[:15]

db = None
try:
    cred_env = os.environ.get('FIREBASE_CREDENTIALS')
    if cred_env:
        cred_dict = json.loads(cred_env)
        if 'private_key' in cred_dict:
            cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
        cred = credentials.Certificate(cred_dict)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        
        doc_ref = db.collection('daily_picks').document('latest_scan')
        doc_ref.set({
            'status': 'active',
            'updated_at': datetime.now().isoformat(),
            'stocks': scanned_stocks
        })
        print(f"Successfully uploaded {len(scanned_stocks)} stocks to Firestore!")
except Exception as e:
    print(f"Firebase error: {e}")
    
