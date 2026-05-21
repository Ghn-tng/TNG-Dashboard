import json
import sys
import os

# Ensure workspace is in path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

from chat_service import app

client = app.test_client()

def test_query(msg):
    print(f"\n==================== TESTING QUERY: {msg} ====================")
    response = client.post('/chat', json={
        'message': msg,
        'history': [],
        'files': []
    })
    res_data = response.get_json()
    print("STATUS:", res_data.get('status'))
    print("RESPONSE:")
    print(res_data.get('response'))

if __name__ == "__main__":
    # Test queries
    test_query("📊 Báo cáo OPR")
    test_query("Báo cáo tình hình nhân sự")
    test_query("Báo cáo chỉ số GTC")
