import yfinance as yf
import pandas as pd
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase Initialize
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

nifty_500_symbols = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", 
    "SBIN.NS", "BHARTIARTL.NS", "LICI.NS", "ITC.NS", "HINDUNILVR.NS",
    "AEGISVOPAK.NS", "AMBER.NS", "ANGELONE.NS", "ACE.NS", "AIAENG.NS",
    # (Apni baaki bachi hui Nifty 500 stocks ki list yahan rakhein)
]

def run_institutional_scanner():
    scanned_stocks = []
    today_date = datetime.now().strftime('%Y-%m-%d')
    print(f"🚀 Scanning for Fresh 50/100/200 DMA Crossovers...")

    for symbol in nifty_500_symbols:
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period="1yr") # 200 DMA ke liye 1 saal ka data zaroori hai
            
            if df.empty or len(df) < 200:
                continue

            current_price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-2])
            
            # FILTER 1: Price < ₹100 strictly rejected
            if current_price < 100.0:
                continue

            current_volume = float(df['Volume'].iloc[-1])
            avg_volume_20 = float(df['Volume'].rolling(window=20).mean().iloc[-1])
            volume_ratio = round(current_volume / avg_volume_20, 2) if avg_volume_20 > 0 else 1.0
            
            change_val = round(((current_price - prev_price) / prev_price) * 100, 2)

            # Moving Averages Calculation
            df['DMA50'] = df['Close'].rolling(window=50).mean()
            df['DMA100'] = df['Close'].rolling(window=100).mean()
            df['DMA200'] = df['Close'].rolling(window=200).mean()

            dma_50 = float(df['DMA50'].iloc[-1])
            dma_100 = float(df['DMA100'].iloc[-1])
            dma_200 = float(df['DMA200'].iloc[-1])
            
            prev_dma_50 = float(df['DMA50'].iloc[-2])
            prev_dma_100 = float(df['DMA100'].iloc[-2])
            prev_dma_200 = float(df['DMA200'].iloc[-2])

            # FILTER 2: Fresh DMA Crossover Check (Aaj price DMA ke upar gaya ho)
            crossed_50 = (current_price >= dma_50) and (prev_price < prev_dma_50)
            crossed_100 = (current_price >= dma_100) and (prev_price < prev_dma_100)
            crossed_200 = (current_price >= dma_200) and (prev_price < prev_dma_200)

            # Agar kisi bhi DMA ka fresh crossover nahi hai, toh skip kar do
            if not (crossed_50 or crossed_100 or crossed_200):
                continue

            # Category & Reason determination
            if crossed_200:
                category = "200 DMA Breakout"
                reason = "Major Trend Reversal: Crossed 200 DMA Today"
            elif crossed_100:
                category = "100 DMA Breakout"
                reason = "Medium-Term Bullish Shift: Crossed 100 DMA Today"
            else:
                category = "50 DMA Breakout"
                reason = "Short-Term Momentum: Crossed 50 DMA Today"

            # Smart Score calculation
            score = 60
            if volume_ratio > 1.5: score += 20
            if change_val > 2.0: score += 15
            smart_score = min(score, 98)

            stock_info = stock.info
            stock_data = {
                "symbol": symbol.replace(".NS", ""),
                "name": stock_info.get('longName', symbol.replace(".NS", "")),
                "price": f"Rs. {current_price:,.2f}",
                "change": f"{'+' if change_val >= 0 else ''}{change_val}%",
                "change_val": float(change_val),
                "volume_ratio": float(volume_ratio),
                "volume_spike": f"{volume_ratio}x Avg",
                "smart_score": int(smart_score),
                "category": category,
                "why_selected": reason,
                "scan_date": today_date
            }
            scanned_stocks.append(stock_data)

        except Exception as e:
            print(f"Error processing {symbol}: {e}")

    if scanned_stocks:
        db.collection('daily_picks').document('latest_scan').set({
            "date": today_date,
            "stocks": scanned_stocks,
            "total_count": len(scanned_stocks)
        })
        print(f"🎉 Success! Uploaded {len(scanned_stocks)} pure DMA crossover stocks.")
    else:
        print("⚠️ No stocks matched DMA crossover criteria today.")

if __name__ == "__main__":
    run_institutional_scanner()
    
