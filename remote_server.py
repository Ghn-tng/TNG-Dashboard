import http.server
import socketserver
import os
import socket
import subprocess
import sys
import time
import re
import json

def ensure_chat_service():
    """Đảm bảo dịch vụ chat đang chạy trên cổng 5005."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(('127.0.0.1', 5005)) == 0:
                return # Đã chạy, ok
            
            print("⚠️ Ngọc Trinh đang nghỉ ngơi, đang gọi dậy ngay...")
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 1. Thử kích hoạt qua LaunchAgent
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.ghn.chat_service.plist")
            if os.path.exists(plist_path):
                # Unload trước để đảm bảo refresh trạng thái nếu đang bị lỗi (status 78)
                subprocess.run(["launchctl", "unload", plist_path], stderr=subprocess.DEVNULL)
                subprocess.run(["launchctl", "load", plist_path], stderr=subprocess.DEVNULL)
                time.sleep(1)
            
            # 2. Kiểm tra lại, nếu vẫn chưa chạy thì dùng fallback trực tiếp
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
                s2.settimeout(0.5)
                if s2.connect_ex(('127.0.0.1', 5005)) != 0:
                    script_path = os.path.join(base_dir, 'chat_service.py')
                    subprocess.Popen([sys.executable, script_path], 
                                     cwd=base_dir,
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
                    print("🚀 Đã kích hoạt Ngọc Trinh (Fallback mode)")
    except Exception as e:
        print(f"❌ Lỗi khi khởi động Chat Service: {e}")

def ensure_tunnel():
    """Đảm bảo tunnel đang chạy và bot_url.js đã được cập nhật/đồng bộ."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        start_tunnel_script = os.path.join(base_dir, 'start_tunnel.py')
        
        # Đọc nội dung bot_url.js hiện tại
        js_before = ""
        bot_url_path = os.path.join(base_dir, 'bot_url.js')
        if os.path.exists(bot_url_path):
            with open(bot_url_path, 'r', encoding='utf-8') as f:
                js_before = f.read()

        # Chạy start_tunnel.py để kiểm tra/khởi động tunnel và cập nhật bot_url.js
        print("🔄 Đang kiểm tra Cloudflare Tunnel...")
        subprocess.run([sys.executable, start_tunnel_script], cwd=base_dir)
        
        # Đọc nội dung bot_url.js sau khi chạy start_tunnel.py
        js_after = ""
        if os.path.exists(bot_url_path):
            with open(bot_url_path, 'r', encoding='utf-8') as f:
                js_after = f.read()
                
        # Nếu bot_url.js thay đổi (tức là có tunnel mới hoặc url mới), thực hiện đồng bộ lên GitHub
        if js_before != js_after and js_after:
            print("🚀 Phát hiện URL mới cho Ngọc Trinh, đang tự động đồng bộ lên GitHub...")
            sync_script = os.path.join(base_dir, 'sync_to_github.py')
            # Chạy sync_to_github.py bất đồng bộ để tránh chặn phản hồi wakeup của server
            subprocess.Popen([sys.executable, sync_script], cwd=base_dir)
    except Exception as e:
        print(f"❌ Lỗi khi khởi động/đồng bộ Tunnel: {e}")

def get_current_tunnel_url():
    """Đọc URL tunnel hiện tại từ bot_url.js."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        bot_url_path = os.path.join(base_dir, 'bot_url.js')
        if os.path.exists(bot_url_path):
            with open(bot_url_path, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', content)
                if match:
                    return match.group(0)
    except Exception as e:
        print(f"❌ Lỗi khi đọc URL tunnel: {e}")
    return None

# Kích hoạt dịch vụ
ensure_chat_service()
ensure_tunnel()

PORT = 5001
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # Mọi truy cập đều kích hoạt kiểm tra dịch vụ chat và tunnel
        ensure_chat_service()
        ensure_tunnel()
        
        if self.path in ['/ping', '/wakeup']:
            bot_url = get_current_tunnel_url()
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response_data = {
                "status": "success",
                "message": "Ngoc Trinh is awake!",
                "bot_url": bot_url
            }
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return
        super().do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Server Ngọc Trinh phục vụ tại Port {PORT}")
    httpd.serve_forever()
