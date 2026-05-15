import os
import json
import re
import subprocess

def verify():
    errors = []
    print("🚀 Bắt đầu kiểm tra hệ thống...")

    # 1. Check Data Files
    for f in ['data.json', 'history.json', 'weather.json']:
        if not os.path.exists(f):
            errors.append(f"Thiếu file dữ liệu quan trọng: {f}")
        else:
            try:
                with open(f, 'r', encoding='utf-8') as jf:
                    json.load(jf)
                print(f"✅ File {f}: Hợp lệ")
            except Exception as e:
                errors.append(f"File {f} bị lỗi cấu trúc JSON: {str(e)}")

    # 2. Check Build Script
    print("🔄 Đang chạy thử build_dashboard.py...")
    try:
        result = subprocess.run(['python3', 'build_dashboard.py'], capture_output=True, text=True)
        if result.returncode != 0:
            errors.append(f"build_dashboard.py gặp lỗi khi chạy: {result.stderr}")
        else:
            print("✅ build_dashboard.py: Chạy thành công")
    except Exception as e:
        errors.append(f"Không thể chạy build_dashboard.py: {str(e)}")

    # 3. Check Dashboard Integrity
    if os.path.exists('dashboard.html'):
        with open('dashboard.html', 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check for leaked formatting strings
            leaks = re.findall(r'\{[a-z_\[\]"]+\}', content)
            # Filter out things that might be valid CSS or JS but look like python variables
            # Common leaks: {x["am"]}, {money(n1)}, {day_cells}
            leaked_vars = [l for l in leaks if any(word in l for word in ['x[', 'money(', 'cells', 'num(', 'pct('])]
            if leaked_vars:
                errors.append(f"Phát hiện rò rỉ mã nguồn Python trong HTML: {list(set(leaked_vars))}")
            
            # Check for chart canvases
            canvases = re.findall(r'<canvas id="(.+?)"', content)
            expected_charts = ['chartGtc', 'chartKD', 'chartNS', 'chartKDTrend']
            for chart in expected_charts:
                if chart not in canvases:
                    errors.append(f"Thiếu biểu đồ quan trọng: {chart}")
            
            # Check for tables
            tables = re.findall(r'<table id="(.+?)"', content)
            if len(tables) < 5:
                errors.append(f"Số lượng bảng dữ liệu quá ít ({len(tables)}), nghi ngờ mất dữ liệu")
            
            print(f"✅ dashboard.html: Kiểm tra cấu trúc hoàn tất (Biểu đồ: {len(canvases)}, Bảng: {len(tables)})")
    else:
        errors.append("Không tìm thấy file dashboard.html sau khi build")

    # 4. Check Chat Service
    print("📡 Kiểm tra dịch vụ Chat...")
    try:
        # Check if port 5005 is active
        res = subprocess.run(['lsof', '-i', ':5005'], capture_output=True, text=True)
        if not res.stdout:
            errors.append("Dịch vụ chat_service.py (Port 5005) chưa khởi động")
        else:
            print("✅ chat_service.py: Đang hoạt động")
    except:
        pass

    if errors:
        print("\n❌ PHÁT HIỆN LỖI HỆ THỐNG:")
        for err in errors:
            print(f"   - {err}")
        return False
    else:
        print("\n✨ HỆ THỐNG HOÀN HẢO! Không phát hiện lỗi nào.")
        return True

if __name__ == "__main__":
    verify()
