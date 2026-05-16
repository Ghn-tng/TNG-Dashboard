#!/bin/bash
# push_to_github.sh

echo "🛠️ Đang chuẩn bị đẩy code lên GitHub..."

# 1. Khởi tạo Git nếu chưa có
if [ ! -d ".git" ]; then
    git init
    git branch -M main
fi

# 2. Tạo .gitignore chuẩn bảo mật
cat > .gitignore << EOF
backups/
*.xlsx
*.log
__pycache__/
.DS_Store
# SECRETS
GOOGLE_API_KEY.txt
response_cache.json
data.json
data.js
history.json
gtc_prov_history.json
weather.json
tunnel_public.log
bot_url.js
*.plist
EOF

# 3. Đảm bảo Git "quên" các file nhạy cảm nếu lỡ add trước đó
git rm --cached GOOGLE_API_KEY.txt data.json data.js response_cache.json history.json gtc_prov_history.json weather.json tunnel_public.log 2>/dev/null || true

git add .
git commit -m "Bảo mật hóa Dashboard - Ẩn API Keys và Dữ liệu nhạy cảm"

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
