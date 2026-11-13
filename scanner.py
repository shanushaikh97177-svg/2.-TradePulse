import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime

cred_dict = {
    "type": "service_account",
    "project_id": "karigarhub-4be11",
    "private_key_id": "cb0bd4dd59fc973b4e633544baa07e198175e9d9",
    "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCbnjWQ9xxjsyI5
4hTm8384gal+DlezQUVvZglMM6J3U/7wfLp958i9GZe6PeVMcBzQBcRB47BMe4h2
8aB+Lu9NTOXAmeFHSTWRJ4M8put0gpCIOy+6kKaQSlMhMmjV0/Kf0ih7dHdV/YkK
3HUUu2kd2dJWNgeggnQUGy2rY0eU8RiDjt7cuN9VmM9Gj89bvwyly5UB2RaQBXbc
vC5NURuAW3RZewr6dLMMXXqDMPRIcW3XIFGGAq1EOJ115t43+P2Ua+IQFCgadn/T
MG4CuIjz6HIirROliR7ZlJHcHDLIQIQJmvRrW7ow2qn8e5LqXEdIxkQS2C1n96R9
w8kpqKbjAgMBAAECggEAEy9QfEQysEnjxM4N9KD9RKqbiipbfoJj/IVQTSAqfdqR
mfVOinoaQdHXZkL+M0u5CZ5EYTkgQXWTT9KfDh9cKiP6SSHPZ5nrbC86Wy5a5by4
88qUKkRt/GjlUbjkusPL7A8dJYcotSWyEPA30Ov/3AnACBfWHeAnTllBapktOHvF
ZmZwHx5twN3jMHnfBqO/Q7HV+CP2mM07pOaz43L9Hr+col39K+mWY4ydIZUtYkKv
LNjf91HIXNeK0OKh/C51c8xAHIeq6XHgheBbG/T9gkgCFyD57RcgGhkBp0ikNxFY
dK2jOoMEEkSC0PWtJjOie4aBOs2/hn+wbmEVQ8cxKQKBgQDM5xTaPWYTmh6Fpy3L
xzUZlQ0uqMuUnEclDxO5tP0s5eOfOJZxFtDX3zKz5nlb/gZ8+EN6+JWmyJPEpYua
J2R66Yd4zIMogSVy9n+kXZmfG1T8Si0m4KRYiqtTr01lXGA/xjos/ehzh0dnfwU6
97jOElcBI5KjpwWFF2Twmgw0ewKBgQDCbM+90fRk33/MjMQUU1J82ZvDQ+ezIogr
3zt3G/Onkts3dsWIWsimHYfIJIaUPKoLO0ldlptPwDq6ekkVLTmqN+J3JiNObYzf
bvP16kEqidaCmDlseVKvK8jiZ9wL/i4h0hnKm2765O9JWdEWGBjkinrVlFoTUpyC
++yBbmgOuQKBgDBi0TXIEfbHCjYdiF76p7tmyzodehWZ4eMKcGoGJ1MW5m2O+1ex
P5f6iQqafkYO8pFIPwcm9I/yBZMGVLUOYFf2FZudD8vc028WboXt5H0CA0ugaJEp
nsyWFeXfFic1JxyDIOqytONsvMtlp0V5faTCgfBM0x0gGBPOs1pVKi19JAoGBALZb
Uroqm7ylOHwFp7+cqyi4/fS20zJceDYWCfNcvzr0bjJmbz3GUJ4l4n4hbCzLfX5N
NDGwmfnCRhMzsSpwob567iltFv5vmArVSXLlBbw9TnptBqcsYBY2zhM08No6zNAh
/Njg0sX2Rk2ZNZgwf+CT1kRPAfFPscbVPW3kvSrZAoGBAMG/h+YukDHRu87HhAb3
6TWIJcTaqVL4OD7wx5PSC3gUcC0oRBLs/zytlVnYHXCvGVb27iZRSNgwX2BU1prj
nxK000Hu1UDwJ2m2A2yCDPQ2KUIR5aLvbrw3iOhLJ2kUNqLjWqGKsrVx38yULVpIe
S2PXvar9+52gCPSh9weNL9rS
-----END PRIVATE KEY-----""",
    "client_email": "firebase-adminsdk-fbsvc@karigarhub-4be11.iam.gserviceaccount.com",
    "client_id": "100875688108014463740",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40karigarhub-4be11.iam.gserviceaccount.com"
}

db = None
try:
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase Admin connected successfully!")
except Exception as e:
    print(f"Firebase initialization error: {e}")

print("=== Running TradePulse Stock Scanner ===")

scanned_stocks = [
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

if db:
    try:
        batch = db.batch()
        for stock in scanned_stocks:
            doc_ref = db.collection('daily_picks').document(stock['symbol'])
            batch.set(doc_ref, stock)
        batch.commit()
        print("Successfully saved scanned data to Firestore collection 'daily_picks'.")
    except Exception as e:
        print(f"Error saving to Firestore: {e}")
else:
    print(f"Firestore DB not connected. Local simulation output: {scanned_stocks}")

import os
import json
from firebase_admin import credentials, initialize_app

# GitHub Secret se JSON uthao
cred_env = os.environ.get('FIREBASE_CREDENTIALS')

if cred_env:
    cred_dict = json.loads(cred_env)
    # Yeh line ensure karegi ki private key ki padding kharab na ho
    if 'private_key' in cred_dict:
        cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
    
    cred = credentials.Certificate(cred_dict)
    initialize_app(cred)
    
