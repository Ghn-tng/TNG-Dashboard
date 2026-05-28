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
    """Giảm dung lượng dữ liệu tối đa để tiết kiệm Quota nhưng vẫn đầy đủ các chỉ số cốt lõi."""
    if not data: return {}
    
    report_date = data.get("report_date")
    
    # 1. Chỉ số tổng quan Vùng TNG
    metrics_vung = {
        "gtc_vung": f"{data.get('grand_total_gtc', {}).get('gtc', 0)*100:.2f}%",
        "gtc_tts_vung": f"{data.get('grand_total_gtc_tts', {}).get('gtc', 0)*100:.2f}%",
        "opr_total": f"{data.get('opr_total', 0)*100:.2f}%",
        "hr_total_thieu": data.get("ns_total", {}).get("so_thieu", 0),
        "hr_total_can": data.get("ns_total", {}).get("ptt_can", 0),
        "hr_total_co": data.get("ns_total", {}).get("ptt_co", 0),
        "vol_total": data.get("grand_total_gtc", {}).get("vol", 0),
        "doanh_thu_luy_ke": f"{data.get('total_lay', {}).get('luyke', 0):,.0f}đ" if data.get('total_lay', {}).get('luyke') else "0đ"
    }

    # Map BC to AM for hotspot resolution
    bc_to_am = {item.get('bc'): item.get('am') for item in data.get('gtc_bc', []) if item.get('bc')}

    # 2. Chi tiết theo Tỉnh (Đắk Lắk, Gia Lai, Bình Định, Phú Yên)
    gtc_tinh_details = {}
    for item in data.get("gtc_tinh", []):
        t_name = item.get("tinh")
        if t_name:
            gtc_tinh_details[t_name] = f"{item.get('total_gtc', 0)*100:.2f}%"

    gtc_tts_tinh_details = {}
    for item in data.get("gtc_tts_tinh", []):
        t_name = item.get("tinh")
        if t_name:
            gtc_tts_tinh_details[t_name] = f"{item.get('total_gtc', 0)*100:.2f}%"

    opr_tinh_details = {}
    for proc in data.get("opr_tinh_report", {}).get("procs", []):
        t_name = proc.get("name")
        if t_name:
            for frame in proc.get("frames", []):
                if frame.get("name") == "Total":
                    vals = frame.get("vals", {})
                    val_data = vals.get(report_date) or {}
                    if not val_data and vals:
                        sorted_vals_dates = sorted(vals.keys())
                        if sorted_vals_dates:
                            val_data = vals.get(sorted_vals_dates[-1]) or {}
                    opr_tinh_details[t_name] = f"{val_data.get('opr', 0)*100:.2f}%"

    hr_tinh_details = {}
    for item in data.get("ns_bc", []):
        t_name = item.get("tinh")
        if t_name:
            if t_name not in hr_tinh_details:
                hr_tinh_details[t_name] = {"can": 0, "co": 0, "thieu": 0}
            hr_tinh_details[t_name]["can"] += item.get("can", 0)
            hr_tinh_details[t_name]["co"] += item.get("co", 0)
            hr_tinh_details[t_name]["thieu"] += item.get("thieu", 0)

    hr_tinh_formatted = {}
    for t_name, stats in hr_tinh_details.items():
        hr_tinh_formatted[t_name] = f"Cần: {stats['can']}, Có: {stats['co']}, Thiếu: {stats['thieu']}"

    tinh_details = {}
    for t_name in ["Đắk Lắk", "Gia Lai", "Bình Định", "Phú Yên"]:
        tinh_details[t_name] = {
            "gtc": gtc_tinh_details.get(t_name, "0.00%"),
            "gtc_tts": gtc_tts_tinh_details.get(t_name, "0.00%"),
            "opr": opr_tinh_details.get(t_name, "0.00%"),
            "hr": hr_tinh_formatted.get(t_name, "Cần: 0, Có: 0, Thiếu: 0")
        }

    # 3. Tổng hợp AM và mapping Tỉnh của từng AM
    am_to_tinh = {}
    for item in data.get("ns_bc", []):
        am_name = item.get("am")
        t_name = item.get("tinh")
        if am_name and t_name:
            am_to_tinh[am_name] = t_name

    am_details = {}
    for item in data.get("gtc_am", []):
        am_name = item.get("am")
        if am_name:
            am_details[am_name] = {
                "gtc": f"{item.get('total_gtc', 0)*100:.2f}%",
                "vol": item.get("total_vol", 0)
            }
    
    for item in data.get("ns_am", []):
        am_name = item.get("am")
        if am_name and am_name in am_details:
            am_details[am_name]["hr_thieu"] = item.get("so_thieu", 0)
            
    for item in data.get("ltc_am", []):
        am_name = item.get("am")
        if am_name and am_name in am_details:
            am_details[am_name]["ltc"] = f"{item.get('total_ltc', 0)*100:.2f}%"

    am_summary = [
        {
            "am": am_name,
            "tinh": am_to_tinh.get(am_name, "Chưa rõ"),
            "gtc": stats.get("gtc", "0.00%"),
            "ltc": stats.get("ltc", "0.00%"),
            "hr_thieu": stats.get("hr_thieu", 0)
        }
        for am_name, stats in am_details.items()
    ]

    # 4. Danh sách Hotspots
    raw_hotspots = sorted(data.get("canh_bao_vung", []), key=lambda x: x.get('gap', 0))[:7]
    enriched_hotspots = []
    for hs in raw_hotspots:
        hs_copy = hs.copy()
        hs_copy['am'] = bc_to_am.get(hs.get('bc'), "Chưa rõ AM")
        if 'gtc_7d' in hs_copy: hs_copy['gtc_7d'] = f"{hs_copy['gtc_7d']*100:.2f}%"
        if 'gtc_30d' in hs_copy: hs_copy['gtc_30d'] = f"{hs_copy['gtc_30d']*100:.2f}%"
        if 'target' in hs_copy: hs_copy['target'] = f"{hs_copy['target']*100:.2f}%"
        if 'gap' in hs_copy: hs_copy['gap'] = f"{hs_copy['gap']*100:.2f}%"
        enriched_hotspots.append(hs_copy)

    # 5. External knowledge
    external_knowledge = ""
    if any(k in user_msg.lower() for k in ["ông", "anh", "chị", "liên hệ", "quy định"]):
        kb_path = 'Tai Lieu GHN/knowledge.json'
        if os.path.exists(kb_path):
            try:
                with open(kb_path, 'r') as f:
                    external_knowledge = f.read()[:1000]
            except: pass

    return {
        "report_date": report_date,
        "metrics_vung": metrics_vung,
        "tinh_details": tinh_details,
        "am_summary": am_summary,
        "hotspots": enriched_hotspots,
        "kb": external_knowledge
    }

