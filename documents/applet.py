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
        # Hiển thị khi chưa mở file nào
        # --------------------------------------------------------------------
        self.left_panel = ctk.CTkFrame(
            self.main_container,
            fg_color=self.colors['panel_bg'],
            corner_radius=30
        )
        # Không pack left_panel ngay, sẽ pack trong show_list_view()
        
        # --------------------------------------------------------------------
        # RIGHT PANEL - Bảng nội dung (bên phải)
        # Hiển thị khi mở file
        # --------------------------------------------------------------------
        self.right_panel = ctk.CTkFrame(
            self.main_container, 
            fg_color=self.colors['panel_bg'],
            corner_radius=30
        )
        # Không pack right_panel ngay, sẽ pack trong show_file_view()
        
        # ====================================================================
        # KHỚI TẠO - Hiển thị list view (danh sách file)
        # ====================================================================
        self.show_list_view()

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
        3. Add Buttons (PDF/TXT) - Nút thêm tài liệu mới
        """
        # Xóa tất cả widget cũ
        for widget in self.left_panel.winfo_children():
            widget.destroy()
        
        # Biến theo dõi item được chọn
        self.selected_note_id = None
        
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
            placeholder_text="🔍 Search",  # Placeholder text
            textvariable=self.search_var,
            fg_color="#5A4A6A",
            text_color="#FFFFFF",
            placeholder_text_color="#AAAAAA",
            corner_radius=20,
            height=45,
            border_width=0
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
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
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
        5. Thêm nút PDF/TXT ở cuối
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
        
        # Ẩn các linked notes (note của PDF, title bắt đầu bằng "Note:")
        sorted_notes = [n for n in sorted_notes if not n.get('title', '').startswith('Note:')]
        
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
        # NÚT THÊM PDF/TXT - Ở cuối danh sách
        # Thiết kế mới: Card với icon folder và 2 nút PDF, TXT
        # --------------------------------------------------------------------
        add_card = ctk.CTkFrame(
            self.scroll_frame,
            fg_color="#5A4A6A",
            corner_radius=20,
            height=55
        )
        add_card.pack(fill="x", pady=10)
        add_card.pack_propagate(False)
        
        # Icon folder
        ctk.CTkLabel(
            add_card,
            text="📁",
            font=ctk.CTkFont(size=20),
            text_color="#FFFFFF"
        ).pack(side="left", padx=(15, 5))
        
        # Separator
        ctk.CTkLabel(
            add_card,
            text="|",
            font=ctk.CTkFont(size=18),
            text_color="#888888"
        ).pack(side="left", padx=5)
        
        # Button frame
        btn_frame = ctk.CTkFrame(add_card, fg_color="transparent")
        btn_frame.pack(side="left", fill="x", expand=True, padx=10)
        
        # Nút PDF
        ctk.CTkButton(
            btn_frame,
            text="PDF",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#6B5A7A",
            text_color="#FFFFFF",
            hover_color="#7B6A8A",
            width=60,
            height=35,
            corner_radius=10,
            command=self.open_pdf_file
        ).pack(side="left", padx=5)
        
        # Nút TXT
        ctk.CTkButton(
            btn_frame,
            text="TXT",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#6B5A7A",
            text_color="#FFFFFF",
            hover_color="#7B6A8A",
            width=60,
            height=35,
            corner_radius=10,
            command=self.create_new_note
        ).pack(side="left", padx=5)
    
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
        
        Cấu trúc card mới (theo mockup):
        ┌──────────────────────────────────────┐
        │ � | filename.pdf                    │
        └──────────────────────────────────────┘
        - Icon folder bên trái
        - Separator dọc
        - Tên file
        - Viền xanh khi được chọn
        """
        note_id = note.get('id', note.get('title', ''))
        is_selected = (self.selected_note_id == note_id)
        
        # Card Container - Khung chính của item
        # Viền xanh nếu được chọn
        if is_selected:
            card = ctk.CTkFrame(
                self.scroll_frame,
                fg_color="#5A4A6A",
                corner_radius=20,
                height=55,
                border_width=2,
                border_color="#00BFFF"
            )
        else:
            card = ctk.CTkFrame(
                self.scroll_frame,
                fg_color="#5A4A6A",
                corner_radius=20,
                height=55
            )
        card.pack(fill="x", pady=8)
        card.pack_propagate(False)  # Giữ chiều cao cố định
        
        # Icon folder
        icon = ctk.CTkLabel(
            card,
            text="📁",
            font=ctk.CTkFont(size=20),
            text_color="#FFFFFF"
        )
        icon.pack(side="left", padx=(15, 5))
        
        # Separator dọc
        separator = ctk.CTkLabel(
            card,
            text="|",
            font=ctk.CTkFont(size=18),
            text_color="#888888"
        )
        separator.pack(side="left", padx=5)
        
        # Title - Tên file
        title = note.get('title', 'Untitled')
        # Thêm đuôi file nếu chưa có
        if note.get('type') == 'pdf' and not title.lower().endswith('.pdf'):
            title = title + '.pdf'
        elif note.get('type') != 'pdf' and not title.lower().endswith('.txt'):
            title = title + '.txt' if '.' not in title else title
        
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=14),
            text_color="#FFFFFF",
            anchor="w"
        )
        title_label.pack(side="left", fill="x", expand=True, padx=10)
        
        # Click bindings - Bắt sự kiện click vào card
        def on_click(e, n=note):
            self.selected_note_id = n.get('id', n.get('title', ''))
            # Chuyển sang File View (ẩn list, hiện nội dung)
            self.show_file_view(n)
        
        for w in [card, icon, separator, title_label]:
            w.bind("<Button-1>", on_click)
            
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
    # PHẦN 5: TOGGLE GIỮA LIST VIEW VÀ FILE VIEW
    # ========================================================================
    
    def show_list_view(self):
        """
        Hiển thị List View - Danh sách tài liệu
        
        - Ẩn right_panel (nội dung file)
        - Hiển thị left_panel (danh sách file)
        - Được gọi khi khởi tạo và khi nhấn nút Back
        """
        # Ẩn right panel
        self.right_panel.pack_forget()
        
        # Hiển thị left panel (chiếm toàn bộ không gian)
        self.left_panel.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Khởi tạo nội dung left panel
        self.init_left_panel()
    
    def show_file_view(self, note):
        """
        Hiển thị File View - Nội dung file
        
        - Ẩn left_panel (danh sách file)
        - Hiển thị right_panel (nội dung file)
        - Được gọi khi click vào một file trong danh sách
        """
        # Ẩn left panel
        self.left_panel.pack_forget()
        
        # Hiển thị right panel (chiếm toàn bộ không gian)
        self.right_panel.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Hiển thị nội dung file
        self.show_note_content(note)
    
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
        # 0. NÚT BACK - Quay lại danh sách
        # --------------------------------------------------------------------
        back_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        back_frame.pack(fill="x", padx=15, pady=(15, 0))
        
        ctk.CTkButton(
            back_frame,
            text="← Back",
            font=ctk.CTkFont(size=14),
            fg_color="#5A4A6A",
            text_color="#FFFFFF",
            hover_color="#6B5A7A",
            width=100,
            height=35,
            corner_radius=15,
            command=self.show_list_view
        ).pack(side="left")
            
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
        title_entry.pack(fill="x", pady=(15, 15), padx=30)
        title_entry.insert(0, note.get('title', ''))
        # Tự động lưu khi focus out
        title_entry.bind("<FocusOut>", lambda e: self.update_title(title_entry.get()))
        
        # --------------------------------------------------------------------
        # 2. CONTROL BAR - Pack trước để hiển thị ở đáy
        # Chứa Priority, Date, và các Action buttons
        # --------------------------------------------------------------------
        self.create_control_bar(note)
        
        # --------------------------------------------------------------------
        # 3. CONTENT CONTAINER - Khung nội dung chính
        # Bo tròn nhiều (corner_radius=40) như mockup
        # --------------------------------------------------------------------
        content_container = ctk.CTkFrame(
            self.right_panel,
            fg_color=self.colors['content_bg'],
            corner_radius=40
        )
        content_container.pack(fill="both", expand=True, pady=(0, 0), padx=15)
        
        # Kiểm tra loại nội dung và render tương ứng
        if note.get('type') == 'pdf':
            self.render_pdf_content(content_container, note)
        else:
            self.render_text_content(content_container, note)
        
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
        # LEFT SECTION - Date Badge
        # ====================================================================
        left_section = ctk.CTkFrame(bar, fg_color="transparent")
        left_section.pack(side="left", fill="y", padx=(15, 10), pady=8)
        
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
            # Quay về list view sau khi xóa
            self.show_list_view()

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
        2. Giữ ở file view (không hiện left panel)
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
        
        # KHÔNG hiện lại Left Panel - giữ ở file view
        # self.left_panel.pack(...) - đã bỏ
        
        # Đảm bảo right_panel được hiển thị đúng cách
        self.right_panel.pack_forget()
        self.right_panel.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Reload view PDF bình thường
        self.show_note_content(self.current_note)

    def get_linked_note(self, pdf_note):
        """
        Lấy hoặc tạo note liên kết với PDF
        
        Args:
            pdf_note: Note PDF đang xem
        
        Returns:
            dict: Note liên kết (được lưu trực tiếp trong PDF document)
        
        Logic mới:
        - Note được lưu trực tiếp vào trường 'notes' của PDF document
        - Không tạo file note riêng biệt
        """
        pdf_name = pdf_note.get('title', 'Unknown')
        
        # Kiểm tra xem PDF đã có notes chưa
        if 'notes' not in pdf_note:
            pdf_note['notes'] = ''
            self.save_notes()
        
        # Trả về một dict giả để tương thích với code hiện tại
        return {
            'id': f"embedded_note_{pdf_note.get('id', '')}",
            'title': f"Notes for: {pdf_name}",
            'content': pdf_note.get('notes', ''),
            'type': 'embedded_note',
            'pdf_id': pdf_note.get('id', '')
        }

    def save_split_note(self, note):
        """
        Lưu note trong chế độ Split View
        
        Args:
            note: Note đang chỉnh sửa (embedded note dict)
        
        Note được lưu trực tiếp vào trường 'notes' của PDF document
        """
        if hasattr(self, 'current_text_widget') and self.current_note:
            content = self.current_text_widget.get("1.0", "end-1c")
            
            # Lưu vào trường 'notes' của PDF document
            self.current_note['notes'] = content
            self.current_note['modified'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.save_notes()
            messagebox.showinfo("Saved", "Note saved successfully!")
