import os
import json
import random
import time
from datetime import datetime
import base64
import io
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import pandas as pd
import docx
import hashlib

# Elite Performance Tracking
CACHE_FILE = 'response_cache.json'
EXHAUSTED_KEYS = {} # key -> timestamp when it hit quota
RESPONSE_CACHE = {}

def load_cache():
    global RESPONSE_CACHE
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                RESPONSE_CACHE = json.load(f)
        except: RESPONSE_CACHE = {}

def save_cache():
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(RESPONSE_CACHE, f, ensure_ascii=False, indent=2)
    except: pass

load_cache()
LAST_WORKING_KEY_IDX = 0
CACHE_EXPIRY = 3600 # 1 hour for persistent cache

app = Flask(__name__)
CORS(app)

# Load API Keys
KEYS_FILE = 'GOOGLE_API_KEY.txt'
def get_keys():
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    return []

def get_compact_data(data, user_msg=""):
    """Giảm dung lượng dữ liệu tối đa để tiết kiệm Quota."""
    if not data: return {}
    
    # Chỉ lấy các thông tin thực sự cần thiết
    compact = {
        "report_date": data.get("report_date"),
        "gtc_vung": f"{data.get('grand_total_gtc', {}).get('gtc', 0)*100:.2f}%",
        "hr_total": data.get("ns_total", {}).get("so_thieu", 0),
    }
    
    # Map BC to AM for specific action proposals
    bc_to_am = {item.get('bc'): item.get('am') for item in data.get('gtc_bc', []) if item.get('bc')}
    
    raw_hotspots = sorted(data.get("canh_bao_vung", []), key=lambda x: x.get('gap', 0))[:7]
    enriched_hotspots = []
    for hs in raw_hotspots:
        hs_copy = hs.copy()
        hs_copy['am'] = bc_to_am.get(hs.get('bc'), "Chưa rõ AM")
        enriched_hotspots.append(hs_copy)

    compact["hotspots"] = enriched_hotspots
    
    # Load knowledge chỉ khi thực sự cần
    external_knowledge = ""
    if any(k in user_msg.lower() for k in ["ông", "anh", "chị", "liên hệ", "quy định"]):
        kb_path = 'Tai Lieu GHN/knowledge.json'
        if os.path.exists(kb_path):
            try:
                with open(kb_path, 'r') as f:
                    external_knowledge = f.read()[:1000]
            except: pass
    
    compact["kb"] = external_knowledge
    return compact

