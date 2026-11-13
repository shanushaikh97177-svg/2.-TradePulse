            # Moving Averages Calculation
            df['DMA50'] = df['Close'].rolling(window=50).mean()
            df['DMA100'] = df['Close'].rolling(window=100).mean()
            df['DMA200'] = df['Close'].rolling(window=200).mean()

            dma_50 = float(df['DMA50'].iloc[-1])
            dma_100 = float(df['DMA100'].iloc[-1])
            dma_200 = float(df['DMA200'].iloc[-1])

            # Distance percentage check (Price DMA se kitna paas hai)
            # Jaise price DMA se 2% niche ya upar ho
            dist_50 = ((current_price - dma_50) / dma_50) * 100
            dist_100 = ((current_price - dma_100) / dma_100) * 100
            dist_200 = ((current_price - dma_200) / dma_200) * 100

            category = None
            reason = None

            # Agar price 200 DMA ke -2% se +1% ke beech hai (Yani paas aa raha hai)
            if -2.0 <= dist_200 <= 1.0:
                category = "Approaching 200 DMA"
                reason = f"Pre-Breakout Radar: Only {abs(round(dist_200, 2))}% away from 200 DMA"
            elif -2.0 <= dist_100 <= 1.0:
                category = "Approaching 100 DMA"
                reason = f"Pre-Breakout Radar: Only {abs(round(dist_100, 2))}% away from 100 DMA"
            elif -2.0 <= dist_50 <= 1.0:
                category = "Approaching 50 DMA"
                reason = f"Pre-Breakout Radar: Only {abs(round(dist_50, 2))}% away from 50 DMA"
            else:
                continue # Agar paas nahi hai toh skip kar do
