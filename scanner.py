import os
import json
from datetime import datetime
import yfinance as yf
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

print("=== Running TradePulse Local Nifty 500 Batch Scanner ===")

# Local uploaded CSV file se symbols read karenge
try:
    df_symbols = pd.read_csv('ind_nifty500list.csv')
    symbols = [str(sym).strip() + ".NS" for sym in df_symbols['Symbol'].dropna().tolist()]
    print(f"Loaded {len(symbols)} symbols from local Nifty 500 file.")
except Exception as e:
    print(f"Error loading local CSV: {e}")
    symbols = ["RELIANCE.NS", "TCS.NS", "TATAMOTORS.NS", "INFY.NS", "HDFCBANK.NS"]

scanned_stocks = []
print("Downloading batch data from Yahoo Finance...")

try:
    # Saare symbols ko ek sath batch mein download karenge
    batch_data = yf.download(symbols, period="1mo", group_by='ticker', threads=True, progress=False)
    
    for ticker in symbols:
        try:
            if len(symbols) == 1:
                df = batch_data
            else:
                df = batch_data[ticker]
            
            if df.empty:
                continue
            
            df = df.dropna(subset=['Close', 'Volume'])
            if len(df) < 5:
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
        except Exception:
            continue
except Exception as e:
    print(f"Batch download error: {e}")

print(f"Total successfully processed stocks: {len(scanned_stocks)}")

# Firebase Connection & Upload
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
        print(f"Successfully uploaded all {len(scanned_stocks)} stocks to Firestore!")
except Exception as e:
    print(f"Firebase error: {e}")
    
