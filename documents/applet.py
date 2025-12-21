"""
================================================================================
DOCUMENT MANAGEMENT APPLET - PHÂN HỆ QUẢN LÝ TÀI LIỆU
================================================================================
Mô tả: Module quản lý tài liệu với giao diện Master-Detail Layout
Tác giả: Project Sapient Team
Phiên bản: 1.0

CẤU TRÚC FILE:
=============
1. IMPORTS & DEPENDENCIES (Dòng 1-34)
   - Thư viện giao diện: customtkinter, tkinter
   - Xử lý file: json, os, filedialog
   - PDF rendering: PyMuPDF (fitz), Pillow (PIL)

2. CLASS DocumentApplet (Dòng 36-897)
   - __init__: Khởi tạo applet, layout, theme
   - Data Management: load_notes, save_notes, get_data_path
   - LEFT PANEL: Danh sách tài liệu với search & filter
   - RIGHT PANEL: Hiển thị nội dung (PDF hoặc Note)
   - SPLIT VIEW: Chế độ xem song song PDF + Note
   - ACTIONS: CRUD operations cho documents

CÁC CHỨC NĂNG CHÍNH (Functional Requirements):
=============================================
- FR-DCM-01: Quản lý danh sách tài liệu (Left Panel)
- FR-DCM-02: Đọc tài liệu (Read Mode) - Right Panel  
- FR-DCM-03: Ghi chép & Chỉnh sửa (Write/Edit Note)
- FR-DCM-04: Split View - Xem PDF và ghi chú song song
================================================================================
"""

# ============================================================================
# PHẦN 1: IMPORTS - THƯ VIỆN CẦN THIẾT
# ============================================================================

import customtkinter as ctk      # Thư viện UI chính (CustomTkinter)
import tkinter as tk            # Tkinter gốc cho một số widget
from tkinter import filedialog, messagebox  # Dialog chọn file, hộp thoại
import json                     # Đọc/ghi dữ liệu JSON
import os                       # Thao tác hệ điều hành
import subprocess               # Chạy lệnh hệ thống (mở file bằng app mặc định)
import platform                 # Xác định hệ điều hành
from datetime import datetime   # Xử lý ngày tháng
from pathlib import Path        # Thao tác đường dẫn file

# ----------------------------------------------------------------------------
# KIỂM TRA THƯ VIỆN PDF (PYMUPDF)
# PyMuPDF (fitz) được dùng để render PDF thành hình ảnh
# Nếu không có, tính năng xem PDF sẽ bị vô hiệu hóa
# ----------------------------------------------------------------------------
try:
    import fitz  # PyMuPDF - thư viện xử lý PDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False  # Đánh dấu là không có thư viện PDF

# ----------------------------------------------------------------------------
# KIỂM TRA THƯ VIỆN HÌNH ẢNH (PILLOW)
# PIL được dùng để chuyển đổi hình ảnh từ PDF sang định dạng hiển thị
# ----------------------------------------------------------------------------
try:
    from PIL import Image, ImageTk  # Pillow - xử lý hình ảnh
    HAS_PIL = True
except ImportError:
    HAS_PIL = False  # Đánh dấu là không có thư viện hình ảnh


# ============================================================================
# PHẦN 2: CLASS CHÍNH - DOCUMENT APPLET
# ============================================================================

