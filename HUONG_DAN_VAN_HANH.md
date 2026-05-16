# HƯỚNG DẪN VẬN HÀNH & NHẬT KÝ CÔNG VIỆC (WORK LOG)
## Hệ thống TNG Operational Dashboard V10.0

---

### 1. CẤU TRÚC HỆ THỐNG (FILE COMPONENTS)
Hệ thống được chia thành 3 lớp chính:

*   **Lớp Dữ liệu (Data Layer):**
    *   `auto_refresh.py`: Script cốt lõi tải dữ liệu từ Google Sheets, xử lý và làm mới Dashboard hàng giờ.
    *   `data.json` / `data.js`: Dữ liệu hiện tại của hệ thống.
    *   `history.json` / `gtc_prov_history.json`: Lưu trữ lịch sử KPI để vẽ biểu đồ xu hướng.
*   **Lớp Hiển thị (UI Layer):**
    *   `build_dashboard.py`: "Kiến trúc sư" xây dựng file HTML từ dữ liệu.
    *   `dashboard.html`: File Dashboard chính chạy tại máy local.
    *   `index.html`: Bản sao của Dashboard phục vụ cho link online trên GitHub.
*   **Lớp Trí tuệ & Kết nối (AI & Connectivity):**
    *   `chat_service.py`: Bộ não của Trợ lý Ngọc Trinh (Gemini 3.1 Pro).
    *   `start_tunnel.py`: Tạo đường truyền HTTPS bảo mật để Bot chat có thể dùng được online.
    *   `sync_to_github.py`: Tự động đẩy dữ liệu mới lên internet.

---

### 2. HƯỚNG DẪN VẬN HÀNH HÀNG NGÀY

#### ▶️ Cách khởi động hệ thống:
1.  Sếp chỉ cần chạy file: **`Launch_Dashboard.command`**.
2.  Hệ thống sẽ tự động bật Server, kiểm tra Bot chat và mở Dashboard trên trình duyệt cho Sếp.

#### 🔄 Cách cập nhật dữ liệu:
*   Hệ thống đã được thiết lập chạy ngầm (LaunchAgent). Dữ liệu sẽ tự động làm mới vào mỗi đầu giờ (7h, 8h, 9h...).
*   Sếp có thể theo dõi tiến trình tại file: `auto_refresh.log`.

---

### 3. QUY TRÌNH BẢO TRÌ & XỬ LÝ LỖI

#### 🔑 Cập nhật API Key (Năng lượng cho Ngọc Trinh):
*   Khi cần thêm Key mới, Sếp chỉ cần mở file **`GOOGLE_API_KEY.txt`** và dán Key mới vào dòng đầu tiên. Ngọc Trinh sẽ tự động nhận diện Key "xịn" nhất để dùng.

#### 🛠️ Xử lý lỗi "Không thể kết nối với dịch vụ chat":
1.  Thử nhấn **Cmd + Shift + R** để tải lại trang.
2.  Nếu vẫn lỗi, Sếp chạy file `start_tunnel.py` để làm mới đường truyền.

#### 🌐 Cập nhật link Online:
*   Mỗi khi Sếp thay đổi cấu hình hoặc dữ liệu, hãy chạy script `sync_to_github.py` để đẩy thay đổi lên link: [https://Ghn-tng.github.io/TNG-Dashboard/](https://Ghn-tng.github.io/TNG-Dashboard/)

---

### 4. NHẬT KÝ CÔNG VIỆC QUAN TRỌNG (LAST UPDATES)
*   **15/05/2026**: Nâng cấp Ngọc Trinh lên phiên bản **Gemini 3.1 Ultra Premium**.
*   **15/05/2026**: Thiết lập cơ chế nhận diện Vùng TNG thông minh (không dùng từ "của chúng ta" cho vùng khác).
*   **15/05/2026**: Tối ưu hóa toàn diện tốc độ load Dashboard và tính năng đồng bộ GitHub Pages.
*   **15/05/2026**: Hoàn thiện bộ sao lưu (Backup) cuối cùng cho dự án.

---
**Ghi chú**: Mọi tài liệu chi tiết và hướng dẫn phong cách của Ngọc Trinh được lưu tại file `NGOCTRINH_STYLE_GUIDE.md`. 💋
