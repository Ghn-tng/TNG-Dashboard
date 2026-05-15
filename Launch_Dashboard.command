#!/bin/bash
# Chuyển đến thư mục chứa file này
cd "$(dirname "$0")"

clear
echo "==========================================="
echo "   HỆ THỐNG DASHBOARD NGỌC TRINH V10.0"
echo "==========================================="
echo ""

# Chạy script launcher
python3 launcher.py

# Để cửa sổ terminal lại nếu có lỗi, hoặc đóng nếu mọi thứ ok
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Có lỗi xảy ra. Vui lòng kiểm tra lại!"
    read -p "Nhấn Enter để đóng..."
fi
