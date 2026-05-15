import os
import json
import random
import time
import base64
import io
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import pandas as pd
import docx
import hashlib

# Elite Performance Tracking
RESPONSE_CACHE = {}
LAST_WORKING_KEY_IDX = 0
CACHE_EXPIRY = 300 # 5 minutes

app = Flask(__name__)
CORS(app)

# Load API Keys
KEYS_FILE = 'GOOGLE_API_KEY.txt'
def get_keys():
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    return []

def get_compact_data(data):
    """Giảm dung lượng dữ liệu gửi cho AI và tiền xử lý số liệu địa phương."""
    if not data: return {}
    
    # 1. Tiền xử lý số liệu địa phương (Local Analytics Engine)
    provinces = {
        "Đắk Lắk": ["Nguyễn Văn Sáng", "Nguyễn Thị Bảo Nhi", "Lê Văn Tài", "Nguyễn  Ngọc Hà", "Mai Đức Hoàng Long", "Nguyễn  Hoàng Anh", "Đặng Văn Dũng"],
        "Gia Lai": ["Nguyễn Công Luận", "Nguyễn Đình Trung", "Ngô  Thị Bích Trâm", "Phan Thị Mỹ Chi"],
        "Bình Định": ["Phan Thanh Thức", "Võ Thanh Diệu", "Trần Nhật Thương"],
        "Phú Yên": ["Huỳnh Thị Mới", "Lê Trọng Khiêm"]
    }
    
    prov_stats = {}
    am_data = {x['am']: x for x in data.get('gtc_am', [])}
    
    for prov, am_list in provinces.items():
        total_vol = 0
        total_gtc_vol = 0
        for am in am_list:
            if am in am_data:
                item = am_data[am]
                total_vol += item.get('total_vol', 0)
                total_gtc_vol += item.get('total_vol', 0) * item.get('total_gtc', 0)
        
        if total_vol > 0:
            prov_stats[prov] = {
                "vol": int(total_vol),
                "gtc": f"{round(total_gtc_vol / total_vol * 100, 2)}%"
            }
    
    # 2. Load External Knowledge (Folder: Tai Lieu GHN)
    external_knowledge = ""
    kb_path = 'Tai Lieu GHN'
    if os.path.exists(kb_path):
        for file in os.listdir(kb_path):
            fpath = os.path.join(kb_path, file)
            try:
                if file.endswith('.json'):
                    with open(fpath, 'r') as f:
                        external_knowledge += f"\n[Knowledge {file}]:\n{f.read()}\n"
                elif file.endswith('.docx'):
                    doc = docx.Document(fpath)
                    text = "\n".join([p.text for p in doc.paragraphs])
                    external_knowledge += f"\n[Knowledge {file}]:\n{text}\n"
                elif file.endswith('.xlsx'):
                    df = pd.read_excel(fpath)
                    external_knowledge += f"\n[Knowledge {file}]:\n{df.to_markdown(index=False)}\n"
            except: pass
    
    # 3. Phân tích rủi ro (Risk Analysis for BCs)
    risk_bc = sorted(data.get('canh_bao_vung', []), key=lambda x: x.get('gap', 0))[:5]
    
    # 4. Thu gọn dữ liệu gửi đi (Token Optimization)
    compact = {
        "timestamp": data.get("timestamp"),
        "prov_stats": prov_stats,
        "gtc_vung": f"{data.get('grand_total_gtc', {}).get('gtc', 0)*100:.2f}%",
        "canh_bao_top": [{**x, 'gap': f"{x.get('gap',0)*100:.2f}%"} for x in data.get("canh_bao_vung", [])[:10]],
        "risk_forecast": risk_bc,
        "hr_summary": data.get("ns_total"),
        "hr_top_missing": sorted(data.get("ns_bc", []), key=lambda x: x.get('thieu', 0), reverse=True)[:5],
        "external_kb": external_knowledge
    }
    return compact