@app.route('/chat', methods=['POST'])
def chat():
    global LAST_WORKING_KEY_IDX, RESPONSE_CACHE
    
    req_data = request.json
    user_msg = req_data.get('message', '')
    history = req_data.get('history', [])
    files = req_data.get('files', []) # Danh sách base64 files
    
    if not user_msg and not files:
        return jsonify({"response": "Sếp ơi, Sếp chưa nhập nội dung câu hỏi ạ!", "status": "error"})

    # 1. Persistent Cache Check
    data_timestamp = ""
    try:
        if os.path.exists('data.json'):
            data_timestamp = str(os.path.getmtime('data.json'))
    except: pass
    
    cache_key = hashlib.md5(f"{user_msg}_{data_timestamp}".encode()).hexdigest()
    if cache_key in RESPONSE_CACHE:
        cached = RESPONSE_CACHE[cache_key]
        if time.time() - cached.get('time', 0) < CACHE_EXPIRY:
            return jsonify({"response": cached['response'], "status": "success"})

    # Load context data
    dashboard_data = {}
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r') as f:
                dashboard_data = json.load(f)
        except: pass

    compact_context = get_compact_data(dashboard_data, user_msg)
    
    # Load Style Guide
    style_guide = ""
    if os.path.exists('NGOCTRINH_STYLE_GUIDE.md'):
        try:
            with open('NGOCTRINH_STYLE_GUIDE.md', 'r') as f:
                style_guide = f.read()
        except: pass

    today_str = datetime.now().strftime('%d/%m/%Y')
    system_prompt = f"{style_guide}\nBạn là Ngọc Trinh, trợ lý điều hành cao cấp. Trả lời chuyên nghiệp, sắc sảo.\n\nTHÔNG TIN THỜI GIAN:\n- Hôm nay là ngày thực tế: **{today_str}**.\n- Tin tức xã hội PHẢI dùng ngày này.\n\nQUY TẮC CỐT LÕI (BẮT BUỘC):\n1. TIÊU ĐỀ CHÍNH: KHÔNG đánh số thứ tự.\n2. TIÊU ĐỀ NHỎ: Bắt đầu đánh số từ 1. (Dùng div hồng, margin-bottom: 2.5px).\n3. DANH SÁCH: Xuống dòng cho mỗi mục. Có ICON thì KHÔNG dùng dấu (•).\n4. ĐỊNH DẠNG: In đậm số liệu và tên tỉnh/BC. Mỗi ý 1 dòng riêng biệt.\n5. TÀI LIỆU: Sử dụng dữ liệu dưới đây.\n\nData: {json.dumps(compact_context, ensure_ascii=False)}"

    api_keys = get_keys()
    if not api_keys:
        return jsonify({"response": "Sếp ơi, em chưa thấy API Key trong file GOOGLE_API_KEY.txt ạ!", "status": "error"})

    # Rotate keys starting from the last working one
    last_error = ""
    rotated_keys = api_keys[LAST_WORKING_KEY_IDX:] + api_keys[:LAST_WORKING_KEY_IDX]
    
    for i, key in enumerate(rotated_keys):
        # Kiểm tra xem Key này có đang bị "cấm" do hết hạn mức không
        now = time.time()
        if key in EXHAUSTED_KEYS:
            if now - EXHAUSTED_KEYS[key] < 3600: # Cấm 1 tiếng
                continue
            else:
                del EXHAUSTED_KEYS[key]

        try:
            genai.configure(api_key=key)
            
            # Danh sách model tối ưu (Cập nhật cho 2026)
            models = [
                "gemini-3.1-flash-lite",
                "gemini-2.5-flash",
                "gemini-2.0-flash",
                "gemini-flash-latest",
                "gemini-pro-latest"
            ]
            
            model_instance = None
            last_model = globals().get('LAST_WORKING_MODEL')
            if last_model and last_model in models:
                models.remove(last_model)
                models.insert(0, last_model)

            for model_name in models:
                try:
                    m = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_prompt
                    )
                    model_instance = m
                    globals()['LAST_WORKING_MODEL'] = model_name
                    break
                except: continue
            
            if not model_instance: continue 

            formatted_history = []
            for h in history[-3:]: 
                role = "user" if h['role'] == 'user' else "model"
                formatted_history.append({"role": role, "parts": [h['content']]})
                
            chat_session = model_instance.start_chat(history=formatted_history)
            
            msg_parts = [user_msg]
            if files:
                for f in files:
                    mime = f.get('mime_type', 'unknown')
                    b64_data = f.get('data', '')
                    if 'image' in mime or 'pdf' in mime:
                        msg_parts.append({"inline_data": {"data": b64_data, "mime_type": mime}})
            
            response = chat_session.send_message(
                msg_parts,
                generation_config={"max_output_tokens": 1000, "temperature": 0.7}
            )
            
            LAST_WORKING_KEY_IDX = api_keys.index(key)
            
            # Lưu vào Cache
            RESPONSE_CACHE[cache_key] = {
                'response': response.text,
                'time': time.time()
            }
            save_cache()
            
            return jsonify({"response": response.text, "status": "success"})
            
        except Exception as e:
            last_error = str(e)
            if "429" in last_error or "quota" in last_error.lower():
                print(f"❌ Key {i+1} hết hạn mức, tạm thời loại bỏ.")
                EXHAUSTED_KEYS[key] = time.time()
                continue
            continue

    last_err_msg = str(last_error)
    hint = "Sếp ơi, hiện tại tất cả API Key đều đã hết hạn mức (Quota). Sếp có thể bổ sung thêm API Key mới vào file GOOGLE_API_KEY.txt nhé!"
    if "429" not in last_err_msg and "quota" not in last_err_msg.lower():
        hint = f"Lỗi kỹ thuật: {last_err_msg}. Sếp kiểm tra lại giúp em nhé!"
        
    return jsonify({
        "response": f"Sếp ơi, em đã thử {len(api_keys)} API Key nhưng chưa thành công. {hint}", 
        "status": "failed"
    }), 200

if __name__ == '__main__':
    print("🚀 Ngọc Trinh Chat Service starting on port 5005...")
    app.run(port=5005, host='0.0.0.0', debug=False)
