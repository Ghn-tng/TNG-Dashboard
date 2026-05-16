import subprocess
import os
import sys
from datetime import datetime

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [GitHub Sync] {msg}", flush=True)

def sync():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    
    # 1. Update index.html from dashboard.html
    if os.path.exists('dashboard.html'):
        try:
            with open('dashboard.html', 'r', encoding='utf-8') as f:
                content = f.read()
            with open('index.html', 'w', encoding='utf-8') as f:
                f.write(content)
            log("📄 Updated index.html from dashboard.html")
        except Exception as e:
            log(f"❌ Failed to update index.html: {e}")
            return

    # 2. Check if there are changes to commit
    try:
        # Add files
        files_to_sync = ['index.html', 'dashboard.html', 'data.json', 'data.js', 'history.json', 'gtc_prov_history.json', 'weather.json', 'bot_url.js']
        # Filter only existing files
        existing_files = [f for f in files_to_sync if os.path.exists(f)]
        
        subprocess.run(['git', 'add'] + existing_files, check=True)
        
        # Check if anything is staged
        status = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True).stdout
        if not status:
            log("😴 No changes to sync.")
            return

        # 3. Commit and Push
        commit_msg = f"Auto-update Dashboard: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        
        # Force push to gh-pages branch
        log("🚀 Pushing to GitHub (gh-pages)...")
        result = subprocess.run(['git', 'push', 'origin', 'gh-pages'], capture_output=True, text=True)
        
        if result.returncode == 0:
            log("✅ Successfully synced to GitHub Pages!")
            log(f"🔗 Link: https://Ghn-tng.github.io/TNG-Dashboard/")
        else:
            log(f"❌ Push failed: {result.stderr}")

    except subprocess.CalledProcessError as e:
        log(f"❌ Git operation failed: {e}")
    except Exception as e:
        log(f"❌ Unexpected error during sync: {e}")

if __name__ == "__main__":
    sync()