@app.route('/chat', methods=['POST'])
def chat():
    global LAST_WORKING_KEY_IDX
    
    req_data = request.json
    user_msg = req_data.get('message', '')
    history = req_data.get('history', [])
    files = req_data.get('files', []) # Danh sách base64 files
    
    if not user_msg and not files:
        return jsonify({"response": "Sếp ơi, Sếp chưa nhập nội dung câu hỏi ạ!", "status": "error"})

    # Check Cache
    data_timestamp = ""
    try:
        if os.path.exists('data.json'):
            data_timestamp = str(os.path.getmtime('data.json'))
    except: pass
    
    cache_key = hashlib.md5(f"{user_msg}_{data_timestamp}".encode()).hexdigest()
    if cache_key in RESPONSE_CACHE:
        cached = RESPONSE_CACHE[cache_key]
        if time.time() - cached['time'] < CACHE_EXPIRY:
            print("🚀 Trả lời từ Cache (Ngọc Trinh Super Speed)")
            return jsonify({"response": cached['response'], "status": "success"})

    # Load context data
    dashboard_data = {}
    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r') as f:
                dashboard_data = json.load(f)
        except: pass

    compact_context = get_compact_data(dashboard_data)
    
    # Load Style Guide
    style_guide = ""
    if os.path.exists('NGOCTRINH_STYLE_GUIDE.md'):
        with open('NGOCTRINH_STYLE_GUIDE.md', 'r') as f:
            style_guide = f.read()

    system_prompt = f"""
{style_guide}

Bối cảnh dữ liệu Dashboard Vùng Tây Nguyên hiện tại:
{json.dumps(compact_context, indent=2, ensure_ascii=False)}

HƯỚNG DẪN QUAN TRỌNG:
1. Bạn là Ngọc Trinh, trợ lý điều hành của Sếp.
2. Luôn trả lời theo phong cách Executive, thông minh và quyến rũ.
3. Với câu hỏi Vận hành: Sử dụng dữ liệu compact_context ở trên, phân tích sâu, tìm Hotspots và đề xuất hành động theo cấu trúc 4 phần (1. Đánh giá chung, 2. Điểm nóng, 3. Dự báo rủi ro, 4. Đề xuất).
   - MỤC ĐỀ XUẤT: Phải có sự LIÊN KẾT CHẶT CHẼ giữa Điểm nóng (xử lý ngay cái sai) và Dự báo rủi ro (ngăn chặn cái sắp sai). Ưu tiên các hành động quyết liệt cho các bưu cục xuất hiện ở cả 2 mục.
   - MỤC DỰ BÁO RỦI RO: Sử dụng dữ liệu risk_forecast. Cảnh báo sớm xu hướng. CẤM TUYỆT ĐỐI dùng bảng markdown (|) hoặc bất kỳ ký tự gạch dọc nào. Hãy viết bằng văn bản (text) bình thường, đúng văn phong Executive, liệt kê các bưu cục và vấn đề một cách tự nhiên.
4. Với câu hỏi Ngoài Vận hành:
   - Trả lời đúng trọng tâm, văn phong Executive, quyến rũ.
5. Quy tắc Trình bày & Màu sắc: 
   - CHỈ tiêu đề các phần (1, 2, 3...) dùng màu Hồng (#db2777). 
   - **BẮT BUỘC Highlight**: Phải **IN ĐẬM** (`**`) toàn bộ số liệu, **TÊN TỈNH**, **TÊN BƯU CỤC** và các từ khóa quan trọng, nhưng giữ màu **ĐEN**.
   - Các số liệu tỷ lệ (GTC, OPR, ODR...) PHẢI trình bày đúng định dạng % (Ví dụ: 74.15% thay vì 0.7415).
   - Dãn dòng thoáng, tăng khoảng cách giữa các phần báo cáo. Tuy nhiên, TUYỆT ĐỐI KHÔNG để dòng trống ngay sau Tiêu đề. Khoảng cách Tiêu đề và nội dung phải cực kỳ hẹp.
   - Tên Tỉnh và Tên Bưu cục: PHẢI hiển thị **IN ĐẬM** và ĐẦY ĐỦ (Ví dụ: **Đắk Lắk**, **Gia Lai**, **Bưu cục 123 Hùng Vương-Quy Nhơn-Bình Định**). Cấm tuyệt đối việc viết tắt hoặc rút gọn.
   - Luôn sử dụng dấu (•) và ngắt dòng dứt khoát cho từng ý phân tích. Mỗi ý phải là một dòng riêng biệt.
6. Quy tắc Phân biệt Vùng (QUAN TRỌNG):
   - Sếp của bạn là Giám đốc Vùng Tây Nguyên (Vùng TNG). Đây là "Vùng của chúng ta".
   - Các vùng khác (Ví dụ: Vùng HNO - Hà Nội, Vùng HCM...) là các đơn vị độc lập, không thuộc quyền quản lý của Sếp.
   - Cấm tuyệt đối dùng từ "của chúng ta" khi nói về các vùng khác (Ví dụ: KHÔNG ĐƯỢC nói "Vùng HNO của chúng ta"). 
   - Coi các GĐV (Giám đốc Vùng) khác là đồng nghiệp ngang hàng của Sếp, tôn trọng nhưng phân định ranh giới rõ ràng.
9. Nếu Sếp gửi file hoặc hình ảnh, hãy phân tích nội dung đó kết hợp với dữ liệu Dashboard hoặc Kiến thức bên ngoài nếu cần.
"""

    api_keys = get_keys()
    if not api_keys:
        return jsonify({"response": "Sếp ơi, em chưa thấy API Key trong file GOOGLE_API_KEY.txt ạ!", "status": "error"})

    # Rotate keys starting from the last working one
    last_error = ""
    rotated_keys = api_keys[LAST_WORKING_KEY_IDX:] + api_keys[:LAST_WORKING_KEY_IDX]
    
    for i, key in enumerate(rotated_keys):
        try:
            genai.configure(api_key=key)
            
            # Ưu tiên các model mới nhất và ổn định nhất dựa trên list_models thực tế
            # Danh sách model tối ưu (Ưu tiên Flash 1.5 để tốc độ nhanh và hạn mức cao)
            models = [
                "gemini-2.5-pro", 
                "gemini-2.5-flash",
                "gemini-2.0-flash",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-3.1-flash-lite",
                "gemini-pro-latest",
                "gemini-flash-latest"
            ]
            
            model_instance = None
            for model_name in models:
                try:
                    # 1. Thử khởi tạo model với Google Search (Grounding)
                    try:
                        m = genai.GenerativeModel(
                            model_name=model_name,
                            system_instruction=system_prompt,
                            tools=[{"google_search_retrieval": {}}]
                        )
                        # Test thử một tin nhắn ngắn
                        test_chat = m.start_chat(history=[])
                        test_chat.send_message("hi", generation_config={"max_output_tokens": 1})
                        model_instance = m
                        print(f"✅ Đã kết nối với {model_name} (Có Google Search)")
                        break
                    except Exception as e_tool:
                        # 2. Nếu lỗi tool, thử khởi tạo model bình thường (Internal knowledge)
                        print(f"⚠️ Model {model_name} không hỗ trợ Search Tool, thử mode thường...")
                        m = genai.GenerativeModel(
                            model_name=model_name,
                            system_instruction=system_prompt
                        )
                        test_chat = m.start_chat(history=[])
                        test_chat.send_message("hi", generation_config={"max_output_tokens": 1})
                        model_instance = m
                        print(f"✅ Đã kết nối với {model_name} (Internal Knowledge)")
                        break
                except Exception as e:
                    # print(f"      - Model {model_name} lỗi: {str(e)[:50]}...")
                    continue
            
            if not model_instance:
                print(f"⚠️ Key {i+1} không tìm thấy model nào khả dụng. Đang thử key tiếp theo...")
                last_error = "Không có model nào khả dụng cho key này (có thể hết quota hoặc bị hạn chế vùng)"
                continue # Thử key tiếp theo thay vì return ngay

            # Nếu đã tìm thấy model_instance, tiến hành chat chính thức
            # Convert history format - Optimized to last 5 messages
            formatted_history = []
            for h in history[-5:]: 
                role = "user" if h['role'] == 'user' else "model"
                formatted_history.append({"role": role, "parts": [h['content']]})
                
            chat_session = model_instance.start_chat(history=formatted_history)
            
            # Xử lý tin nhắn kèm file/hình ảnh
            msg_parts = [user_msg]
            if files:
                print(f"📎 Nhận được {len(files)} file đính kèm:")
                for f in files:
                    mime = f.get('mime_type', 'unknown')
                    b64_data = f.get('data', '')
                    size = len(b64_data) * 0.75 / 1024 # Approx KB
                    print(f"  - MIME: {mime} | Size: {size:.1f} KB")
                    
                    try:
                        # 1. Native Multimodal (Images & PDF)
                        if 'image' in mime or 'pdf' in mime:
                            msg_parts.append({
                                "inline_data": {
                                    "data": b64_data,
                                    "mime_type": mime
                                }
                            })
                        
                        # 2. Document Processing (Word, Excel, Text)
                        else:
                            file_bytes = base64.b64decode(b64_data)
                            extracted_text = ""
                            
                            if 'word' in mime or 'officedocument.wordprocessingml' in mime:
                                doc = docx.Document(io.BytesIO(file_bytes))
                                extracted_text = f"\n[Nội dung file Word]:\n" + "\n".join([p.text for p in doc.paragraphs])
                            
                            elif 'excel' in mime or 'spreadsheet' in mime or 'csv' in mime:
                                if 'csv' in mime:
                                    df = pd.read_csv(io.BytesIO(file_bytes))
                                else:
                                    df = pd.read_excel(io.BytesIO(file_bytes))
                                extracted_text = f"\n[Dữ liệu file Excel/CSV]:\n{df.to_markdown(index=False)}"
                            
                            elif 'text/plain' in mime:
                                extracted_text = f"\n[Nội dung file Text]:\n{file_bytes.decode('utf-8')}"
                            
                            if extracted_text:
                                msg_parts[0] += f"\n\n--- FILE ATTACHED ---\n{extracted_text}\n--- END FILE ---"
                                print(f"  ✅ Đã trích xuất text từ file ({len(extracted_text)} ký tự)")
                            else:
                                print(f"  ⚠️ Không thể trích xuất text cho MIME: {mime}")

                    except Exception as fe:
                        print(f"  ❌ Lỗi xử lý file ({mime}): {str(fe)}")
                
            response = chat_session.send_message(msg_parts)
            
            # Cập nhật key đang hoạt động tốt nhất
            LAST_WORKING_KEY_IDX = api_keys.index(key)
            
            # Lưu vào Cache
            RESPONSE_CACHE[cache_key] = {
                'response': response.text,
                'time': time.time()
            }
            
            return jsonify({
                "response": response.text,
                "status": "success"
            })
            
        except Exception as e:
            last_error = str(e)
            print(f"❌ Lỗi với API Key {i+1}: {last_error}")
            # Nếu là lỗi quota, tiếp tục thử key khác
            if "quota" in last_error.lower() or "429" in last_error:
                continue
            # Nếu là lỗi nghiêm trọng khác nhưng vẫn còn key, cũng tiếp tục thử
            continue

    last_err_msg = str(last_error)
    if "429" in last_err_msg or "quota" in last_err_msg.lower():
        hint = "Sếp ơi, hiện tại tất cả API Key đều đã hết hạn mức (Quota). Sếp vui lòng: 1. Đợi khoảng 1-2 phút rồi thử lại. 2. Hoặc bổ sung thêm API Key mới vào file GOOGLE_API_KEY.txt nhé!"
    else:
        hint = f"Lỗi cuối cùng: {last_err_msg}. Sếp kiểm tra lại giúp em nhé!"

    return jsonify({
        "response": f"Sếp ơi, em đã thử tất cả {len(api_keys)} API Key nhưng chưa thành công. {hint}", 
        "status": "failed"
    }), 200

if __name__ == '__main__':
    print("🚀 Ngọc Trinh Chat Service starting on port 5005...")
    app.run(port=5005, host='0.0.0.0', debug=False)
