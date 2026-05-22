import http.server
import socketserver
import os
import socket
import subprocess
import sys

import time

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

# Kích hoạt dịch vụ
ensure_chat_service()

PORT = 5001
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # Mọi truy cập đều kích hoạt kiểm tra dịch vụ chat
        ensure_chat_service()
        if self.path in ['/ping', '/wakeup']:
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"success","message":"Ngoc Trinh is awake!"}')
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
