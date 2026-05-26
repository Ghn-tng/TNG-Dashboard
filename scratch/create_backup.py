import os
import zipfile
import shutil
from datetime import datetime

base_dir = "/Users/macbook/Downloads/GHN"
backup_dir = os.path.join(base_dir, "backups")

# 1. Delete old backups in backups/
print("=== DELETING OLD BACKUPS ===")
if os.path.exists(backup_dir):
    for filename in os.listdir(backup_dir):
        file_path = os.path.join(backup_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
                print(f"Deleted file: {filename}")
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                print(f"Deleted directory: {filename}")
        except Exception as e:
            print(f"Failed to delete {filename}: {e}")
else:
    os.makedirs(backup_dir)
    print("Created backups directory.")

# 2. Define zip filename using date & time
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
zip_filename = f"v_{timestamp}_BACKUP.zip"
zip_filepath = os.path.join(backup_dir, zip_filename)

# 3. Create zip file
print(f"\n=== CREATING NEW BACKUP: {zip_filename} ===")

# Exclude list
exclude_names = {
    ".git",
    "backups",
    "__pycache__",
    "cloudflared",
    "cloudflared.tgz",
    "ngrok.zip",
    ".DS_Store",
    "auto_refresh.log",
    "chat_service.log",
    "chat_service_manual.log",
    "chat_service_system.log",
    "dashboard_server.log",
    "data_repair.log",
    "http_server.log",
    "http_server_manual.log",
    "serveo.log",
    "tunnel.log",
    "tunnel_public.log"
}

with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(base_dir):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in exclude_names and not d.startswith(".")]
        
        for file in files:
            if file in exclude_names or file.startswith("."):
                continue
            if file == zip_filename: # Don't zip the zip file itself
                continue
                
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, base_dir)
            
            # Skip massive logs or temp files if any
            if file.endswith(".log") or file.endswith(".pyc"):
                continue
                
            zipf.write(abs_path, rel_path)
            print(f"Added to zip: {rel_path}")

print(f"\nBackup successfully created at: {zip_filepath}")
size_mb = os.path.getsize(zip_filepath) / (1024 * 1024)
print(f"Backup file size: {size_mb:.2f} MB")

# 4. Copy dashboard.html as dashboard_backup.html
print("\n=== COPYING DASHBOARD HTML BACKUP ===")
src_dashboard = os.path.join(base_dir, "dashboard.html")
dest_dashboard = os.path.join(backup_dir, "dashboard_backup.html")
if os.path.exists(src_dashboard):
    shutil.copy2(src_dashboard, dest_dashboard)
    print(f"Copied dashboard.html to backups/dashboard_backup.html")
else:
    print("Warning: dashboard.html not found, skipped HTML copy.")