@app.route('/chat', methods=['POST'])
def chat():
    global LAST_WORKING_KEY_IDX, RESPONSE_CACHE
    
    req_data = request.json
    user_msg = req_data.get('message', '')
    history = req_data.get('history', [])
    files = req_data.get('files', []) # Danh sách base64 files
    
    if not user_msg and not files:
        return jsonify({"response": "Sếp ơi, Sếp chưa nhập nội dung câu hỏi ạ!", "status": "error"})


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
    system_prompt = f"""{style_guide}
Bạn là Ngọc Trinh, trợ lý điều hành cao cấp của Sếp Lê Văn Cường. Trả lời chuyên nghiệp, sắc sảo, cực kỳ quyết liệt và khó tính về mặt thẩm mỹ.

THÔNG TIN THỜI GIAN:
- Hôm nay là ngày thực tế: **{today_str}**.
- Tin tức xã hội PHẢI dùng ngày này.

QUY TẮC PHÂN BỔ AM (BẮT BUỘC):
- Mỗi AM chỉ thuộc quản lý của một Tỉnh duy nhất. Sếp yêu cầu tuyệt đối tuân thủ theo trường `tinh` được cung cấp trong `am_summary` để xác định tỉnh/khu vực của AM đó.
- CẤM TUYỆT ĐỐI gán sai tỉnh cho AM! Ví dụ: AM **Nguyễn Công Luận** thuộc tỉnh **Gia Lai**, AM **Nguyễn Văn Sáng** thuộc tỉnh **Đắk Lắk**, AM **Lê Văn Tài** thuộc tỉnh **Đắk Lắk**. Tuyệt đối không được nhầm lẫn!

QUY TẮC PHÂN BIỆT VÀ BÁO CÁO CÁC CHỈ SỐ (BẮT BUỘC):
1. **BÁO CÁO OPR (Báo cáo OPR TTS)**:
   - Khi Sếp hỏi về OPR, click "Báo cáo OPR", hoặc hỏi chỉ số OPR: Bạn PHẢI trả lời về chỉ số OPR, tuyệt đối KHÔNG trả lời GTC!
   - Sử dụng `metrics_vung.opr_total` làm chỉ số OPR Vùng TNG.
   - Sử dụng `tinh_details[Tỉnh].opr` làm chỉ số OPR của từng tỉnh (Đắk Lắk, Gia Lai, Bình Định, Phú Yên).
   - Giải thích OPR là Tỷ lệ Đúng giờ tạo đơn / On-time Processing Rate.

2. **BÁO CÁO NHÂN SỰ (HR)**:
   - Sử dụng `metrics_vung.hr_total_thieu` làm Số thiếu nhân sự, `metrics_vung.hr_total_can` làm Số cần, và `metrics_vung.hr_total_co` làm Số đang có.
   - Sử dụng `tinh_details[Tỉnh].hr` làm chỉ số nhân sự từng tỉnh.
   - TUYỆT ĐỐI KHÔNG báo cáo "Số thiếu" thành "Tổng nhân sự hiện tại". Tổng nhân sự hiện tại phải là số "Đang có" (Co). Ví dụ: "Tổng nhân sự đang có của vùng là {compact_context.get('metrics_vung', {}).get('hr_total_co', 0)} nhân sự, hiện đang thiếu hụt {compact_context.get('metrics_vung', {}).get('hr_total_thieu', 0)} nhân sự".
   - LƯU Ý ĐẶC BIỆT QUAN TRỌNG: Chỉ số `metrics_vung.hr_total_thieu` (ví dụ: 50) là số thiếu của TOÀN VÙNG (gồm cả 4 tỉnh: Đắk Lắk, Gia Lai, Bình Định, Phú Yên). Khi đưa ra đề xuất hay báo cáo liên quan đến số thiếu này, TUYỆT ĐỐI KHÔNG ĐƯỢC gán hoặc quy kết số thiếu này là riêng của Đắk Lắk và Gia Lai (hoặc bất kỳ tỉnh lẻ nào). Phải nêu rõ đây là "nhân sự còn thiếu của toàn vùng" hoặc "nhân sự còn thiếu trên toàn vùng TNG".

3. **BÁO CÁO GTC VÀ GTC TTS**:
   - GTC Vùng (Giao thành công Vùng): Sử dụng `metrics_vung.gtc_vung` và `tinh_details[Tỉnh].gtc`.
   - GTC TTS Vùng (Giao tự tuyển Vùng): Sử dụng `metrics_vung.gtc_tts_vung` và `tinh_details[Tỉnh].gtc_tts`.

QUY TẮC CỐT LÕI VỀ TRÌNH BÀY (BẮT BUỘC):
1. TIÊU ĐỀ CHÍNH: KHÔNG đánh số thứ tự. Viết HOA TOÀN BỘ, IN ĐẬM, dùng mã màu hồng và margin-bottom: 2.5px. Mẫu code: `<div style="color:#db2777; font-weight:bold; margin-top:10px; margin-bottom:2.5px; font-size:16px;">TIÊU ĐỀ CHÍNH</div>`.
2. TIÊU ĐỀ NHỎ: Đánh số từ 1. Viết HOA, IN ĐẬM, màu hồng và margin-bottom: 2.5px. Mẫu code: `<div style="color:#db2777; font-weight:bold; margin-top:0.5px; margin-bottom:2.5px; font-size:15px;">1. TIÊU ĐỀ NHỎ</div>`.
3. DANH SÁCH: Xuống dòng cho mỗi mục. Nếu có ICON thì CẤM DÙNG dấu (•). Nếu KHÔNG có icon mới dùng dấu (•).
4. ĐỊNH DẠNG: In đậm tất cả số liệu (phần trăm %, số lượng) và tên Tỉnh/Bưu cục.
5. CẤU TRÚC 4 PHẦN CHO BÁO CÁO VẬN HÀNH: 1. ĐÁNH GIÁ CHUNG, 2. TÌNH HÌNH CHI TIẾT & ĐIỂM NÓNG, 3. DỰ BÁO RỦI RO, 4. PHƯƠNG ÁN & ĐỀ XUẤT HÀNH ĐỘNG. Luôn liệt kê đủ 4 tỉnh: Đắk Lắk, Gia Lai, Bình Định, Phú Yên trong Đánh giá chung.
6. YÊU CẦU BÁO CÁO ĐIỂM NÓNG (BẮT BUỘC): Trong phần '2. TÌNH HÌNH CHI TIẾT & ĐIỂM NÓNG', PHẢI cung cấp đầy đủ chi tiết số liệu cụ thể của từng điểm nóng (chỉ số GTC 7 ngày, mục tiêu, độ lệch/gap), ghi rõ điểm nóng đó thuộc bưu cục nào (tên bưu cục đầy đủ) và dưới quyền quản lý của AM nào, đồng thời nêu rõ cụ thể lỗi/vấn đề điểm nóng ở đây là gì (ví dụ: GTC sụt giảm nghiêm trọng so với mục tiêu, tỷ lệ đúng giờ processing thấp, hay thiếu hụt nhân sự ở mức báo động). Tuyệt đối CẤM báo cáo chung chung thiếu số liệu hoặc thiếu thông tin AM/bưu cục!

Data: {json.dumps(compact_context, ensure_ascii=False)}"""

    # 1. Persistent Cache Check based on user message and prompt content hash (to auto-invalidate on code/data updates)
    prompt_hash = hashlib.md5(system_prompt.encode()).hexdigest()
    cache_key = hashlib.md5(f"{user_msg}_{prompt_hash}".encode()).hexdigest()
    if cache_key in RESPONSE_CACHE:
        cached = RESPONSE_CACHE[cache_key]
        if time.time() - cached.get('time', 0) < CACHE_EXPIRY:
            return jsonify({"response": cached['response'], "status": "success"})

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
                generation_config={"max_output_tokens": 8192, "temperature": 0.7}
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

@app.route('/save_key', methods=['POST'])
def save_key():
    try:
        req_data = request.json or {}
        key = req_data.get('key', '').strip()
        if not key:
            return jsonify({"response": "Mã khóa API trống, Sếp vui lòng nhập lại nhé!", "status": "error"}), 400
        
        # Write securely to GOOGLE_API_KEY.txt
        with open('GOOGLE_API_KEY.txt', 'w', encoding='utf-8') as f:
            f.write(key + '\n')
            
        print("✅ Đã lưu API Key mới thành công vào GOOGLE_API_KEY.txt")
        return jsonify({"response": "Đã lưu API Key thành công!", "status": "success"})
    except Exception as e:
        print(f"❌ Lỗi khi lưu API Key: {e}")
        return jsonify({"response": f"Không thể lưu key: {str(e)}", "status": "error"}), 500

if __name__ == '__main__':
    print("🚀 Ngọc Trinh Chat Service starting on port 5005...")
    app.run(port=5005, host='0.0.0.0', debug=False)
