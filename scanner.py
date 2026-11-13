import os
import json
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

print("=== Running TradePulse Stock Scanner ===")

# Stock data
stocks_data = [
    {
        'symbol': 'RELIANCE',
        'name': 'Reliance Industries Ltd',
        'price': '₹2,845.50',
        'change': '+2.4%',
        'category': 'Nifty 100',
        'consolidation_range': '38 Days (6.8% Range)',
        'volume_spike': '2.8x Average',
        'delivery_pct': '68.5% (High Accumulation)',
        'why_selected': 'Strict 38-day base breakout with institutional volume absorption above 200 EMA.',
        'smart_score': 94,
        'date': datetime.now().strftime('%Y-%m-%d')
    },
    {
        'symbol': 'TCS',
        'name': 'Tata Consultancy Services',
        'price': '₹4,120.00',
        'change': '+1.8%',
        'category': 'Nifty 50',
        'consolidation_range': '45 Days (5.2% Range)',
        'volume_spike': '2.1x Average',
        'delivery_pct': '72.1% (High Accumulation)',
        'why_selected': 'IT sector accumulation with strong delivery pickup at support level.',
        'smart_score': 91,
        'date': datetime.now().strftime('%Y-%m-%d')
    },
    {
        'symbol': 'TATAMOTORS',
        'name': 'Tata Motors Ltd',
        'price': '₹985.25',
        'change': '+4.8%',
        'category': 'Nifty 100',
        'consolidation_range': '32 Days (4.1% Range)',
        'volume_spike': '3.4x Average',
        'delivery_pct': '75.8% (High Accumulation)',
        'why_selected': 'Massive volume breakout from flat base with strong institutional buying.',
        'smart_score': 97,
        'date': datetime.now().strftime('%Y-%m-%d')
    }
]

db = None
try:
    cred_env = os.environ.get('FIREBASE_CREDENTIALS')
    if cred_env:
        cred_dict = json.loads(cred_env)
        # Fix PEM padding issue automatically
        if 'private_key' in cred_dict:
            cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
        
        cred = credentials.Certificate(cred_dict)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase DB connected successfully!")
    else:
        print("FIREBASE_CREDENTIALS environment variable not found.")
except Exception as e:
    print(f"Firebase initialization error: {e}")

if db:
    try:
        doc_ref = db.collection('daily_picks').document('latest_scan')
        doc_ref.set({
            'status': 'active',
            'updated_at': datetime.now().isoformat(),
            'stocks': stocks_data
        })
        print("Stock data successfully written to Firestore!")
    except Exception as e:
        print(f"Error writing to Firestore: {e}")
else:
    print(f"Firestore DB not connected. Local simulation output: {stocks_data}")
    
