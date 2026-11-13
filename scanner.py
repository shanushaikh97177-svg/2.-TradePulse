import os
import json
from datetime import datetime
import yfinance as yf
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

try:
    df_symbols = pd.read_csv('ind_nifty500list.csv')
    symbols = [str(sym).strip() + ".NS" for sym in df_symbols['Symbol'].dropna().tolist()]
except Exception:
    symbols = ["RELIANCE.NS", "TCS.NS", "TATAMOTORS.NS", "INFY.NS", "HDFCBANK.NS"]

scanned_stocks = []
chunk_size = 50

for i in range(0, len(symbols), chunk_size):
    chunk = symbols[i:i + chunk_size]
    try:
        batch_data = yf.download(chunk, period="1d", group_by='ticker', threads=True, progress=False)
        for ticker in chunk:
            try:
                df = batch_data if len(chunk) == 1 else batch_data[ticker]
                if df.empty: continue
                df = df.dropna(subset=['Close'])
                if len(df) < 1: continue

                p = float(df['Close'].iloc[-1])
                
                scanned_stocks.append({
                    'symbol': ticker.replace('.NS', ''),
                    'name': ticker.replace('.NS', ' Ltd'),
                    'price': f"Rs. {p:,.2f}",
                    'change': "0.0%",
                    'category': 'Nifty 500',
                    'consolidation_range': 'N/A',
                    'volume_spike': 'N/A',
                    'delivery_pct': 'N/A',
                    'why_selected': 'Direct Stock Loaded',
                    'smart_score': 80,
                    'high_30': f"Rs. {p:,.2f}",
                    'low_30': f"Rs. {p:,.2f}",
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
            except Exception:
                continue
    except Exception:
        continue

cred_env = os.environ.get('FIREBASE_CREDENTIALS')
if cred_env:
    cred_dict = json.loads(cred_env)
    if 'private_key' in cred_dict:
        cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
    cred = credentials.Certificate(cred_dict)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    db.collection('daily_picks').document('latest_scan').set({
        'status': 'active',
        'updated_at': datetime.now().isoformat(),
        'stocks': scanned_stocks
    })
print(f"Total uploaded: {len(scanned_stocks)}")
