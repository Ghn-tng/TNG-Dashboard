#!/bin/bash
# push_to_github.sh

echo "🛠️ Đang chuẩn bị đẩy code lên GitHub..."

# 1. Khởi tạo Git nếu chưa có
if [ ! -d ".git" ]; then
    git init
    git branch -M main
fi

# 2. Thêm toàn bộ file (loại trừ file không cần thiết)
cat > .gitignore << EOF
backups/
*.xlsx
*.log
__pycache__/
.DS_Store
EOF

git add .
git commit -m "Khởi tạo Dashboard TNG online"

echo ""
echo "-------------------------------------------------------"
echo "BƯỚC TIẾP THEO RẤT QUAN TRỌNG:"
echo "1. Truy cập: https://github.com/new"
echo "2. Đặt tên Repository là: TNG-Dashboard"
echo "3. Nhấn nút 'Create repository'"
echo "4. Copy dòng lệnh 'git remote add origin ...' dán vào đây"
echo "-------------------------------------------------------"
echo ""

# Chờ người dùng nhập remote
read -p "Dán lệnh 'git remote add origin ...' vào đây: " remote_cmd
eval $remote_cmd

# Đẩy code lên
git push -u origin main

echo "✅ Hoàn tất! Bây giờ hãy vào Settings -> Pages trên GitHub để kích hoạt link."
