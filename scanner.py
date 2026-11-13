import os
import json
from datetime import datetime
import yfinance as yf
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

print("=== Starting TradePulse Pro Scanner (Institutional Grade) ===")

csv_filename = 'ind_nifty500list.csv'
if not os.path.exists(csv_filename):
    raise FileNotFoundError(f"CRITICAL ERROR: Required CSV file '{csv_filename}' not found!")

try:
    df_symbols = pd.read_csv(csv_filename)
    if 'Symbol' not in df_symbols.columns or 'Industry' not in df_symbols.columns:
        raise ValueError("CRITICAL ERROR: 'Symbol' or 'Industry' column missing in CSV!")
    
    symbol_to_industry = {}
    for _, row in df_symbols.iterrows():
        sym = str(row['Symbol']).strip()
        ind = str(row['Industry']).strip()
        symbol_to_industry[sym] = ind if ind and ind != 'nan' else 'Others'
        
    symbols = [str(sym).strip() + ".NS" for sym in df_symbols['Symbol'].dropna().tolist()]
    print("TOTAL SYMBOLS:", len(symbols))
except Exception as e:
    raise RuntimeError(f"Failed to parse CSV file: {e}")

scanned_stocks = []
failed_count = 0
chunk_size = 50

for i in range(0, len(symbols), chunk_size):
    chunk = symbols[i:i + chunk_size]
    print(f"Processing chunk {i//chunk_size + 1}...")
    
    try:
        batch_data = yf.download(chunk, period="2mo", group_by='ticker', threads=True, progress=False)
        
        for ticker in chunk:
            try:
                raw_sym = ticker.replace('.NS', '')
                industry = symbol_to_industry.get(raw_sym, 'Others')
                
                if len(chunk) == 1:
                    df = batch_data
                else:
                    if ticker not in batch_data.columns.levels[0]:
                        failed_count += 1
                        continue
                    df = batch_data[ticker]
                
                if df.empty or len(df.dropna(subset=['Close'])) < 25:
                    failed_count += 1
                    continue
                
                df = df.dropna(subset=['Close', 'Volume'])
                
                current_price = float(df['Close'].iloc[-1])
                prev_close = float(df['Close'].iloc[-2])
                change_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0.0
                
                # 20-day Volume Average comparison
                vol_series = df['Volume']
                avg_vol_20 = float(vol_series.iloc[-21:-1].mean()) if len(vol_series) >= 21 else float(vol_series.mean())
                current_vol = float(vol_series.iloc[-1])
                volume_ratio = current_vol / avg_vol_20 if avg_vol_20 > 0 else 1.0
                
                # 30-Day Range metrics
                df_30 = df.iloc[-30:]
                high_30 = float(df_30['High'].max())
                low_30 = float(df_30['Low'].min())
                price_range_pct = ((high_30 - low_30) / low_30) * 100 if low_30 > 0 else 0.0
                near_high_pct = ((high_30 - current_price) / high_30) * 100
                
                # Smart Score Calculation (Multi-factor base)
                # Vol multiplier score + Momentum score + Range proximity
                vol_score_component = min(volume_ratio * 15, 40)
                momentum_component = min(max(change_pct, 0) * 10, 30)
                proximity_component = max(0, 30 - (near_high_pct * 2))
                smart_score = int(min(max(vol_score_component + momentum_component + proximity_component, 45), 98))
                
                scanned_stocks.append({
                    'symbol': raw_sym,
                    'name': raw_sym + ' Ltd',
                    'price': f"Rs. {current_price:,.2f}",
                    'change': f"{'+' if change_pct > 0 else ''}{change_pct:.2f}%",
                    'change_val': change_pct,
                    'category': industry,
                    'volume_ratio': round(volume_ratio, 1),
                    'volume_spike': f"{volume_ratio:.1f}x Avg",
                    'consolidation_range': f"{price_range_pct:.1f}% Range",
                    'range_val': price_range_pct,
                    'near_high_val': near_high_pct,
                    'smart_score': smart_score,
                    'why_selected': f"Vol: {volume_ratio:.1f}x | Chg: {change_pct:+.1f}%",
                    'date': datetime.now().strftime('%Y-%m-%d')
                })
            except Exception:
                failed_count += 1
    except Exception:
        failed_count += len(chunk)

print("SUCCESSFULLY DOWNLOADED:", len(scanned_stocks))

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
    print("TOTAL UPLOADED TO FIREBASE:", len(scanned_stocks))
    
