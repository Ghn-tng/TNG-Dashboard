import subprocess
import os
import re
import time
import sys
from datetime import datetime

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [Tunnel] {msg}", flush=True)

def start_tunnel():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    
    cf_path = os.path.join(base_dir, 'cloudflared')
    log_file = os.path.join(base_dir, 'tunnel_public.log')
    
    # 1. Check if cloudflared is running
    is_running = False
    try:
        ps = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'cloudflared tunnel --url' in ps.stdout:
            is_running = True
    except:
        pass

    if not is_running:
        log("🚀 Starting Cloudflare Tunnel...")
        cmd = [cf_path, 'tunnel', '--url', 'http://127.0.0.1:5005']
        with open(log_file, 'w') as f:
            subprocess.Popen(cmd, stdout=f, stderr=f, text=True)
    else:
        log("ℹ️ Tunnel is already running.")

    # 2. Extract URL from log (with polling/retries up to 15 seconds if starting new)
    url = None
    max_wait = 15 if not is_running else 2
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', content)
                if match:
                    url = match.group(0)
                    break
        time.sleep(0.5)

    if url:
        # 3. Check if bot_url.js needs update
        current_js = ""
        if os.path.exists('bot_url.js'):
            with open('bot_url.js', 'r', encoding='utf-8') as f:
                current_js = f.read()
        
        expected_js = f'window.BOT_URL = "{url}";'
        if current_js != expected_js:
            with open('bot_url.js', 'w', encoding='utf-8') as f:
                f.write(expected_js)
            log(f"✅ Updated bot_url.js with: {url}")
        else:
            log(f"✅ bot_url.js is already up to date: {url}")
    else:
        log("❌ Could not find public URL in log file. Try deleting tunnel_public.log and restarting.")

if __name__ == "__main__":
    start_tunnel()
