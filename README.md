# Project Sapient

> Ứng dụng quản lý công việc và năng suất cá nhân được xây dựng bằng Python với giao diện hiện đại.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## Mục Lục

- [Tổng Quan](#-tổng-quan)
- [Tính Năng](#-tính-năng)
- [Cài Đặt](#-cài-đặt)
- [Hướng Dẫn Sử Dụng](#-hướng-dẫn-sử-dụng)
- [Cấu Trúc Dự Án](#-cấu-trúc-dự-án)
- [Yêu Cầu Hệ Thống](#-yêu-cầu-hệ-thống)

---

## Tổng Quan

**Sapient** là một ứng dụng desktop đa chức năng giúp bạn quản lý công việc, theo dõi thời gian và tăng năng suất làm việc. Với giao diện người dùng hiện đại và thân thiện, Sapient cung cấp các công cụ cần thiết để tổ chức cuộc sống hàng ngày của bạn.

---

## Tính Năng

### **Trang Chủ (Home Dashboard)**

- **Lịch tương tác** - Xem và điều hướng qua các tháng, hiển thị các ngày có công việc
- **Tổng quan công việc** - Xem nhanh các công việc sắp tới, hôm nay và quá hạn
- **Thanh tìm kiếm** - Tìm kiếm nhanh trong ứng dụng
- **Recent Files** - Hiển thị các tệp đã mở gần đây

### **Quản Lý Công Việc (To-Do List)**

- **Thêm công việc** - Tạo công việc mới với tiêu đề và mô tả chi tiết
- **Đặt deadline** - Lịch popup tích hợp để chọn ngày hết hạn
- **Mức độ ưu tiên** - Phân loại công việc theo 3 mức: Low, Normal, High
- **Đánh dấu hoàn thành** - Toggle trạng thái hoàn thành/chưa hoàn thành
- **Chỉnh sửa công việc** - Click vào task để xem và chỉnh sửa chi tiết
- **Xóa công việc** - Xóa các công việc không cần thiết
- **Tìm kiếm** - Tìm kiếm công việc theo tiêu đề hoặc mô tả
- **Lưu trữ tự động** - Dữ liệu được lưu vào file JSON và đồng bộ với lịch

### **Bộ Đếm Thời Gian (Focus Timer)**

- Hỗ trợ các phương pháp tập trung như Pomodoro
- Theo dõi thời gian làm việc
- Thông báo khi hết thời gian

### **Quản Lý Tài Liệu (Document Manager)**

- Notepad tích hợp để ghi chú nhanh
- Quản lý và mở các tài liệu

### **Cài Đặt & Giao Diện**

| Tính năng | Mô tả |
|-----------|-------|
| **Dark Mode** | Chuyển đổi giữa giao diện sáng/tối |
| **Usage Tracking** | Theo dõi thời gian sử dụng ứng dụng |
| **Auto-save** | Tự động lưu dữ liệu và reset hàng ngày |
| **Theme Customization** | Bảng màu tùy chỉnh cho Light/Dark mode |

---

## Cài Đặt

### 1. Clone repository

```bash
git clone https://github.com/your-username/ProjectSapient.git
cd ProjectSapient-develop
```

### 2. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 3. Chạy ứng dụng

```bash
python main.py
```

---

## Hướng Dẫn Sử Dụng

### Điều Hướng

- ** SAPIENT** (Header) - Click để quay về trang chủ
- ** Document Manager** - Mở trình quản lý tài liệu
- ** Focus Timer** - Mở bộ đếm thời gian
- ** To do list** - Mở danh sách công việc
- ** Settings** - Mở cài đặt (góc dưới sidebar)

### Quản Lý Công Việc

1. Vào **To do list** từ sidebar
2. Click nút **+ Add New Task** để thêm công việc mới
3. Điền thông tin:
   - **Title**: Tiêu đề công việc
   - **Description**: Mô tả chi tiết
   - **Priority**: Chọn mức độ ưu tiên (Low/Normal/High)
   - **Deadline**: Chọn ngày hết hạn từ lịch
4. Click **Save** để lưu

### Xem Công Việc Theo Ngày

- Trên trang chủ, click vào bất kỳ ngày nào trên lịch
- Các ngày có công việc được đánh dấu bằng chấm cam
- Panel bên dưới sẽ hiển thị chi tiết các công việc trong ngày đó

---

## Cấu Trúc Dự Án

```
ProjectSapient-develop/
├── main.py              # File chính của ứng dụng
├── task_manager.py      # Module quản lý công việc (Singleton)
├── requirements.txt     # Dependencies
├── README.md           # Tài liệu dự án
│
├── notepad/            # Module Notepad
│   ├── __init__.py
│   └── applet.py
│
├── timer/              # Module Timer  
│   ├── __init__.py
│   └── applet.py
│
└── to_do_list/         # Module To-Do List
    ├── __init__.py
    └── applet.py
```

---

## Yêu Cầu Hệ Thống

- **Python**: 3.8 trở lên
- **Hệ điều hành**: Windows, macOS, Linux

### Dependencies

| Package | Phiên bản | Mô tả |
|---------|-----------|-------|
| `customtkinter` | ≥5.2.0 | Framework GUI hiện đại |
| `tkcalendar` | ≥1.6.1 | Widget lịch |
| `tkinter` | Built-in | GUI cơ bản (có sẵn trong Python) |

> **Lưu ý cho Linux**: Nếu thiếu tkinter, cài đặt bằng:
> - Ubuntu/Debian: `sudo apt-get install python3-tk`
> - Fedora: `sudo dnf install python3-tkinter`
> - Arch: `sudo pacman -S tk`

---

## Data Storage

Dữ liệu ứng dụng được lưu tại:

| Hệ điều hành | Đường dẫn |
|--------------|-----------|
| **Windows** | `%LOCALAPPDATA%/sapient/` |
| **macOS** | `~/Library/Application Support/sapient/` |
| **Linux** | `~/.config/sapient/` |

Files được lưu:
- `tasks.json` - Danh sách công việc
- `app_usage.json` - Thống kê sử dụng

---

## Screenshots

*Coming soon...*

---

## Changelog

### v1.0.0
- ✅ Trang chủ với lịch và tổng quan công việc
- ✅ Quản lý công việc đầy đủ (CRUD)
- ✅ Hỗ trợ Dark/Light mode
- ✅ Theo dõi thời gian sử dụng
- ✅ View caching cho hiệu suất tốt hơn

---

## Đóng Góp

Mọi đóng góp đều được chào đón! Hãy tạo Pull Request hoặc mở Issue nếu bạn có ý tưởng cải thiện.

---

## License


---

<p align="center">
  Made with ❤️ by Sapient Team
</p>
# Project Sapient


