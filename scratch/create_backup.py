import os
import zipfile
from datetime import datetime

# 1. Clean old backups
backup_dir = "backups"
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

print("🗑️ Đang xóa các file backup cũ...")
for f in os.listdir(backup_dir):
    fpath = os.path.join(backup_dir, f)
    if os.path.isfile(fpath):
        os.remove(fpath)
        print(f"   Đã xóa: {f}")

# 2. Define backup filename
now_str = datetime.now().strftime("%Y%m%d_%H%M")
backup_filename = f"v_{now_str}_OPR_SHIFT_FIX.zip"
backup_path = os.path.join(backup_dir, backup_filename)

print(f"📦 Đang đóng gói phiên bản mới vào {backup_path}...")

# 3. Exclude list
exclude_dirs = {".git", "backups", "__pycache__", ".gemini", "scratch"}
exclude_files = {
    "cloudflared", "cloudflared.tgz", "ngrok.zip", 
    ".DS_Store", "response_cache.json"
}

with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk("."):
        # Modify dirs in-place to prevent os.walk from entering excluded dirs
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            # Check if file should be excluded
            if file in exclude_files:
                continue
            if file.endswith(".pyc") or file.endswith(".log"):
                continue
                
            filepath = os.path.join(root, file)
            # Remove leading './'
            arcname = os.path.relpath(filepath, ".")
            zipf.write(filepath, arcname)

print(f"✅ Hoàn tất sao lưu! File: {backup_filename}")
