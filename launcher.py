import os
import sys
import socket
import subprocess
import time
import webbrowser
import shutil

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0

def setup_system_services(base_dir):
    """Thiết lập các dịch vụ chạy ngầm vĩnh viễn trên macOS."""
    plist_files = ["com.ghn.chat_service.plist", "com.ghn.dashboard.refresh.plist", "com.ghn.dashboard.server.plist"]
    dest_dir = os.path.expanduser("~/Library/LaunchAgents")
    
    # Tạo thư mục nếu chưa có
    os.makedirs(dest_dir, exist_ok=True)

    for plist_filename in plist_files:
        src_plist = os.path.join(base_dir, plist_filename)
        dest_plist = os.path.join(dest_dir, plist_filename)

        if not os.path.exists(src_plist):
            print(f"⚠️ Không tìm thấy file {plist_filename}, bỏ qua...")
            continue

        # Kiểm tra xem đã cài đặt chưa hoặc có thay đổi không
        should_install = True
        if os.path.exists(dest_plist):
            with open(src_plist, 'r') as f1, open(dest_plist, 'r') as f2:
                if f1.read() == f2.read():
                    should_install = False

        if should_install:
            print(f"🛠️  Đang thiết lập dịch vụ {plist_filename}...")
            try:
                shutil.copy2(src_plist, dest_plist)
                # Load service using modern launchctl bootstrap
                uid = os.getuid()
                domain = f"gui/{uid}"
                subprocess.run(["launchctl", "bootout", domain, dest_plist], stderr=subprocess.DEVNULL)
                subprocess.run(["launchctl", "bootstrap", domain, dest_plist], check=True)
                print(f"✅ Đã lưu {plist_filename} vào hệ thống.")
            except Exception as e:
                print(f"⚠️ Không thể thiết lập dịch vụ {plist_filename}: {e}")
        else:
            # Vẫn đảm bảo dịch vụ đã được load
            uid = os.getuid()
            domain = f"gui/{uid}"
            subprocess.run(["launchctl", "bootstrap", domain, dest_plist], stderr=subprocess.DEVNULL)


def launch():
    # Sử dụng đường dẫn tuyệt đối của thư mục chứa file launcher.py
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("🌟 Đang chuẩn bị hệ thống Ngọc Trinh...")

    # 0. Thiết lập các dịch vụ hệ thống (Chạy ngầm vĩnh viễn)
    setup_system_services(base_dir)


    # 1. Khởi động Chat Service (Cổng 5005)
    # Nếu chưa dùng cổng 5005, thử kích hoạt qua launchctl hoặc chạy thủ công
    if not is_port_in_use(5005):
        print("🚀 Đang kích hoạt Chat Service...")
        dest_plist = os.path.expanduser("~/Library/LaunchAgents/com.ghn.chat_service.plist")
        if os.path.exists(dest_plist):
            uid = os.getuid()
            domain = f"gui/{uid}"
            subprocess.run(["launchctl", "bootstrap", domain, dest_plist], stderr=subprocess.DEVNULL)
        
        # Nếu vẫn chưa chạy (có thể do load rồi nhưng đang start), đợi một chút
        # Hoặc chạy fallback nếu launchctl không khả dụng
        if not is_port_in_use(5005):
            chat_script = os.path.join(base_dir, 'chat_service.py')
            subprocess.Popen([sys.executable, chat_script], 
                             cwd=base_dir,
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
        
        # Đợi một chút để service kịp khởi động
        for _ in range(15):
            if is_port_in_use(5005):
                break
            time.sleep(0.5)
    
    if is_port_in_use(5005):
        print("✅ Ngọc Trinh Chat Service đã sẵn sàng (Port 5005).")
    else:
        print("❌ Lỗi: Không thể khởi động Chat Service.")
 
    # 2. Khởi động Dashboard Server (Cổng 5001)
    if not is_port_in_use(5001):
        print("🌐 Đang kích hoạt Dashboard Server...")
        dest_plist = os.path.expanduser("~/Library/LaunchAgents/com.ghn.dashboard.server.plist")
        if os.path.exists(dest_plist):
            uid = os.getuid()
            domain = f"gui/{uid}"
            subprocess.run(["launchctl", "bootstrap", domain, dest_plist], stderr=subprocess.DEVNULL)
        
        # Nếu vẫn chưa chạy, chạy fallback
        if not is_port_in_use(5001):
            server_script = os.path.join(base_dir, 'remote_server.py')
            subprocess.Popen([sys.executable, server_script], 
                             cwd=base_dir,
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
        
        for _ in range(10):
            if is_port_in_use(5001):
                break
            time.sleep(0.5)
 
    if is_port_in_use(5001):
        print("✅ Dashboard Server đã sẵn sàng (Port 5001).")
    else:
        print("❌ Lỗi: Không thể khởi động Dashboard Server.")

    # 3. Mở Trình duyệt
    # Ưu tiên mở qua localhost để đảm bảo tính năng hoạt động đầy đủ
    url = "http://localhost:5001/dashboard.html"
    print(f"🖥️  Đang mở Dashboard tại: {url}")
    webbrowser.open(url)
    
    print("\n🎉 Chúc Sếp một ngày làm việc hiệu quả và tràn đầy năng lượng!")
    time.sleep(2)

if __name__ == "__main__":
    launch()
