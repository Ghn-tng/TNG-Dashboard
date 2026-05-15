import http.server
import socketserver
import os
import socket
import subprocess
import sys

import time

def ensure_chat_service():
    """Đảm bảo dịch vụ chat đang chạy trên cổng 5005."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        if s.connect_ex(('127.0.0.1', 5005)) != 0:
            print("⚠️ Chat Service chưa chạy, đang kích hoạt...")
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 1. Thử kích hoạt qua LaunchAgent (Thiết lập vĩnh viễn)
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.ghn.chat_service.plist")
            if os.path.exists(plist_path):
                subprocess.run(["launchctl", "load", plist_path], stderr=subprocess.DEVNULL)
                time.sleep(1) # Đợi một lát
            
            # 2. Kiểm tra lại, nếu vẫn chưa chạy thì dùng fallback
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
                s2.settimeout(0.5)
                if s2.connect_ex(('127.0.0.1', 5005)) != 0:
                    script_path = os.path.join(base_dir, 'chat_service.py')
                    subprocess.Popen([sys.executable, script_path], 
                                     cwd=base_dir,
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
                    print("🚀 Đã chạy fallback chat_service.py")

# Kích hoạt dịch vụ
ensure_chat_service()

PORT = 5001
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path.endswith('dashboard.html') or self.path == '/':
            ensure_chat_service()
        super().do_GET()

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Server Ngọc Trinh phục vụ tại Port {PORT}")
    httpd.serve_forever()
