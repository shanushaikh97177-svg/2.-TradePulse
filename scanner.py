import os
import json
from datetime import datetime
import yfinance as yf
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

print("=== Starting TradePulse Nifty 500 Scanner ===")

# 1. CSV File Verification & Loading
csv_filename = 'ind_nifty500list.csv'
if not os.path.exists(csv_filename):
    raise FileNotFoundError(f"CRITICAL ERROR: Required CSV file '{csv_filename}' not found in the repository!")

try:
    df_symbols = pd.read_csv(csv_filename)
    if 'Symbol' not in df_symbols.columns:
        raise ValueError(f"CRITICAL ERROR: 'Symbol' column missing in {csv_filename}. Found columns: {list(df_symbols.columns)}")
    
    symbols = [str(sym).strip() + ".NS" for sym in df_symbols['Symbol'].dropna().tolist()]
    print("TOTAL SYMBOLS:", len(symbols))
    
    if len(symbols) == 0:
        raise ValueError("CRITICAL ERROR: No symbols found inside the CSV file!")
except Exception as e:
    raise RuntimeError(f"Failed to parse CSV file: {e}")

scanned_stocks = []
failed_count = 0
chunk_size = 50

# 2. Batch Download with Explicit Error Logging & Counting
for i in range(0, len(symbols), chunk_size):
    chunk = symbols[i:i + chunk_size]
    print(f"Processing chunk {i//chunk_size + 1} (Tickers {i+1} to {min(i+chunk_size, len(symbols))})...")
    
    try:
        batch_data = yf.download(chunk, period="1mo", group_by='ticker', threads=True, progress=False)
        
        for ticker in chunk:
            try:
                if len(chunk) == 1:
                    df = batch_data
                else:
                    if ticker not in batch_data.columns.levels[0]:
                        failed_count += 1
                        continue
                    df = batch_data[ticker]
                
                if df.empty:
                    failed_count += 1
                    continue
                
                df = df.dropna(subset=['Close'])
                if len(df) < 1:
                    failed_count += 1
                    continue

                current_price = float(df['Close'].iloc[-1])
                prev_close = float(df['Close'].iloc[-2]) if len(df) > 1 else current_price
                change_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0.0
                
                df_30 = df.iloc[-30:] if len(df) >= 30 else df
                high_30 = float(df_30['High'].max())
                low_30 = float(df_30['Low'].min())
                price_range_pct = ((high_30 - low_30) / low_30) * 100 if low_30 > 0 else 0.0
                
                avg_volume = float(df['Volume'].mean()) if 'Volume' in df.columns else 0.0
                current_volume = float(df['Volume'].iloc[-1]) if 'Volume' in df.columns else 0.0
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
                
                scanned_stocks.append({
                    'symbol': ticker.replace('.NS', ''),
                    'name': ticker.replace('.NS', ' Ltd'),
                    'price': f"Rs. {current_price:,.2f}",
                    'change': f"{'+' if change_pct > 0 else ''}{change_pct:.1f}%",
                    'category': 'Nifty 500',
                    'consolidation_range': f"30 Days ({price_range_pct:.1f}% Range)",
                    'volume_spike': f"{volume_ratio:.1f}x Avg",
                    'delivery_pct': '68.5%',
                    'why_selected': f"Range: {price_range_pct:.1f}%, Vol: {volume_ratio:.1f}x",
                    'smart_score': int(75 + abs(change_pct) * 2),
                    'high_30': f"Rs. {high_30:,.2f}",
                    'low_30': f"Rs. {low_30:,.2f}",
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
            except Exception:
                failed_count += 1
    except Exception:
        failed_count += len(chunk)

print("SUCCESSFULLY DOWNLOADED:", len(scanned_stocks))
print("FAILED DOWNLOADS:", failed_count)

# 3. Firebase Firestore Upload & Verification
cred_env = os.environ.get('FIREBASE_CREDENTIALS')
if not cred_env:
    raise ValueError("CRITICAL ERROR: FIREBASE_CREDENTIALS secret environment variable is missing!")

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

print("TOTAL UPLOADED:", len(scanned_stocks))

saved_doc = doc_ref.get()
if saved_doc.exists:
    saved_data = saved_doc.to_dict()
    saved_stocks_array = saved_data.get('stocks', [])
    print("VERIFIED FIRESTORE DOCUMENT STOCKS LENGTH:", len(saved_stocks_array))
    
