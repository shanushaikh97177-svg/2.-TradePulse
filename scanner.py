import yfinance as yf
import pandas as pd
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# 1. Firebase Initialize (Apni JSON key file ka path yahan dein)
cred = credentials.Certificate("firebase_credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Nifty 500 Stocks ki list (Aap yahan apne saare 498-500 stocks ki list rakh sakte hain)
nifty_500_symbols = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", 
    "SBIN.NS", "BHARTIARTL.NS", "LICI.NS", "ITC.NS", "HINDUNILVR.NS",
    "AEGISVOPAK.NS", "AMBER.NS", "ANGELONE.NS", "ACE.NS", "AIAENG.NS",
    # ... (Aapki baaki bachi hui Nifty 500 stocks ki list)
]

def run_institutional_scanner():
    scanned_stocks = []
    today_date = datetime.now().strftime('%Y-%m-%d')
    print(f"🚀 Scanning {len(nifty_500_symbols)} stocks for Fresh Institutional Crossovers...")

    for symbol in nifty_500_symbols:
        try:
            # Historical data fetch karein (200 Days taaki Moving Average nikal sakein)
            stock = yf.Ticker(symbol)
            df = stock.history(period="1yr")
            
            if df.empty or len(df) < 200:
                continue

            # Latest day ka data
            current_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2]
            
            # ---------------------------------------------------------
            # FILTER 1: Price ₹100 se kam nahi honi chahiye
            # ---------------------------------------------------------
            if current_price < 100.0:
                continue

            current_volume = df['Volume'].iloc[-1]
            avg_volume_20 = df['Volume'].rolling(window=20).mean().iloc[-1]
            volume_ratio = round(current_volume / avg_volume_20, 2) if avg_volume_20 > 0 else 1.0
            
            change_val = round(((current_price - prev_price) / prev_price) * 100, 2)

            # Moving Averages calculate karein
            df['DMA50'] = df['Close'].rolling(window=50).mean()
            df['DMA100'] = df['Close'].rolling(window=100).mean()
            df['DMA200'] = df['Close'].rolling(window=200).mean()

            dma_50 = df['DMA50'].iloc[-1]
            prev_dma_50 = df['DMA50'].iloc[-2]
            
            dma_200 = df['DMA200'].iloc[-1]
            prev_dma_200 = df['DMA200'].iloc[-2]

            # ---------------------------------------------------------
            # FILTER 2: Strictly TODAY'S Crossover Check (Not past days)
            # ---------------------------------------------------------
            crossed_50dma_today = (prev_price <= prev_dma_50) and (current_price > dma_50)
            crossed_200dma_today = (prev_price <= prev_dma_200) and (current_price > dma_200)

            # Agar aaj inmein se koi crossover hua hai ya heavy volume breakout hai tabhi select karein
            if crossed_50dma_today or crossed_200dma_today or (volume_ratio >= 2.0 and change_val > 1.0):
                
                # Category aur Reason assign karna
                if crossed_200dma_today:
                    category = "Short-Term"
                    reason = "200 DMA Fresh Crossover (Long-term Bullish)"
                    smart_score = 88
                elif crossed_50dma_today:
                    category = "Swing"
                    reason = "50 DMA Momentum Crossover + Vol Spike"
                    smart_score = 82
                else:
                    category = "Intraday"
                    reason = f"Unusual Volume Spike ({volume_ratio}x vs Avg)"
                    smart_score = 75

                stock_info = stock.info
                stock_data = {
                    "symbol": symbol.replace(".NS", ""),
                    "name": stock_info.get('longName', symbol),
                    "price": f"Rs. {current_price:,.2f}",
                    "change": f"{'+' if change_val >= 0 else ''}{change_val}%",
                    "change_val": change_val,
                    "volume_ratio": volume_ratio,
                    "volume_spike": f"{volume_ratio}x Avg",
                    "smart_score": smart_score,
                    "category": category,
                    "why_selected": reason,
                    "consolidation_range": "Breakout Zone",
                    "scan_date": today_date
                }
                scanned_stocks.append(stock_data)
                print(f"✅ Selected: {symbol} | Price: {current_price} | Reason: {reason}")

        except Exception as e:
            print(f"Error processing {symbol}: {e}")

    # 3. Firebase par data save karein (Sirf pure aur filtered stocks)
    if scanned_stocks:
        db.collection('daily_picks').document('latest_scan').set({
            "date": today_date,
            "stocks": scanned_stocks,
            "total_count": len(scanned_stocks)
        })
        print(f"🎉 Success! Uploaded {len(scanned_stocks)} fresh institutional stocks to Firebase.")
    else:
        print("⚠️ No stocks matched today's strict criteria.")

if __name__ == "__main__":
    run_institutional_scanner()
    