class DocumentApplet:
    """
    Lớp chính quản lý Document Applet với layout Master-Detail
    
    Cấu trúc giao diện:
    ┌──────────────────────────────────────────────────────┐
    │                 MAIN CONTAINER                        │
    │  ┌─────────────┐  ┌───────────────────────────────┐  │
    │  │ LEFT PANEL  │  │        RIGHT PANEL            │  │
    │  │             │  │                               │  │
    │  │ - Search    │  │  - Title Entry                │  │
    │  │ - Doc List  │  │  - Content (PDF/Note)         │  │
    │  │ - Add (+)   │  │  - Control Bar                │  │
    │  │             │  │                               │  │
    │  └─────────────┘  └───────────────────────────────┘  │
    └──────────────────────────────────────────────────────┘
    """
    
    def __init__(self, parent):
        """
        Khởi tạo Document Applet
        
        Args:
            parent: Widget cha (CTkFrame) chứa applet này
        """
        self.parent = parent
        self.name = "Document Manager"  # Tên hiển thị của applet
        
        # ====================================================================
        # KHỞI TẠO THƯ MỤC LƯU TRỮ DỮ LIỆU
        # Dữ liệu được lưu trong thư mục cấu hình của ứng dụng
        # ====================================================================
        self.data_dir = self.get_data_path()           # Đường dẫn thư mục data
        self.notes_file = self.data_dir / "notes.json" # File JSON lưu notes
        
        # Tải dữ liệu đã lưu từ file
        self.notes = self.load_notes()
        
        # ====================================================================
        # BIẾN TRẠNG THÁI (STATE VARIABLES)
        # Theo dõi trạng thái hiện tại của applet
        # ====================================================================
        self.current_note = None       # Note đang được hiển thị
        self.current_pdf_page = 0      # Trang PDF hiện tại (cho phân trang)
        self.pdf_doc = None            # Đối tượng tài liệu PDF (PyMuPDF)
        self.pdf_images = []           # Danh sách ảnh các trang PDF đã render
        self.is_split_mode = False     # Có đang ở chế độ Split View không
        self.search_var = None         # Biến StringVar cho ô tìm kiếm
        
        # ====================================================================
        # ĐỊNH NGHĨA THEME (MÀU SẮC)
        # Hỗ trợ cả hai chế độ: Dark Mode và Light Mode
        # ====================================================================
        self.themes = {
            # ------------------------
            # DARK THEME - Chế độ tối
            # ------------------------
            'dark': {
                'bg': '#2E253A',              # Nền chính (Deep Purple đậm)
                'panel_bg': '#403355',        # Nền panel (Purple nhạt hơn)
                'card_bg': '#C8C8C8',         # Nền card danh sách (Xám bạc)
                'card_fg': '#2E253A',         # Chữ trên card (Purple đậm)
                'content_bg': '#BFBFBF',      # Nền nội dung (Xám đậm)
                'control_bar': '#F0F0F0',     # Thanh điều khiển (Trắng)
                'accent': '#9B7BB8',          # Màu nhấn (Purple)
                'text_light': '#FFFFFF',      # Chữ trên nền tối
                'text_dark': '#333333',       # Chữ tối
                'button_hover': '#E0E0E0',    # Màu hover nút
                'border': '#555555',          # Màu viền
                'pdf_bg': '#555555',          # Nền canvas PDF
                'placeholder': '#888888'      # Chữ placeholder
            },
            # -------------------------
            # LIGHT THEME - Chế độ sáng
            # -------------------------
            'light': {
                'bg': '#E8F4FC',              # Nền chính (Xanh nhạt)
                'panel_bg': '#D6E9F5',        # Nền panel (Xanh dịu)
                'card_bg': '#FFFFFF',         # Nền card danh sách (Trắng)
                'card_fg': '#333333',         # Chữ trên card (Xám đậm)
                'content_bg': '#FFFFFF',      # Nền nội dung (Trắng)
                'control_bar': '#F5F5F5',     # Thanh điều khiển (Xám nhạt)
                'accent': '#4A90D9',          # Màu nhấn (Xanh)
                'text_light': '#333333',      # Chữ trên nền sáng
                'text_dark': '#333333',       # Chữ tối
                'button_hover': '#E0E0E0',    # Màu hover nút
                'border': '#CCCCCC',          # Màu viền
                'pdf_bg': '#F0F0F0',          # Nền canvas PDF
                'placeholder': '#666666'      # Chữ placeholder
            }
        }
        
        # Lấy theme hiện tại từ customtkinter
        current_mode = ctk.get_appearance_mode()  # Trả về "Light" hoặc "Dark"
        theme_key = 'dark' if current_mode == "Dark" else 'light'
        self.colors = self.themes.get(theme_key, self.themes['light'])
        
        # ====================================================================
        # TẠO GIAO DIỆN - MAIN CONTAINER
        # Container chính chứa 2 panel: Left (danh sách) và Right (nội dung)
        # ====================================================================
        self.main_container = ctk.CTkFrame(parent, fg_color=self.colors['bg'])
        self.main_container.pack(fill="both", expand=True)
        
        # --------------------------------------------------------------------
        # LEFT PANEL - Bảng danh sách tài liệu (bên trái)
        # Chiều rộng cố định 350px, chứa search bar và document list
        # --------------------------------------------------------------------
        self.left_panel = ctk.CTkFrame(
            self.main_container,
            fg_color=self.colors['panel_bg'],
            corner_radius=30,     # Bo tròn góc
            width=350             # Chiều rộng cố định
        )
        self.left_panel.pack(side="left", fill="both", expand=False, padx=20, pady=20)
        self.left_panel.pack_propagate(False)  # Giữ nguyên width, không co giãn
        
        # --------------------------------------------------------------------
        # RIGHT PANEL - Bảng nội dung (bên phải)
        # Co giãn theo cửa sổ, hiển thị PDF hoặc Note content
        # --------------------------------------------------------------------
        self.right_panel = ctk.CTkFrame(
            self.main_container, 
            fg_color=self.colors['panel_bg'],
            corner_radius=30
        )
        self.right_panel.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        # ====================================================================
        # KHỞI TẠO CÁC VIEW
        # ====================================================================
        self.init_left_panel()              # Khởi tạo panel danh sách
        self.init_right_panel_placeholder() # Khởi tạo placeholder "Select a document"
        
        # Nếu có notes, hiển thị note đầu tiên
        if self.notes:
            self.show_note_content(self.notes[0])

    # ========================================================================
    # PHẦN 3: QUẢN LÝ DỮ LIỆU (DATA MANAGEMENT)
    # ========================================================================

    def get_data_path(self):
        """
        Lấy đường dẫn thư mục lưu trữ dữ liệu ứng dụng
        
        Thư mục khác nhau tùy theo hệ điều hành:
        - Windows: %LOCALAPPDATA%/sapient/documents
        - macOS: ~/Library/Application Support/sapient/documents
        - Linux: ~/.config/sapient/documents
        
        Returns:
            Path: Đường dẫn đến thư mục data
        """
        app_name = "sapient"
        
        if os.name == "nt":  # Windows
            data_dir = Path(os.getenv("LOCALAPPDATA")) / app_name / "documents"
        elif os.name == "posix":  # Unix-like (Linux, macOS)
            import sys
            if sys.platform == "darwin":  # macOS
                data_dir = Path.home() / "Library" / "Application Support" / app_name / "documents"
            else:  # Linux
                data_dir = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / app_name / "documents"
        else:  # Fallback cho các OS khác
            data_dir = Path.home() / f".{app_name.lower()}" / "documents"
        
        # Tạo thư mục nếu chưa tồn tại
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def load_notes(self):
        """
        Tải danh sách notes từ file JSON
        
        Returns:
            list: Danh sách notes, hoặc [] nếu file không tồn tại/lỗi
        """
        if self.notes_file.exists():
            try:
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_notes(self):
        """
        Lưu danh sách notes vào file JSON
        
        Lưu ý: ensure_ascii=False để hỗ trợ tiếng Việt
        """
        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving notes: {e}")

    # ========================================================================
    # PHẦN 4: LEFT PANEL - DANH SÁCH TÀI LIỆU
    # ========================================================================
    
    def init_left_panel(self):
        """
        Khởi tạo Left Panel với:
        1. Search Bar - Ô tìm kiếm tài liệu
        2. Scrollable List - Danh sách tài liệu cuộn được
        3. Add Button (+) - Nút thêm tài liệu mới
        """
        # Xóa tất cả widget cũ
        for widget in self.left_panel.winfo_children():
            widget.destroy()
        
        # --------------------------------------------------------------------
        # SEARCH BAR - Ô tìm kiếm (FR-DCM-01)
        # Tự động filter khi người dùng gõ
        # --------------------------------------------------------------------
        search_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        search_frame.pack(fill="x", padx=15, pady=(20, 10))
        
        # Biến StringVar để theo dõi nội dung search
        self.search_var = ctk.StringVar()
        # Gọi filter_documents mỗi khi nội dung thay đổi
        self.search_var.trace_add("write", lambda *args: self.filter_documents())
        
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Search documents...",  # Placeholder text
            textvariable=self.search_var,
            fg_color=self.colors['card_bg'],
            text_color=self.colors['card_fg'],
            placeholder_text_color="#888888",
            corner_radius=15,
            height=40
        )
        search_entry.pack(fill="x")
            
        # --------------------------------------------------------------------
        # SCROLLABLE LIST - Danh sách tài liệu có thanh cuộn
        # --------------------------------------------------------------------
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.left_panel,
            fg_color="transparent",
            scrollbar_button_color=self.colors['panel_bg'],
            width=300
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=20)
        
        # Điền danh sách tài liệu vào scroll_frame
        self.populate_document_list()
            
    
    def populate_document_list(self, search_query=""):
        """
        Điền danh sách tài liệu vào Left Panel
        
        Args:
            search_query: Từ khóa tìm kiếm (mặc định = "" hiển thị tất cả)
        
        Logic:
        1. Xóa danh sách cũ
        2. Sắp xếp notes theo ngày sửa đổi (mới nhất trước)
        3. Lọc theo search_query nếu có
        4. Tạo card cho mỗi note
        5. Thêm nút [+] ở cuối
        """
        # Xóa các item cũ
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        # Sắp xếp theo ngày modified (mới nhất trước)
        sorted_notes = sorted(self.notes, key=lambda x: x.get('modified', ''), reverse=True)
        
        # Lọc theo search query
        if search_query:
            search_lower = search_query.lower()
            sorted_notes = [n for n in sorted_notes if search_lower in n.get('title', '').lower()]
        
        # Tạo card cho mỗi note
        for note in sorted_notes:
            self.create_list_item(note)
        
        # Hiển thị thông báo nếu không tìm thấy kết quả
        if not sorted_notes and search_query:
            ctk.CTkLabel(
                self.scroll_frame,
                text="No documents found",
                text_color="#888888",
                font=ctk.CTkFont(size=14)
            ).pack(pady=30)

        # --------------------------------------------------------------------
        # NÚT THÊM [+] - Ở cuối danh sách
        # Click để mở menu thêm file PDF hoặc Note mới
        # --------------------------------------------------------------------
        ctk.CTkButton(
            self.scroll_frame,
            text="+",
            font=ctk.CTkFont(size=40, weight="bold"),
            fg_color=self.colors['card_bg'],
            text_color="black",
            hover_color=self.colors['button_hover'],
            height=60,
            corner_radius=30,  # Bo tròn thành hình viên thuốc (pill)
            command=self.show_add_menu
        ).pack(fill="x", pady=20)
    
    def filter_documents(self):
        """
        Lọc tài liệu dựa trên search query (FR-DCM-01)
        Được gọi tự động khi người dùng gõ trong search bar
        """
        if self.search_var:
            search_query = self.search_var.get()
            self.populate_document_list(search_query)
        
    def create_list_item(self, note):
        """
        Tạo một card item trong danh sách tài liệu
        
        Args:
            note: Dictionary chứa thông tin note
        
        Cấu trúc card:
        ┌──────────────────────────────────────┐
        │ ▌ 📕 Title                 🔴 High    │
        │ ▌     Date: 2024-01-01               │
        └──────────────────────────────────────┘
         ↑ Priority bar (màu sắc theo mức độ)
        """
        # Màu sắc theo mức độ ưu tiên
        priority_colors = {
            "High": "#FF4444",      # Đỏ - Cao
            "Medium": "#FFB800",    # Vàng - Trung bình
            "Normal": "#44BB44"     # Xanh lá - Bình thường
        }
        priority = note.get('priority', 'Normal')
        priority_color = priority_colors.get(priority, "#44BB44")
        
        # Card Container - Khung chính của item
        card = ctk.CTkFrame(
            self.scroll_frame,
            fg_color=self.colors['card_bg'],
            corner_radius=20,
            height=80
        )
        card.pack(fill="x", pady=10)
        card.pack_propagate(False)  # Giữ chiều cao cố định
        
        # Priority Indicator Bar - Thanh màu bên trái thể hiện mức độ ưu tiên
        priority_bar = ctk.CTkFrame(
            card,
            fg_color=priority_color,
            corner_radius=10,
            width=6
        )
        priority_bar.pack(side="left", fill="y", padx=(8, 0), pady=10)
        
        # Icon - Biểu tượng loại file (📕 cho PDF, 📝 cho Note)
        icon_text = "📕" if note.get('type') == 'pdf' else "📝"
        icon = ctk.CTkLabel(card, text=icon_text, font=ctk.CTkFont(size=24), text_color=self.colors['card_fg'])
        icon.pack(side="left", padx=(10, 10))
        
        # Info Container - Chứa thông tin title và metadata
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, pady=10)
        
        # Title - Tiêu đề (cắt ngắn nếu quá dài)
        title = note.get('title', 'Untitled')
        if len(title) > 20: title = title[:18] + "..."
        ctk.CTkLabel(
            info_frame, 
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors['card_fg'],
            anchor="w"
        ).pack(fill="x")
        
        # Metadata Row - Hàng chứa ngày và mức độ ưu tiên
        meta_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        meta_frame.pack(fill="x", pady=(5, 0))
        
        # Ngày sửa đổi
        date_str = note.get('modified', '').split(' ')[0]  # Chỉ lấy phần ngày
        ctk.CTkLabel(
            meta_frame,
            text=f"Date:{date_str}",
            font=ctk.CTkFont(size=11),
            text_color=self.colors['card_fg']
        ).pack(side="left")
        
        # Priority Badge - Hiển thị mức độ ưu tiên với emoji
        priority_emoji = {"High": "🔴", "Medium": "🟡", "Normal": "🟢"}.get(priority, "🟢")
        ctk.CTkLabel(
            meta_frame,
            text=f"{priority_emoji} {priority}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors['card_fg']
        ).pack(side="right", padx=10)
        
        # Click bindings - Bắt sự kiện click vào card
        for w in [card, icon, info_frame, priority_bar]:
            w.bind("<Button-1>", lambda e, n=note: self.show_note_content(n))
            
    def show_add_menu(self):
        """
        Hiển thị dialog để thêm file mới
        
        Cho phép người dùng chọn:
        - PDF File: Mở file PDF có sẵn
        - New Note: Tạo ghi chú mới
        """
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Add File")
        dialog.geometry("300x150")
        dialog.transient(self.parent)  # Dialog phụ thuộc vào cửa sổ chính
        
        ctk.CTkLabel(dialog, text="Choose file type:", font=ctk.CTkFont(size=16)).pack(pady=20)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20)
        
        # Nút mở file PDF
        ctk.CTkButton(
            btn_frame, text="PDF File", command=lambda: [dialog.destroy(), self.open_pdf_file()]
        ).pack(side="left", expand=True, padx=5)
        
        # Nút tạo note mới
        ctk.CTkButton(
            btn_frame, text="New Note", command=lambda: [dialog.destroy(), self.create_new_note()]
        ).pack(side="right", expand=True, padx=5)
        
    # ========================================================================
    # PHẦN 5: RIGHT PANEL - HIỂN THỊ NỘI DUNG
    # ========================================================================
    
    def init_right_panel_placeholder(self):
        """
        Hiển thị placeholder khi chưa chọn tài liệu nào
        
        Hiển thị dòng chữ "Select a document to view"
        """
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(
            self.right_panel,
            text="Select a document to view",
            font=ctk.CTkFont(size=20),
            text_color=self.colors['placeholder']
        ).pack(expand=True)

    def show_note_content(self, note):
        """
        Hiển thị nội dung của một note/PDF trong Right Panel
        
        Args:
            note: Dictionary chứa thông tin note
        
        Cấu trúc giao diện:
        ┌─────────────────────────────────────┐
        │           Title Entry               │  <- Có thể chỉnh sửa
        │  ┌─────────────────────────────┐    │
        │  │                             │    │
        │  │     Content Area            │    │  <- PDF Canvas hoặc Text Editor
        │  │     (PDF / Note)            │    │
        │  │                             │    │
        │  └─────────────────────────────┘    │
        │  ┌─────────────────────────────┐    │
        │  │ Priority | Date | Actions   │    │  <- Control Bar
        │  └─────────────────────────────┘    │
        └─────────────────────────────────────┘
        """
        self.current_note = note
        self.pdf_doc = None  # Reset trạng thái PDF
        
        # Xóa nội dung cũ
        for widget in self.right_panel.winfo_children():
            widget.destroy()
            
        # --------------------------------------------------------------------
        # 1. TITLE ENTRY - Ô nhập tiêu đề (có thể chỉnh sửa)
        # --------------------------------------------------------------------
        title_entry = ctk.CTkEntry(
            self.right_panel,
            font=ctk.CTkFont(size=22, weight="bold"),
            fg_color="transparent",
            border_width=0,
            text_color=self.colors['text_light'],
            placeholder_text="Title",
            justify="center"
        )
        title_entry.pack(fill="x", pady=(25, 15), padx=30)
        title_entry.insert(0, note.get('title', ''))
        # Tự động lưu khi focus out
        title_entry.bind("<FocusOut>", lambda e: self.update_title(title_entry.get()))
        
        # --------------------------------------------------------------------
        # 2. CONTENT CONTAINER - Khung nội dung chính
        # Bo tròn nhiều (corner_radius=40) như mockup
        # --------------------------------------------------------------------
        content_container = ctk.CTkFrame(
            self.right_panel,
            fg_color=self.colors['content_bg'],
            corner_radius=40
        )
        content_container.pack(fill="both", expand=True, pady=(0, 15), padx=15)
        
        # Kiểm tra loại nội dung và render tương ứng
        if note.get('type') == 'pdf':
            self.render_pdf_content(content_container, note)
        else:
            self.render_text_content(content_container, note)
            
        # --------------------------------------------------------------------
        # 3. CONTROL BAR - Thanh điều khiển ở đáy
        # Chứa Priority, Date, và các Action buttons
        # --------------------------------------------------------------------
        self.create_control_bar(note)
        
    def render_text_content(self, parent, note):
        """
        Render nội dung text note (FR-DCM-03)
        
        Args:
            parent: Widget cha
            note: Dictionary chứa content
        
        Tạo một Text widget để hiển thị và chỉnh sửa nội dung
        """
        text_widget = tk.Text(
            parent,
            bg=self.colors['content_bg'],
            fg="#000000",
            font=("Helvetica", 14),
            relief="flat",            # Không viền
            wrap="word",              # Xuống dòng theo từ
            padx=25,
            pady=25,
            highlightthickness=0      # Không highlight border
        )
        text_widget.pack(fill="both", expand=True, padx=15, pady=15)
        text_widget.insert("1.0", note.get('content', ''))
        
        # Cấu hình các tag định dạng text
        text_widget.tag_configure("bold", font=("Helvetica", 14, "bold"))
        text_widget.tag_configure("italic", font=("Helvetica", 14, "italic"))
        text_widget.tag_configure("underline", underline=True)
        
        # Lưu reference để sử dụng sau
        self.current_text_widget = text_widget
    
    def apply_format(self, format_type):
        """
        Áp dụng định dạng cho text được chọn (FR-DCM-03)
        
        Args:
            format_type: "bold", "italic", hoặc "underline"
        
        Logic: Toggle - nếu đã có tag thì xóa, chưa có thì thêm
        """
        if not hasattr(self, 'current_text_widget'):
            return
        
        try:
            # Lấy vùng text được chọn
            sel_start = self.current_text_widget.index("sel.first")
            sel_end = self.current_text_widget.index("sel.last")
            
            # Kiểm tra xem đã có tag chưa
            current_tags = self.current_text_widget.tag_names(sel_start)
            
            if format_type in current_tags:
                # Đã có tag -> Xóa tag (toggle off)
                self.current_text_widget.tag_remove(format_type, sel_start, sel_end)
            else:
                # Chưa có tag -> Thêm tag (toggle on)
                self.current_text_widget.tag_add(format_type, sel_start, sel_end)
        except tk.TclError:
            # Không có text được chọn
            pass
        
    def render_pdf_content(self, parent, note):
        """
        Render nội dung PDF (FR-DCM-02)
        
        Args:
            parent: Widget cha
            note: Dictionary chứa file_path
        
        Quy trình:
        1. Kiểm tra thư viện PyMuPDF và PIL
        2. Kiểm tra file có tồn tại không
        3. Mở PDF và tạo Canvas để hiển thị
        4. Render tất cả các trang vào Canvas
        """
        file_path = note.get('file_path', '')
        
        # Kiểm tra thư viện PDF
        if not HAS_PYMUPDF:
             err_frame = ctk.CTkFrame(parent, fg_color="transparent")
             err_frame.pack(expand=True)
             ctk.CTkLabel(err_frame, text="⚠️ PDF Library Missing", font=ctk.CTkFont(size=20, weight="bold"), text_color="#FF5555").pack(pady=10)
             ctk.CTkLabel(err_frame, text="Run: pip install PyMuPDF Pillow", font=ctk.CTkFont(size=14)).pack()
             return

        # Kiểm tra file tồn tại
        if not os.path.exists(file_path):
             ctk.CTkLabel(parent, text=f"⚠️ File Not Found:\n{file_path}", text_color="#FF5555", font=ctk.CTkFont(size=16)).pack(expand=True)
             return

        if HAS_PYMUPDF and HAS_PIL:
            try:
                # Mở tài liệu PDF
                self.pdf_doc = fitz.open(file_path)
                
                # Tạo Canvas để vẽ PDF
                self.pdf_canvas = tk.Canvas(parent, bg=self.colors['pdf_bg'], highlightthickness=0)
                self.pdf_canvas.pack(fill="both", expand=True)
                
                # Bind sự kiện resize để auto-fit
                self.pdf_canvas.bind('<Configure>', self.on_canvas_configure)
                
                # Bind sự kiện cuộn chuột
                self.pdf_canvas.bind("<MouseWheel>", self.on_mouse_scroll)  # Windows/macOS
                self.pdf_canvas.bind("<Button-4>", self.on_mouse_scroll)    # Linux scroll up
                self.pdf_canvas.bind("<Button-5>", self.on_mouse_scroll)    # Linux scroll down
                
                # Bắt focus khi hover để cuộn chuột hoạt động
                self.pdf_canvas.bind("<Enter>", lambda e: self.pdf_canvas.focus_set())
                
                # Render tất cả các trang
                self.render_all_pages()
                
            except Exception as e:
                 ctk.CTkLabel(parent, text=f"Error rendering PDF: {e}", text_color="red").pack(pady=20)
        else:
             ctk.CTkLabel(parent, text="PDF rendering requires Pillow library.", text_color="red").pack(pady=20)

    def on_canvas_configure(self, event):
        """
        Xử lý khi Canvas thay đổi kích thước
        
        Re-render PDF để fit với kích thước mới
        """
        if self.pdf_doc:
            self.render_all_pages()

    def on_mouse_scroll(self, event):
        """
        Xử lý cuộn chuột trên PDF Canvas
        
        Chỉ cuộn dọc (vertical scroll)
        """
        if not self.pdf_doc: return
        
        # Cuộn lên/xuống
        if event.num == 5 or event.delta < 0:  # Cuộn xuống
            self.pdf_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:  # Cuộn lên
            self.pdf_canvas.yview_scroll(-1, "units")

    def render_all_pages(self):
        """
        Render tất cả các trang PDF vào Canvas
        
        Logic:
        1. Tính zoom để fit width
        2. Loop qua từng trang
        3. Render trang thành hình ảnh
        4. Vẽ hình ảnh lên canvas
        5. Cập nhật scroll region
        """
        if not self.pdf_doc: return
        
        # Tính zoom để fit chiều rộng canvas
        canvas_width = self.pdf_canvas.winfo_width()
        if canvas_width < 100: canvas_width = 800  # Fallback nếu canvas chưa sẵn sàng
        
        # Reset danh sách ảnh và xóa canvas
        self.pdf_images = []
        self.pdf_canvas.delete("all")
        
        y_offset = 10  # Khoảng cách từ top
        gap = 10       # Khoảng cách giữa các trang
        
        # Loop qua từng trang
        for i in range(len(self.pdf_doc)):
            page = self.pdf_doc[i]
            page_width = page.rect.width
            
            # Tính zoom factor để fit width
            zoom = (canvas_width - 4) / page_width
            
            # Render trang thành pixmap
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Chuyển đổi sang PIL Image rồi sang PhotoImage
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            photo_img = ImageTk.PhotoImage(img)
            self.pdf_images.append(photo_img)  # Giữ reference tránh bị garbage collect
            
            # Vẽ hình ảnh lên canvas (căn giữa)
            self.pdf_canvas.create_image(
                canvas_width // 2,
                y_offset,
                anchor="n",  # Neo ở top-center
                image=photo_img
            )
            
            y_offset += pix.height + gap
            
        # Cập nhật vùng cuộn
        self.pdf_canvas.configure(scrollregion=(0, 0, canvas_width, y_offset))

    def create_control_bar(self, note):
        """
        Tạo Control Bar - Thanh điều khiển ở đáy Right Panel
        
        Args:
            note: Dictionary chứa thông tin note
        
        Cấu trúc:
        ┌──────────────────────────────────────────────────┐
        │ [Priority ▼] [📅 Date]          [Split][Open][Delete][Save] │
        └──────────────────────────────────────────────────┘
        """
        # Container ngoài
        bar_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        bar_container.pack(fill="x", side="bottom", pady=20, padx=20)
        
        # Thanh control chính (hình viên thuốc trắng)
        bar = ctk.CTkFrame(
            bar_container,
            fg_color=self.colors['control_bar'],
            corner_radius=25,
            height=55
        )
        bar.pack(fill="x")
        bar.pack_propagate(False)  # Giữ chiều cao cố định
        
        # ====================================================================
        # LEFT SECTION - Priority Dropdown và Date Badge
        # ====================================================================
        left_section = ctk.CTkFrame(bar, fg_color="transparent")
        left_section.pack(side="left", fill="y", padx=(15, 10), pady=8)
        
        # Priority Dropdown - Chọn mức độ ưu tiên
        priority_options = ["🔴 High", "🟡 Medium", "🟢 Normal"]
        current_priority = note.get('priority', 'Normal')
        priority_map = {"High": "🔴 High", "Medium": "🟡 Medium", "Normal": "🟢 Normal"}
        display_priority = priority_map.get(current_priority, "🟢 Normal")
        
        priority_var = ctk.StringVar(value=display_priority)
        priority_menu = ctk.CTkOptionMenu(
            left_section,
            values=priority_options,
            variable=priority_var,
            fg_color="#E8E8E8",
            button_color="#D0D0D0",
            button_hover_color="#B8B8B8",
            text_color="black",
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color="black",
            dropdown_hover_color="#E8E8E8",
            corner_radius=12,
            width=110,
            height=35,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda val: self.update_priority(note, val)
        )
        priority_menu.pack(side="left", padx=(0, 8))
        
        # Date Badge - Hiển thị ngày sửa đổi
        date_str = note.get('modified', '').split(' ')[0]
        ctk.CTkLabel(
            left_section, 
            text=f"📅 {date_str}",
            text_color="#666666",
            fg_color="#E8E8E8",
            corner_radius=12,
            height=35,
            font=ctk.CTkFont(size=12),
            padx=12
        ).pack(side="left")
        
        # ====================================================================
        # RIGHT SECTION - Action Buttons
        # ====================================================================
        right_section = ctk.CTkFrame(bar, fg_color="transparent")
        right_section.pack(side="right", fill="y", padx=(10, 15), pady=8)
        
        # Save Button - Lưu tài liệu
        ctk.CTkButton(
            right_section,
            text="Save",
            fg_color="#E8E8E8",
            text_color="black",
            hover_color="#D0D0D0",
            corner_radius=12,
            width=70,
            height=35,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.save_current_note
        ).pack(side="right", padx=(8, 0))
        
        # Delete Button - Xóa tài liệu
        ctk.CTkButton(
            right_section,
            text="Delete",
            fg_color="transparent",
            text_color="#CC0000",
            hover_color="#FFE0E0",
            width=60,
            height=35,
            corner_radius=12,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.delete_note(note['id'])
        ).pack(side="right", padx=(8, 0))
        
        # ----------------------------------------------------------------
        # PDF SPECIFIC BUTTONS - Chỉ hiển thị khi xem PDF
        # ----------------------------------------------------------------
        if note.get('type') == 'pdf':
            # Open Button - Mở bằng ứng dụng mặc định
            ctk.CTkButton(
                right_section, 
                text="Open",
                fg_color="transparent",
                text_color="black",
                hover_color="#E8E8E8",
                corner_radius=12,
                width=60,
                height=35,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda: self.open_in_system(note)
            ).pack(side="right", padx=(8, 0))
            
            # Split Button - Vào chế độ Split View
            ctk.CTkButton(
                right_section, 
                text="Split",
                fg_color="transparent",
                text_color="black",
                hover_color="#E8E8E8",
                corner_radius=12,
                width=60,
                height=35,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=self.enter_split_view
            ).pack(side="right", padx=(8, 0))

    # ========================================================================
    # PHẦN 6: ACTIONS - CÁC HÀNH ĐỘNG CRUD
    # ========================================================================

    def update_title(self, new_title):
        """
        Cập nhật tiêu đề của note hiện tại
        
        Args:
            new_title: Tiêu đề mới
        """
        if self.current_note:
            self.current_note['title'] = new_title
            self.save_notes()
            self.init_left_panel()  # Refresh danh sách

    def update_priority(self, note, priority_value):
        """
        Cập nhật mức độ ưu tiên của note
        
        Args:
            note: Note cần update
            priority_value: Giá trị từ dropdown (VD: "🔴 High")
        """
        # Tách lấy phần text priority (bỏ emoji)
        priority_clean = priority_value.split(' ')[-1]  # "High", "Medium", hoặc "Normal"
        note['priority'] = priority_clean
        self.save_notes()
        self.init_left_panel()  # Refresh danh sách

    def save_current_note(self):
        """
        Lưu note hiện tại
        
        Nếu là text note, lấy nội dung từ text widget
        Cập nhật ngày modified và lưu vào file
        """
        if not self.current_note: return
        
        # Nếu là text note, lấy nội dung từ widget
        if self.current_note.get('type') != 'pdf' and hasattr(self, 'current_text_widget'):
            self.current_note['content'] = self.current_text_widget.get("1.0", "end-1c")
        
        # Cập nhật ngày sửa đổi
        self.current_note['modified'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.save_notes()
        self.init_left_panel()
        messagebox.showinfo("Saved", "Document saved successfully")
        
    def delete_note(self, note_id):
        """
        Xóa note theo ID
        
        Args:
            note_id: ID của note cần xóa
        """
        if messagebox.askyesno("Confirm", "Delete this document?"):
            self.notes = [n for n in self.notes if n['id'] != note_id]
            self.save_notes()
            self.init_left_panel()
            self.init_right_panel_placeholder()

    def open_pdf_file(self):
        """
        Mở dialog để chọn file PDF và thêm vào danh sách
        
        Tạo note mới với type='pdf' và hiển thị nội dung
        """
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
        if file_path:
            note_id = f"pdf_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            new_note = {
                'id': note_id,
                'title': os.path.basename(file_path).replace('.pdf', ''),
                'content': '',
                'file_path': file_path,
                'type': 'pdf',
                'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.notes.append(new_note)
            self.save_notes()
            self.init_left_panel()
            self.show_note_content(new_note)
            
    def create_new_note(self):
        """
        Tạo một note text mới
        
        Tạo note với type='note' và nội dung rỗng
        """
        note_id = f"note_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        new_note = {
            'id': note_id,
            'title': 'New Note',
            'content': '',
            'type': 'note',
            'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.notes.append(new_note)
        self.save_notes()
        self.init_left_panel()
        self.show_note_content(new_note)

    def open_in_system(self, note):
        """
        Mở file PDF bằng ứng dụng mặc định của hệ thống
        
        Args:
            note: Note chứa file_path
        
        Sử dụng lệnh khác nhau tùy OS:
        - macOS: open
        - Windows: os.startfile()
        - Linux: xdg-open
        """
        file_path = note.get('file_path', '')
        if os.path.exists(file_path):
            try:
                system = platform.system()
                if system == 'Darwin':
                    subprocess.run(['open', file_path])
                elif system == 'Windows':
                    os.startfile(file_path)
                else:
                    subprocess.run(['xdg-open', file_path])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {e}")

    # ========================================================================
    # PHẦN 7: SPLIT VIEW - CHẾ ĐỘ XEM SONG SONG
    # ========================================================================

    def enter_split_view(self):
        """
        Vào chế độ Split View: Xem PDF và ghi chú song song
        
        Chỉ hoạt động với PDF (type='pdf')
        
        Layout Split View:
        ┌─────────────────────────────────────────────────────┐
        │  ┌──────────────┐  ┌─────────────────────────────┐  │
        │  │  NOTE AREA   │  │       PDF AREA              │  │
        │  │  (flexible)  │  │       (fixed 700px)         │  │
        │  │              │  │                             │  │
        │  └──────────────┘  └─────────────────────────────┘  │
        │  ┌─────────────────────────────────────────────────┐│
        │  │ [Save Note]                    [Exit Split View]││
        │  └─────────────────────────────────────────────────┘│
        └─────────────────────────────────────────────────────┘
        
        Đặc điểm:
        - Ẩn Left Panel (danh sách)
        - Ẩn Sidebar của ứng dụng chính
        - PDF có chiều rộng cố định 700px
        - Note area co giãn theo cửa sổ
        """
        # Kiểm tra có phải PDF không
        if not self.current_note or self.current_note.get('type') != 'pdf':
            return
            
        self.is_split_mode = True
        
        # 1. Ẩn Left Panel (danh sách tài liệu)
        self.left_panel.pack_forget()
        
        # 2. Ẩn Sidebar của ứng dụng chính
        app = self.parent.winfo_toplevel()
        if hasattr(app, 'toggle_sidebar'):
            app.toggle_sidebar(False)
        
        # 3. Xóa Right Panel cũ để tạo layout mới
        for widget in self.right_panel.winfo_children():
            widget.destroy()
            
        # 4. Tạo container chính cho Split View
        content_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        content_container.pack(fill="both", expand=True, padx=10, pady=(10, 5))
        
        # ----------------------------------------------------------------
        # PDF FRAME - Bên phải, chiều rộng CỐ ĐỊNH 700px
        # Pack trước để chiếm vị trí bên phải
        # ----------------------------------------------------------------
        pdf_frame = ctk.CTkFrame(content_container, fg_color=self.colors['content_bg'], corner_radius=20, width=700)
        pdf_frame.pack(side="right", fill="y", padx=(5, 0))
        pdf_frame.pack_propagate(False)  # QUAN TRỌNG: Không cho phép co giãn
        
        # ----------------------------------------------------------------
        # NOTE FRAME - Bên trái, CO GIÃN theo cửa sổ
        # ----------------------------------------------------------------
        note_frame = ctk.CTkFrame(content_container, fg_color=self.colors['content_bg'], corner_radius=20)
        note_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Tìm hoặc tạo note liên kết với PDF này
        linked_note = self.get_linked_note(self.current_note)
        
        # Hiển thị tiêu đề note
        ctk.CTkLabel(note_frame, text=linked_note['title'], font=ctk.CTkFont(size=18, weight="bold"), text_color="black").pack(pady=(15, 10))
        
        # Hiển thị text editor cho note
        self.render_text_content(note_frame, linked_note)
        
        # ----------------------------------------------------------------
        # PDF CANVAS - Render PDF trong pdf_frame
        # ----------------------------------------------------------------
        self.pdf_canvas = tk.Canvas(pdf_frame, bg=self.colors['pdf_bg'], highlightthickness=0)
        self.pdf_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        self.pdf_canvas.bind('<Configure>', self.on_canvas_configure)
        
        # Bind cuộn chuột
        self.pdf_canvas.bind("<MouseWheel>", self.on_mouse_scroll)
        self.pdf_canvas.bind("<Button-4>", self.on_mouse_scroll)
        self.pdf_canvas.bind("<Button-5>", self.on_mouse_scroll)
        self.pdf_canvas.bind("<Enter>", lambda e: self.pdf_canvas.focus_set())
        
        # Render tất cả trang PDF
        self.render_all_pages()
        
        # ----------------------------------------------------------------
        # CONTROL BAR - Thanh điều khiển ở dưới
        # ----------------------------------------------------------------
        bar_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        bar_container.pack(fill="x", padx=10, pady=(5, 15))
        
        bar = ctk.CTkFrame(
            bar_container, 
            fg_color=self.colors['control_bar'], 
            corner_radius=25, 
            height=50
        )
        bar.pack(fill="x")
        bar.pack_propagate(False)
        
        # Nút Save Note (bên trái)
        left_section = ctk.CTkFrame(bar, fg_color="transparent")
        left_section.pack(side="left", fill="y", padx=15, pady=8)
        
        ctk.CTkButton(
            left_section, 
            text="Save Note",
            fg_color="#E8E8E8",
            text_color="black",
            hover_color="#D0D0D0",
            corner_radius=12,
            width=100,
            height=35,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self.save_split_note(linked_note)
        ).pack(side="left")
        
        # Nút Exit Split View (bên phải)
        right_section = ctk.CTkFrame(bar, fg_color="transparent")
        right_section.pack(side="right", fill="y", padx=15, pady=8)
        
        ctk.CTkButton(
            right_section, 
            text="Exit Split View",
            fg_color="transparent",
            text_color="#CC0000",
            hover_color="#FFE0E0",
            corner_radius=12,
            width=120,
            height=35,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.exit_split_view
        ).pack(side="right")

    def exit_split_view(self):
        """
        Thoát chế độ Split View và khôi phục layout bình thường
        
        1. Hiện lại Sidebar ứng dụng
        2. Hiện lại Left Panel (danh sách)
        3. Reload nội dung PDF bình thường
        """
        self.is_split_mode = False
        
        # Hiện lại Sidebar ứng dụng
        app = self.parent.winfo_toplevel()
        if hasattr(app, 'toggle_sidebar'):
            app.toggle_sidebar(True)
        
        # Reset grid config (nếu có)
        self.right_panel.grid_columnconfigure(0, weight=0)
        self.right_panel.grid_columnconfigure(1, weight=0)
        
        # Hiện lại Left Panel
        self.left_panel.pack(side="left", fill="both", expand=False, padx=20, pady=20)
        
        # Reload view PDF bình thường
        self.show_note_content(self.current_note)

    def get_linked_note(self, pdf_note):
        """
        Tìm hoặc tạo note liên kết với PDF
        
        Args:
            pdf_note: Note PDF đang xem
        
        Returns:
            dict: Note liên kết (hiện có hoặc mới tạo)
        
        Logic:
        1. Tìm note có title = "Note: {PDF_title}"
        2. Nếu không tìm thấy, tạo mới
        """
        pdf_name = pdf_note.get('title', 'Unknown')
        note_title = f"Note: {pdf_name}"
        
        # Tìm note đã tồn tại
        for note in self.notes:
            if note.get('title') == note_title and note.get('type') == 'note':
                return note
                
        # Tạo note mới nếu chưa có
        new_note = {
            'id': f"note_linked_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'title': note_title,
            'content': '',
            'type': 'note',
            'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'modified': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.notes.append(new_note)
        self.save_notes()
        return new_note

    def save_split_note(self, note):
        """
        Lưu note trong chế độ Split View
        
        Args:
            note: Note đang chỉnh sửa
        """
        if hasattr(self, 'current_text_widget'):
            note['content'] = self.current_text_widget.get("1.0", "end-1c")
            note['modified'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.save_notes()
            messagebox.showinfo("Saved", "Note saved successfully!")
