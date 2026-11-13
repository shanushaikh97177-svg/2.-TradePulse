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
    # (Aapki baaki bachi hui Nifty 500 stocks ki list yahan rahegi)
]

def run_institutional_scanner():
    scanned_stocks = []
    today_date = datetime.now().strftime('%Y-%m-%d')
    print("🚀 Scanning for Buy-Side Pre-Breakouts & Sell-Side Breakdowns...")

    for symbol in nifty_500_symbols:
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period="1y")
            
            if df.empty or len(df) < 200:
                continue

            current_price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-2])
            
            # FILTER: Price < ₹100 strictly rejected
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

            # Distance percentage check
            dist_50 = ((current_price - dma_50) / dma_50) * 100
            dist_100 = ((current_price - dma_100) / dma_100) * 100
            dist_200 = ((current_price - dma_200) / dma_200) * 100

            category = None
            reason = None

            # ---------------------------------------------------------
            # BUY SIDE (Approaching Breakout from below)
            # ---------------------------------------------------------
            if -2.0 <= dist_200 <= 1.0 and current_price >= dma_200:
                category = "Approaching 200 DMA (Buy)"
                reason = f"Pre-Breakout Radar: Only {abs(round(dist_200, 2))}% away from 200 DMA"
            elif -2.0 <= dist_100 <= 1.0 and current_price >= dma_100:
                category = "Approaching 100 DMA (Buy)"
                reason = f"Pre-Breakout Radar: Only {abs(round(dist_100, 2))}% away from 100 DMA"
            elif -2.0 <= dist_50 <= 1.0 and current_price >= dma_50:
                category = "Approaching 50 DMA (Buy)"
                reason = f"Pre-Breakout Radar: Only {abs(round(dist_50, 2))}% away from 50 DMA"

            # ---------------------------------------------------------
            # SELL SIDE (Approaching Breakdown / Support Breaking from above)
            # ---------------------------------------------------------
            elif -1.0 <= dist_200 <= 2.0 and current_price < dma_200:
                category = "Breakdown 200 DMA (Sell)"
                reason = f"Short Radar: Slipping below 200 DMA ({abs(round(dist_200, 2))}% close)"
            elif -1.0 <= dist_100 <= 2.0 and current_price < dma_100:
                category = "Breakdown 100 DMA (Sell)"
                reason = f"Short Radar: Slipping below 100 DMA ({abs(round(dist_100, 2))}% close)"
            elif -1.0 <= dist_50 <= 2.0 and current_price < dma_50:
                category = "Breakdown 50 DMA (Sell)"
                reason = f"Short Radar: Slipping below 50 DMA ({abs(round(dist_50, 2))}% close)"
            else:
                continue

            score = 65
            if volume_ratio > 1.5: 
                score += 20
            smart_score = min(score, 98)

            high_30d = float(df['Close'].tail(30).max())
            low_30d = float(df['Close'].tail(30).min())
            range_val = round(((high_30d - low_30d) / current_price) * 100, 2)

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
                "consolidation_range": f"{range_val}% Range",
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
        print(f"🎉 Success! Uploaded {len(scanned_stocks)} Buy & Sell side radar stocks.")
    else:
        print("⚠️ No stocks matched criteria today.")

if __name__ == "__main__":
    run_institutional_scanner()
    
