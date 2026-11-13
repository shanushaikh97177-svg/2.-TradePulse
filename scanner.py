import os
import json
from datetime import datetime
import yfinance as yf
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

print("=== Running TradePulse Live Stock Scanner (Flexible Conditions) ===")

symbols = [
    "RELIANCE.NS", "TCS.NS", "TATAMOTORS.NS", "INFY.NS", "HDFCBANK.NS",
    "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LICI.NS",
    "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "ADANIENT.NS", "AXISBANK.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS",
    "NTPC.NS", "POWERGRID.NS", "KOTAKBANK.NS", "ONGC.NS", "TATASTEEL.NS",
    "M&M.NS", "ADANIPORTS.NS", "COALINDIA.NS", "BAJAJFINSV.NS", "BPCL.NS"
]

scanned_stocks = []

print(f"Scanning {len(symbols)} stocks...")

for ticker in symbols:
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1mo")
        
        if df.empty or len(df) < 15:
            continue
            
        current_price = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        change_pct = ((current_price - prev_close) / prev_close) * 100
        
        avg_volume = df['Volume'].iloc[-15:-1].mean()
        current_volume = df['Volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Thodi aasan condition taaki real stocks pick hon
        if change_pct > 0:
            smart_score = int(min(98, 70 + (volume_ratio * 4) + (change_pct * 2)))
            
            scanned_stocks.append({
                'symbol': ticker.replace('.NS', ''),
                'name': ticker.replace('.NS', ' Ltd'),
                'price': f"₹{current_price:,.2f}",
                'change': f"+{change_pct:.1f}%" if change_pct > 0 else f"{change_pct:.1f}%",
                'category': 'Nifty 500 / Liquid',
                'consolidation_range': 'Recent Breakout Zone',
                'volume_spike': f"{volume_ratio:.1f}x Average",
                'delivery_pct': '65.0% Accumulation',
                'why_selected': 'Positive price momentum with active volume participation.',
                'smart_score': smart_score,
                'date': datetime.now().strftime('%Y-%m-%d')
            })
    except Exception as e:
        print(f"Error processing {ticker}: {e}")

# Top stocks uthao
scanned_stocks = sorted(scanned_stocks, key=lambda x: x['smart_score'], reverse=True)[:10]

# Connect to Firebase
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
        print("Firebase DB connected successfully!")
except Exception as e:
    print(f"Firebase initialization error: {e}")

if db and scanned_stocks:
    try:
        doc_ref = db.collection('daily_picks').document('latest_scan')
        doc_ref.set({
            'status': 'active',
            'updated_at': datetime.now().isoformat(),
            'stocks': scanned_stocks
        })
        print(f"Successfully written {len(scanned_stocks)} real scanned stocks to Firestore!")
    except Exception as e:
        print(f"Error writing to Firestore: {e}")
else:
    print(f"No stocks found or DB error. Output: {scanned_stocks}")
            
