import wx
import os
import threading
import queue
from tkinter import filedialog as tk_filedialog
from tkinter import Tk
import wx.grid
import requests
import time
import wx
import time
import pygetwindow as gw
import win32gui
from threading import Thread
import re
import pandas as pd
from datetime import datetime
# Placeholder: Import logic xử lý từ testfull.py
from testfull import process_excel_data
from testfull import extract_first_integer
from testfull import update_column_z_ok
from testfull import stt_Acc
from excel import write_bot_running_details, load_status_grid_from_excel, update_bot_running_details_by_thread, delete_bot_running_details_by_thread
import ast
from run_discord import DiscordBot

class ButtonRenderer(wx.grid.GridCellRenderer):
    def __init__(self, label):
        super().__init__()
        self.label = label
    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        dc.SetBrush(wx.Brush(wx.Colour(200, 200, 255)))
        dc.SetPen(wx.Pen(wx.Colour(100, 100, 200)))
        dc.DrawRectangle(rect)
        w, h = dc.GetTextExtent(self.label)
        dc.DrawText(self.label, rect.x + (rect.width-w)//2, rect.y + (rect.height-h)//2)
    def GetBestSize(self, grid, attr, dc, row, col):
        w, h = dc.GetTextExtent(self.label)
        return wx.Size(w+16, h+8)

class IconRenderer(wx.grid.GridCellRenderer):
    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        # Vẽ dấu X to, màu đỏ tươi
        dc.SetPen(wx.Pen(wx.Colour(255,0,0), 3))  # Đỏ tươi, nét dày
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        margin = 6
        dc.DrawLine(rect.x+margin, rect.y+margin, rect.x+rect.width-margin, rect.y+rect.height-margin)
        dc.DrawLine(rect.x+rect.width-margin, rect.y+margin, rect.x+margin, rect.y+rect.height-margin)
    def GetBestSize(self, grid, attr, dc, row, col):
        return wx.Size(24, 24)

class MainWindow(wx.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(None, title="Discord Airdrop Bot Config", size=(1000, 800))
        self.panel = wx.ScrolledWindow(self, style=wx.VSCROLL | wx.HSCROLL)
        self.panel.SetScrollRate(20, 20)
        self.mode = "manual"  # default
        self.default_excel_path = os.getenv("BOT_EXCEL_PATH", "")
        self.default_errorlog_path = os.getenv("BOT_ERROR_LOG_PATH", "")
        self.default_json_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
        self.default_sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
        self.default_captcha_ext_url = os.getenv("BOT_CAPTCHA_EXT_URL", "")
        self.json_path = self.default_json_path
        self.selected_profiles = []
        self.proxy_type = "static"
        self.static_proxies = []
        self.dynamic_proxies = []
        self.thread_count = 1
        self.mission_text = ""
        self.xpath_after_completion = ""
        self.proxy_dynamic_hostport = None
        self.proxy_dynamic_add_btn = None
        self.proxy_dynamic_listbox = None
        self.proxy_dynamic_scroll = None
        self.selected_dynamic_proxies = []
        self.current_acc_running = {}  # key: thread_index, value: acc_name
        self.skip_acc_flags = {}  # key: thread_id, value: threading.Event
        self.stop_thread_flags = {}  # key: thread_id, value: threading.Event
        self.profile_bots = {}
        self.threads_run = {}
        self.reset_acc_flags = {}  # key: thread_id, value: threading.Event
        self.chuyen_all_acc = {}

        self.init_ui()
        self.Centre()  # Đảm bảo cửa sổ nằm giữa màn hình

    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Hàng chọn file Excel
        excel_box = wx.BoxSizer(wx.HORIZONTAL)
        self.excel_label = wx.StaticText(self.panel, label="Data excel:")
        excel_box.Add(self.excel_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.excel_path_ctrl = wx.TextCtrl(self.panel, style=wx.TE_READONLY, size=(350, -1), value=self.default_excel_path)
        excel_box.Add(self.excel_path_ctrl, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.excel_btn = wx.Button(self.panel, label="Browse Excel File")
        self.excel_btn.Bind(wx.EVT_BUTTON, self.on_select_excel)
        excel_box.Add(self.excel_btn, flag=wx.RIGHT, border=8)
        vbox.Add(excel_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Hàng chọn file ghi lỗi
        errorlog_box = wx.BoxSizer(wx.HORIZONTAL)
        self.errorlog_label = wx.StaticText(self.panel, label="Error log file:")
        errorlog_box.Add(self.errorlog_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.errorlog_path_ctrl = wx.TextCtrl(self.panel, style=wx.TE_READONLY, size=(200, -1), value=self.default_errorlog_path)
        errorlog_box.Add(self.errorlog_path_ctrl, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.errorlog_btn = wx.Button(self.panel, label="Browse Error Log")
        self.errorlog_btn.Bind(wx.EVT_BUTTON, self.on_select_errorlog)
        errorlog_box.Add(self.errorlog_btn, flag=wx.RIGHT, border=8)
        # Thêm ô nhập tên Sheet
        self.sheetname_label = wx.StaticText(self.panel, label="Sheet name:")
        errorlog_box.Add(self.sheetname_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.sheetname_ctrl = wx.TextCtrl(self.panel, size=(120, -1), value="Error")
        errorlog_box.Add(self.sheetname_ctrl, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        vbox.Add(errorlog_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Hàng chọn profile folder
        profile_box = wx.BoxSizer(wx.HORIZONTAL)
        self.profile_label = wx.StaticText(self.panel, label="Select Profile Folder(s):")
        profile_box.Add(self.profile_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.profile_button = wx.Button(self.panel, label="Browse for Profile Folder(s)")
        self.profile_button.Bind(wx.EVT_BUTTON, self.browse_multiple_folders)
        profile_box.Add(self.profile_button, flag=wx.RIGHT, border=8)
        vbox.Add(profile_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.profile_listbox = wx.ListBox(self.panel, choices=[], style=wx.LB_EXTENDED, size=(-1, 120))
        vbox.Add(self.profile_listbox, proportion=0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        self.delete_button = wx.Button(self.panel, label="Delete Selected Folder")
        self.delete_button.Bind(wx.EVT_BUTTON, self.delete_selected_folder)
        vbox.Add(self.delete_button, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Chọn chế độ Auto/Manual + Zoom/Width/Height trên cùng 1 hàng
        topbar_box = wx.BoxSizer(wx.HORIZONTAL)
        self.mode_radio_manual = wx.RadioButton(self.panel, label="Manual", style=wx.RB_GROUP)
        self.mode_radio_auto = wx.RadioButton(self.panel, label="Auto")
        self.mode_radio_manual.SetValue(True)
        self.mode_radio_manual.Bind(wx.EVT_RADIOBUTTON, self.on_mode_change)
        self.mode_radio_auto.Bind(wx.EVT_RADIOBUTTON, self.on_mode_change)
        topbar_box.Add(wx.StaticText(self.panel, label="Mode:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        topbar_box.Add(self.mode_radio_manual, flag=wx.RIGHT, border=8)
        topbar_box.Add(self.mode_radio_auto, flag=wx.RIGHT, border=16)
        # Thêm spinbox zoom
        topbar_box.Add(wx.StaticText(self.panel, label="Zoom (%):"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=4)
        self.zoom_spinbox = wx.SpinCtrl(self.panel, value="100", min=10, max=500)
        topbar_box.Add(self.zoom_spinbox, flag=wx.RIGHT, border=12)
        # Thêm nhập width
        topbar_box.Add(wx.StaticText(self.panel, label="Width:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=4)
        self.width_text = wx.TextCtrl(self.panel, value="800", size=(60, -1))
        topbar_box.Add(self.width_text, flag=wx.RIGHT, border=12)
        # Thêm nhập height
        topbar_box.Add(wx.StaticText(self.panel, label="Height:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=4)
        self.height_text = wx.TextCtrl(self.panel, value="900", size=(60, -1))
        topbar_box.Add(self.height_text, flag=wx.RIGHT, border=12)
        vbox.Add(topbar_box, flag=wx.ALL, border=10)

        # Chọn file .json Google API
        json_box = wx.BoxSizer(wx.HORIZONTAL)
        self.json_path_ctrl = wx.TextCtrl(self.panel, style=wx.TE_READONLY, value=self.default_json_path)
        json_btn = wx.Button(self.panel, label="Select Google API .json")
        json_btn.Bind(wx.EVT_BUTTON, self.on_select_json)
        json_box.Add(wx.StaticText(self.panel, label="Google API .json:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        json_box.Add(self.json_path_ctrl, proportion=1, flag=wx.EXPAND | wx.RIGHT, border=8)
        json_box.Add(json_btn)
        vbox.Add(json_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)
        # Thêm ô nhập SHEET_ID và SHEET_NAME_DISCORD
        sheetid_box = wx.BoxSizer(wx.HORIZONTAL)
        self.sheetid_ctrl = wx.TextCtrl(self.panel, style=0, value=self.default_sheet_id)
        sheetid_box.Add(wx.StaticText(self.panel, label="SHEET_ID:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        sheetid_box.Add(self.sheetid_ctrl, proportion=1, flag=wx.EXPAND | wx.RIGHT, border=8)
        # Thêm ô nhập Sheet_name_discord
        self.sheetname_discord_ctrl = wx.TextCtrl(self.panel, style=0, value="")
        sheetid_box.Add(wx.StaticText(self.panel, label="Sheet name Discord:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.sheetname_discord_ctrl.SetValue("DISCORD 1-1200")
        sheetid_box.Add(self.sheetname_discord_ctrl, proportion=1, flag=wx.EXPAND | wx.RIGHT, border=8)
        vbox.Add(sheetid_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        # Set Threads (cùng hàng với spinbox và restart nếu auto)
        self.cpu_cores = os.cpu_count() or 4
        self.thread_box = wx.BoxSizer(wx.HORIZONTAL)
        self.thread_label = wx.StaticText(self.panel, label="Set Threads:")
        self.thread_spinbox = wx.SpinCtrl(self.panel, value="2", min=1, max=self.cpu_cores)
        # Thêm checkbox Captcha
        self.captcha_checkbox = wx.CheckBox(self.panel, label="Captcha")
        self.captcha_checkbox.SetValue(False)
        self.captcha_ext_url_label = wx.StaticText(self.panel, label="Captcha Extension URL:")
        self.captcha_ext_url = wx.TextCtrl(self.panel, value=self.default_captcha_ext_url, size=(220, -1))
        self.restart_label = wx.StaticText(self.panel, label="Set Maximum Restart Attempts:")
        self.restart_spinbox = wx.SpinCtrl(self.panel, value="5", min=1, max=10)
        self.max_thread_note = wx.StaticText(self.panel, label=f"Số luồng max mà máy bạn có thể chạy là: {self.cpu_cores}")
        # Ban đầu chỉ add các thành phần cho manual
        self.thread_box.Add(self.thread_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.thread_box.Add(self.thread_spinbox, flag=wx.RIGHT, border=8)
        self.thread_box.Add(self.captcha_checkbox, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.thread_box.Add(self.captcha_ext_url_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=4)
        self.thread_box.Add(self.captcha_ext_url, flag=wx.RIGHT, border=8)
        self.thread_box.Add(self.restart_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=16)
        self.thread_box.Add(self.restart_spinbox, flag=wx.RIGHT, border=8)
        vbox.Add(self.thread_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        vbox.Add(self.max_thread_note, flag=wx.LEFT | wx.TOP, border=12)

        # Lựa chọn proxy tĩnh/động
        proxy_box = wx.BoxSizer(wx.HORIZONTAL)
        self.proxy_radio_static = wx.RadioButton(self.panel, label="Proxy tĩnh", style=wx.RB_GROUP)
        self.proxy_radio_dynamic = wx.RadioButton(self.panel, label="Proxy động")
        self.proxy_radio_none = wx.RadioButton(self.panel, label="Không dùng proxy")
        self.proxy_radio_static.SetValue(True)
        self.proxy_radio_static.Bind(wx.EVT_RADIOBUTTON, self.on_proxy_type_change)
        self.proxy_radio_dynamic.Bind(wx.EVT_RADIOBUTTON, self.on_proxy_type_change)
        self.proxy_radio_none.Bind(wx.EVT_RADIOBUTTON, self.on_proxy_type_change)
        proxy_box.Add(wx.StaticText(self.panel, label="Proxy type:"), flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        proxy_box.Add(self.proxy_radio_static, flag=wx.RIGHT, border=8)
        proxy_box.Add(self.proxy_radio_dynamic, flag=wx.RIGHT, border=8)
        proxy_box.Add(self.proxy_radio_none, flag=wx.RIGHT, border=8)
        vbox.Add(proxy_box, flag=wx.ALL, border=10)

        # Nhập proxy tĩnh (nhiều dòng, đúng số thread)
        self.proxy_static_label = wx.StaticText(self.panel, label="Enter proxies (1 proxy per line, must match thread count):")
        vbox.Add(self.proxy_static_label, flag=wx.LEFT | wx.TOP, border=10)
        self.proxy_static_text = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE)
        self.proxy_static_text.SetMinSize(wx.Size(-1, 80))
        vbox.Add(self.proxy_static_text, proportion=0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # --- Proxy động UI ---
        self.proxy_dynamic_sizer = wx.BoxSizer(wx.VERTICAL)
        self.proxy_dynamic_label = wx.StaticText(self.panel, label="Proxy động:")
        self.proxy_dynamic_sizer.Add(self.proxy_dynamic_label, proportion=0, flag=wx.LEFT | wx.TOP, border=10)
        self.proxy_dynamic_label.Hide()
        # Host:Port nhập + Số lần dùng
        proxy_hostport_row = wx.BoxSizer(wx.HORIZONTAL)
        self.proxy_dynamic_hostport = wx.TextCtrl(self.panel, style=0, value="", size=(200, -1))
        proxy_hostport_row.Add(self.proxy_dynamic_hostport, proportion=0, flag=wx.RIGHT, border=8)
        self.proxy_dynamic_use_label = wx.StaticText(self.panel, label="Số lần dùng mỗi proxy:")
        proxy_hostport_row.Add(self.proxy_dynamic_use_label, proportion=0, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        self.proxy_dynamic_use_count = wx.SpinCtrl(self.panel, value="1", min=1, max=100)
        proxy_hostport_row.Add(self.proxy_dynamic_use_count, proportion=0)
        self.proxy_dynamic_sizer.Add(proxy_hostport_row, proportion=0, flag=wx.LEFT | wx.TOP, border=10)
        self.proxy_dynamic_hostport.Hide()
        self.proxy_dynamic_use_label.Hide()
        self.proxy_dynamic_use_count.Hide()
        # Nút lấy danh sách proxy
        self.proxy_dynamic_fetch_btn = wx.Button(self.panel, label="Lấy danh sách proxy")
        self.proxy_dynamic_sizer.Add(self.proxy_dynamic_fetch_btn, proportion=0, flag=wx.LEFT | wx.TOP, border=10)
        self.proxy_dynamic_fetch_btn.Hide()
        self.proxy_dynamic_fetch_btn.Bind(wx.EVT_BUTTON, self.on_fetch_dynamic_proxy)
        # Danh sách proxy
        self.proxy_dynamic_scroll = wx.BoxSizer(wx.HORIZONTAL)
        self.proxy_dynamic_listbox = wx.CheckListBox(self.panel, choices=[], size=(400, 120))
        self.proxy_dynamic_listbox.SetMinSize(wx.Size(-1, 80))
        self.proxy_dynamic_scroll.Add(self.proxy_dynamic_listbox, 1, wx.EXPAND)
        self.proxy_dynamic_sizer.Add(self.proxy_dynamic_scroll, proportion=0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        self.proxy_dynamic_listbox.Hide()
        self.proxy_dynamic_listbox.Bind(wx.EVT_CHECKLISTBOX, self.on_dynamic_proxy_check)
        vbox.Add(self.proxy_dynamic_sizer, proportion=0, flag=wx.EXPAND)

        # Load TXT file cho nhiệm vụ và xpath
        txt_box = wx.BoxSizer(wx.HORIZONTAL)
        self.txt_label = wx.StaticText(self.panel, label="Load TXT File (Comments & XPath):")
        self.txt_button = wx.Button(self.panel, label="Load TXT File")
        self.txt_button.Bind(wx.EVT_BUTTON, self.load_txt_file)
        txt_box.Add(self.txt_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        txt_box.Add(self.txt_button)
        vbox.Add(txt_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        self.txt_content = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.txt_content.SetMinSize(wx.Size(-1, 200))
        self.txt_content.SetMaxSize(wx.Size(-1, 200))
        vbox.Add(self.txt_content, proportion=0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Load CSV file for tasks (chỉ cho Auto)
        csv_box = wx.BoxSizer(wx.HORIZONTAL)
        self.csv_label = wx.StaticText(self.panel, label="Load CSV File (Tasks):")
        self.csv_button = wx.Button(self.panel, label="Load CSV File")
        self.csv_button.Bind(wx.EVT_BUTTON, self.load_csv_file)
        csv_box.Add(self.csv_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
        csv_box.Add(self.csv_button)
        vbox.Add(csv_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        self.csv_content = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.csv_content.SetMinSize(wx.Size(-1, 80))
        self.csv_content.SetMaxSize(wx.Size(-1, 80))
        vbox.Add(self.csv_content, proportion=0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        # Thêm bảng hiển thị CSV
        self.csv_grid = wx.grid.Grid(self.panel)
        self.csv_grid.CreateGrid(0, 0)
        self.csv_grid.Hide()
        vbox.Add(self.csv_grid, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        # Nút Run
        self.run_button = wx.Button(self.panel, label="Run Bot")
        self.run_button.Bind(wx.EVT_BUTTON, self.run_bot)
        vbox.Add(self.run_button, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, border=10)

        # Panel trạng thái bot
        self.status_panel = wx.Panel(self.panel)
        status_vbox = wx.BoxSizer(wx.VERTICAL)
        # Tổng kết
        self.summary_text = wx.StaticText(self.status_panel, label="Tổng số acc đã làm: 0 | Hoàn thành: 0 | Lỗi: 0")
        status_vbox.Add(self.summary_text, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)
        # Bảng trạng thái
        self.status_grid = wx.grid.Grid(self.status_panel)
        self.status_grid.CreateGrid(0, 7)
        for i, col in enumerate(["Thread", "Thời gian bắt đầu", "Proxy tĩnh", "Proxy động", "Không dùng proxy", "Acc success", "Acc error", "Close"]):
            if i < 7:
                self.status_grid.SetColLabelValue(i, col)
        self.status_grid.SetMinSize(wx.Size(650, 220))
        self.status_grid.EnableEditing(False)
        self.status_grid.EnableGridLines(True)
        self.status_grid.SetColLabelAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        self.status_grid.SetLabelBackgroundColour(wx.Colour(220, 220, 220))
        self.status_grid.SetMargins(10, 10)
        # Đặt font nhỏ cho status_grid
        font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.status_grid.SetDefaultCellFont(font)
        self.status_grid.SetLabelFont(font)
        status_vbox.Add(self.status_grid, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=20)
        # Nút Close all bot
        self.close_all_btn = wx.Button(self.status_panel, label="Close all bot")
        self.close_all_btn.Bind(wx.EVT_BUTTON, self.on_close_all_bot)
        self.switch_all_acc_btn = wx.Button(self.status_panel, label="Chuyển all acc")
        self.switch_all_acc_btn.Bind(wx.EVT_BUTTON, self.on_switch_all_acc)
        btn_hbox = wx.BoxSizer(wx.HORIZONTAL)
        btn_hbox.Add(self.close_all_btn, flag=wx.RIGHT, border=10)
        btn_hbox.Add(self.switch_all_acc_btn, flag=wx.RIGHT, border=10)
        status_vbox.Add(btn_hbox, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)
        self.status_panel.SetSizer(status_vbox)
        vbox.Add(self.status_panel, proportion=1, flag=wx.EXPAND | wx.ALL, border=0)
        self.status_panel.Hide()

        self.panel.SetSizer(vbox)
        self.panel.SetMinSize(wx.Size(900, 900))
        self.update_proxy_input_visibility()
        self.update_mode_layout()

        # Timer cập nhật real-time
        self.status_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_status_timer, self.status_timer)
        self.status_grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.on_grid_cell_click)

    def on_mode_change(self, event):
        if self.mode_radio_manual.GetValue():
            self.mode = "manual"
        else:
            self.mode = "auto"
        # Khi chuyển chế độ, cập nhật lại giao diện cho phù hợp
        self.update_mode_layout()

    def update_mode_layout(self):
        # Xóa các thành phần khỏi thread_box trước khi add lại, KHÔNG xóa widget con!
        self.thread_box.Clear(False)
        if self.mode == "manual":
            self.thread_box.Add(self.thread_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
            self.thread_box.Add(self.thread_spinbox, flag=wx.RIGHT, border=8)
            self.thread_box.Add(self.captcha_checkbox, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
            self.thread_box.Add(self.captcha_ext_url_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=4)
            self.thread_box.Add(self.captcha_ext_url, flag=wx.RIGHT, border=8)
            self.restart_label.Hide()
            self.restart_spinbox.Hide()
            self.captcha_ext_url_label.Show()
            self.captcha_ext_url.Show()
            # Hiện tất cả các thành phần cho Manual
            self.profile_label.Show()
            self.profile_button.Show()
            self.profile_listbox.Show()
            self.delete_button.Show()
            self.proxy_radio_static.Show()
            self.proxy_radio_dynamic.Show()
            self.proxy_radio_none.Show()
            self.proxy_static_label.Show()
            self.proxy_static_text.Show()
            self.proxy_dynamic_label.Show(self.proxy_type != "none")
            self.proxy_dynamic_hostport.Show(self.proxy_type != "none")
            self.proxy_dynamic_fetch_btn.Show(self.proxy_type != "none")
            self.proxy_dynamic_listbox.Show(self.proxy_type != "none")
            self.txt_label.Show()
            self.txt_button.Show()
            self.txt_content.Show()
            self.run_button.Show()
            # Ẩn các thành phần chỉ dành cho Auto
            self.csv_label.Hide()
            self.csv_button.Hide()
            self.csv_content.Hide()
            self.csv_grid.Hide()
        elif self.mode == "auto":
            self.thread_box.Add(self.thread_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
            self.thread_box.Add(self.thread_spinbox, flag=wx.RIGHT, border=8)
            self.thread_box.Add(self.captcha_checkbox, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=8)
            self.thread_box.Add(self.captcha_ext_url_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=4)
            self.thread_box.Add(self.captcha_ext_url, flag=wx.RIGHT, border=8)
            self.thread_box.Add(self.restart_label, flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, border=16)
            self.thread_box.Add(self.restart_spinbox, flag=wx.RIGHT, border=8)
            self.restart_label.Show()
            self.restart_spinbox.Show()
            self.captcha_ext_url_label.Show()
            self.captcha_ext_url.Show()
            # Giao diện Auto: hiện thêm các thành phần dưới đây
            self.profile_label.Show()
            self.profile_button.Show()
            self.profile_listbox.Show()
            self.delete_button.Show()
            self.proxy_radio_static.Show()
            self.proxy_radio_dynamic.Show()
            self.proxy_radio_none.Show()
            self.proxy_static_label.Show()
            self.proxy_static_text.Show()
            self.proxy_dynamic_label.Show(self.proxy_type != "none")
            self.proxy_dynamic_hostport.Show(self.proxy_type != "none")
            self.proxy_dynamic_fetch_btn.Show(self.proxy_type != "none")
            self.proxy_dynamic_listbox.Show(self.proxy_type != "none")
            self.txt_label.Show()
            self.txt_button.Show()
            self.txt_content.Show()
            self.run_button.Show()
            # Hiện các thành phần chỉ dành cho Auto
            self.csv_label.Show()
            self.csv_button.Show()
            self.csv_content.Show()
            self.csv_grid.Show()
        self.panel.Layout()
        self.panel.FitInside()

    def on_select_json(self, event):
        # Dùng tkinter để chọn file .json
        root = Tk()
        root.withdraw()
        file_path = tk_filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            self.json_path = file_path
            self.json_path_ctrl.SetValue(file_path)
        root.destroy()

    def on_select_excel(self, event):
        root = Tk()
        root.withdraw()
        file_path = tk_filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
        if file_path:
            self.excel_path_ctrl.SetValue(file_path)
        root.destroy()

    def on_select_errorlog(self, event):
        root = Tk()
        root.withdraw()
        file_path = tk_filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
        if file_path:
            self.errorlog_path_ctrl.SetValue(file_path)
        root.destroy()

    def browse_multiple_folders(self, event):
        dialog = wx.DirDialog(self, "Select Profile Folders", style=wx.DD_MULTIPLE)
        if dialog.ShowModal() == wx.ID_OK:
            folder_paths = dialog.GetPaths()
            for folder_path in folder_paths:
                if folder_path not in self.selected_profiles:
                    self.selected_profiles.append(folder_path)
            self.profile_listbox.Set(self.selected_profiles)
        dialog.Destroy()

    def delete_selected_folder(self, event):
        selections = self.profile_listbox.GetSelections()
        for idx in reversed(selections):
            del self.selected_profiles[idx]
        self.profile_listbox.Set(self.selected_profiles)

    def on_proxy_type_change(self, event):
        if self.proxy_radio_static.GetValue():
            self.proxy_type = "static"
        elif self.proxy_radio_dynamic.GetValue():
            self.proxy_type = "dynamic"
        else:
            self.proxy_type = "none"
        self.update_proxy_input_visibility()

    def update_proxy_input_visibility(self):
        if self.proxy_type == "static":
            self.proxy_static_label.Show()
            self.proxy_static_text.Show()
            self.proxy_dynamic_label.Hide()
            self.proxy_dynamic_hostport.Hide()
            self.proxy_dynamic_use_label.Hide()
            self.proxy_dynamic_use_count.Hide()
            self.proxy_dynamic_fetch_btn.Hide()
            self.proxy_dynamic_listbox.Hide()
        elif self.proxy_type == "dynamic":
            self.proxy_static_label.Hide()
            self.proxy_static_text.Hide()
            self.proxy_dynamic_label.Show()
            self.proxy_dynamic_hostport.Show()
            self.proxy_dynamic_use_label.Show()
            self.proxy_dynamic_use_count.Show()
            self.proxy_dynamic_fetch_btn.Show()
            self.proxy_dynamic_listbox.Show()
        else:  # none
            self.proxy_static_label.Hide()
            self.proxy_static_text.Hide()
            self.proxy_dynamic_label.Hide()
            self.proxy_dynamic_hostport.Hide()
            self.proxy_dynamic_use_label.Hide()
            self.proxy_dynamic_use_count.Hide()
            self.proxy_dynamic_fetch_btn.Hide()
            self.proxy_dynamic_listbox.Hide()
        self.panel.Layout()
        self.panel.FitInside()

    def load_txt_file(self, event):
        with wx.FileDialog(self, "Open TXT File", wildcard="Text Files (*.txt)|*.txt", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_OK:
                file_path = file_dialog.GetPath()
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.mission_text = content.strip()
                    self.txt_content.SetValue(f"Mission Text:\n{self.mission_text}")

    def load_csv_file(self, event):
        with wx.FileDialog(self, "Open CSV File", wildcard="CSV Files (*.csv)|*.csv", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_OK:
                file_path = file_dialog.GetPath()
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.csv_content.SetValue(content)
                    # Hiển thị lên bảng
                    self.show_csv_table(content)

    def show_csv_table(self, content):
        import csv
        import io
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        if not rows:
            self.csv_grid.Hide()
            return
        n_rows = len(rows)
        n_cols = max(len(row) for row in rows)
        self.csv_grid.ClearGrid()
        if self.csv_grid.GetNumberRows() > 0:
            self.csv_grid.DeleteRows(0, self.csv_grid.GetNumberRows())
        if self.csv_grid.GetNumberCols() > 0:
            self.csv_grid.DeleteCols(0, self.csv_grid.GetNumberCols())
        self.csv_grid.AppendRows(n_rows)
        self.csv_grid.AppendCols(n_cols)
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.csv_grid.SetCellValue(r, c, val)
        self.csv_grid.Show()
        self.panel.Layout()
        self.panel.FitInside()

    def on_fetch_dynamic_proxy(self, event):
        import requests
        hostport = self.proxy_dynamic_hostport.GetValue().strip()
        if not hostport:
            wx.MessageBox("Vui lòng nhập host:port!", "Error", wx.ICON_ERROR)
            return
        try:
            url = f"http://{hostport}/proxy_list"
            resp = requests.get(url, timeout=10)
            proxies = resp.json()
            proxy_choices = []
            for p in proxies:
                name = f"{p.get('system','')}:{p.get('proxy_port','')}"
                proxy_choices.append(name)
            self.dynamic_proxies = proxy_choices
            self.proxy_dynamic_listbox.Set(proxy_choices)
            for i in range(self.proxy_dynamic_listbox.GetCount()):
                self.proxy_dynamic_listbox.Check(i, False)
            self.selected_dynamic_proxies = []
        except Exception as e:
            wx.MessageBox(f"Không lấy được proxy: {e}", "Error", wx.ICON_ERROR)
            self.dynamic_proxies = []
            self.proxy_dynamic_listbox.Set([])
        self.panel.Layout()
        self.panel.FitInside()

    def on_dynamic_proxy_check(self, event):
        thread_count = self.thread_spinbox.GetValue()
        checked = [i for i in range(self.proxy_dynamic_listbox.GetCount()) if self.proxy_dynamic_listbox.IsChecked(i)]
        if len(checked) > thread_count:
            self.proxy_dynamic_listbox.Check(event.GetInt(), False)
            wx.MessageBox(f"Chỉ được chọn đúng {thread_count} proxy!", "Error", wx.ICON_ERROR)
            return
        self.selected_dynamic_proxies = [self.dynamic_proxies[i] for i in checked]

    def show_status_panel(self, show=True):
        self.status_panel.Show(show)
        for child in self.panel.GetChildren():
            if child != self.status_panel:
                child.Show(not show)
        self.panel.Layout()
        self.panel.FitInside()
        if show:
            self.update_status_grid()
            self.status_timer.Start(1000)
        else:
            if hasattr(self, 'status_timer'):
                self.status_timer.Stop()

    def on_close_all_bot(self, event):
        dlg = wx.MessageDialog(self, "Bạn có chắc chắn muốn dừng toàn bộ bot?", "Xác nhận", wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            # Dừng toàn bộ thread bot
            for thread_id in list(self.stop_thread_flags.keys()):
                if not self.stop_thread_flags[thread_id].is_set():
                        # Set flag dừng acc và dừng thread
                    self.profile_bots[thread_id].stop()
                    self.skip_acc_flags[thread_id].set()
                    self.stop_thread_flags[thread_id].set()
                    # Dừng bot nếu còn sống
                    try:
                        if self.profile_bots[thread_id]:
                            self.profile_bots[thread_id].stop()
                    except Exception as e:
                        print(f"Lỗi khi stop bot thread {thread_id}: {e}")
                    # Cập nhật trạng thái acc đang chạy về rỗng
                    delete_bot_running_details_by_thread(thread_id)
            self.update_status_grid()
            self.show_status_panel(False)
        dlg.Destroy()

    def run_bot(self, event):     
        threading.Thread(target=self.run_bot_worker, daemon=True).start()

    def run_bot_worker(self):
        self.profiles = self.selected_profiles
        print(f"profiles: [{self.profiles}]")
        self.thread_count = self.thread_spinbox.GetValue()
        self.mission_text_run = self.mission_text
        self.list_url = extract_urls_from_text(self.mission_text)
        self.proxy_type_run = self.proxy_type
        self.proxies_run = []
        self.sheet_id_run = self.sheetid_ctrl.GetValue().strip()
        self.json_path_run = self.json_path
        self.restart_attempts_run = self.restart_spinbox.GetValue()
        self.path_data_excel_run = self.excel_path_ctrl.GetValue()
        self.sheet_name_errorlog_run = self.sheetname_ctrl.GetValue().strip()
        self.log_file_run = (self.errorlog_path_ctrl.GetValue(), self.sheet_name_errorlog_run)
        self.profile_notOk_run = process_excel_data(self.path_data_excel_run)
        self.sheet_name_discord_run = self.sheetname_discord_ctrl.GetValue().strip()

        # Kiểm tra các điều kiện và hiển thị thông báo lỗi nếu cần
        if len(self.profile_notOk_run) < 0:
            wx.CallAfter(wx.MessageBox, f"Các profile không hợp lệ từ execl:{self.path_data_excel_run}", "Error", wx.ICON_ERROR)
            return

        try:
            self.zoom_percent_run = int(self.zoom_spinbox.GetValue())
        except Exception:
            wx.CallAfter(wx.MessageBox, "Zoom phải là số nguyên!", "Error", wx.ICON_ERROR)
            return

        try:
            self.width_run = int(self.width_text.GetValue())
            self.height_run = int(self.height_text.GetValue())
        except Exception:
            wx.CallAfter(wx.MessageBox, "Width/Height phải là số nguyên!", "Error", wx.ICON_ERROR)
            return

        # Lấy kích thước màn hình
        display = wx.Display()
        self.screen_width_run, self.screen_height_run = display.GetGeometry().GetSize()
        print(f"screen_width,screen_height: {self.screen_width_run},{self.screen_height_run}")

        # Tính toán kích thước và vị trí cho mỗi cửa sổ
        self.window_dimensions = self.calculate_window_dimensions(
            self.screen_width_run,
            self.screen_height_run,
            self.thread_count
        )

        # Các kiểm tra điều kiện khác
        if len(self.profiles) < self.thread_count:
            wx.CallAfter(wx.MessageBox, f"Số lượng profile ({len(self.profiles)}) phải lớn hơn hoặc bằng số luồng ({self.thread_count})!", "Error", wx.ICON_ERROR)
            return

        # Xử lý proxy
        if self.proxy_type_run == "static":
            self.proxies_run = [p.strip() for p in self.proxy_static_text.GetValue().splitlines() if p.strip()]
            if len(self.proxies_run) != self.thread_count:
                wx.CallAfter(wx.MessageBox, "Số lượng proxy phải đúng bằng số thread!", "Error", wx.ICON_ERROR)
                return
        elif self.proxy_type_run == "dynamic":
            self.proxies_run = self.selected_dynamic_proxies
            if len(self.proxies_run) != self.thread_count:
                wx.CallAfter(wx.MessageBox, "Số lượng proxy phải đúng bằng số luồng!", "Error", wx.ICON_ERROR)
                return
        else:
            if self.thread_count > self.cpu_cores:
                wx.CallAfter(wx.MessageBox, f"Số luồng không được vượt quá {self.cpu_cores}!", "Error", wx.ICON_ERROR)
                return
            self.proxies_run = [None] * self.thread_count

        # Các kiểm tra điều kiện khác
        if not self.profiles:
            wx.CallAfter(wx.MessageBox, "Vui lòng chọn ít nhất một profile!", "Error", wx.ICON_ERROR)
            return
        if not self.json_path_run:
            wx.CallAfter(wx.MessageBox, "Vui lòng chọn file Google API .json!", "Error", wx.ICON_ERROR)
            return
        if not self.sheet_id_run:
            wx.CallAfter(wx.MessageBox, "Vui lòng nhập SHEET_ID!", "Error", wx.ICON_ERROR)
            return

        # Khởi tạo queue và xử lý profiles
        self.url_run = "https://discord.com/app"
        self.profile_queue_run = queue.Queue()
        self.list_index_run = {}
        print(self.profile_notOk_run)
        for profile in self.profiles:
            print(f"profile: [{profile}]")
            x = stt_Acc(profile)
            print(f"x: [{x}]")
            flag = 0
            for i in range(len(self.profile_notOk_run)):
                if x == self.profile_notOk_run[i][1]:
                    flag = 1
                    self.list_index_run[x] = self.profile_notOk_run[i][0]
                    break
            if flag == 0:
                continue
            self.profile_queue_run.put(profile)

        if self.profile_queue_run.empty():
            wx.CallAfter(wx.MessageBox, "Không có profile nào để chạy!", "Error", wx.ICON_ERROR)
            wx.CallAfter(self.show_status_panel, False)
            return

        # Ghi thông tin chạy bot vào Excel
        running_details = []
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for thread_index in range(self.thread_count):
            if self.proxy_type_run == "static":
                proxy_static = self.proxies_run[thread_index] if self.proxies_run else ''
                proxy_dynamic = ''
                no_proxy = 0
            elif self.proxy_type_run == "dynamic":
                proxy_static = ''
                proxy_dynamic = self.proxies_run[thread_index] if self.proxies_run else ''
                no_proxy = 0
            else:
                proxy_static = ''
                proxy_dynamic = ''
                no_proxy = 1
            running_details.append([
                thread_index + 1,
                now_str,
                proxy_static if proxy_static else '0',
                proxy_dynamic if proxy_dynamic else '0',
                no_proxy,
                '',   # Acc success
                '',    # Acc error
                '',    # Acc đang chạy
                '',    # Các acc đã close
            ])

        columns = ["Thread", "Thời gian bắt đầu", "Proxy tĩnh", "Proxy động", "Không dùng proxy", "Acc success", "Acc error", "Acc đang chạy", "Các acc đã close"]
        write_bot_running_details(running_details, columns, "Bot_Running_Details.xlsx")
        wx.CallAfter(self.show_status_panel, True)

        # Khởi tạo các biến cho proxy
        self.proxy_use_count_run = [0 for _ in self.proxies_run]
        self.max_use_run = self.proxy_dynamic_use_count.GetValue() if self.proxy_type_run != "none" else 1
        self.hostport_run = self.proxy_dynamic_hostport.GetValue().strip() if self.proxy_type_run != "none" else None

        def check_proxy_status(hostport, proxy):
            url = f"http://{hostport}/status?proxy={proxy}"
            try:
                resp = requests.get(url, timeout=5)
                data = resp.json()
                return data.get('status', False)
            except Exception:
                return False

        def reset_proxy(hostport, proxy):
            url = f"http://{hostport}/reset?proxy={proxy}"
            try:
                requests.get(url, timeout=5)
            except Exception:
                pass

        def worker(thread_index):
            # Lấy thông tin vị trí và kích thước cửa sổ cho thread này
            
            while not self.profile_queue_run.empty():
                window_info = self.window_dimensions[thread_index]         
                skip_event = self.skip_acc_flags[thread_index+1]
                stop_thread_event = self.stop_thread_flags[thread_index+1]
                if stop_thread_event.is_set():
                    print(f"[Thread {thread_index+1}] Đã nhận tín hiệu dừng thread, thoát thread.")
                    delete_bot_running_details_by_thread(thread_index+1)
                    break
                
                try:
                    profile = self.profile_queue_run.get_nowait()
                except queue.Empty:
                    break

                profile_name = os.path.basename(profile)
                update_bot_running_details_by_thread(
                    thread_id=thread_index+1,
                    update_dict={"Acc đang chạy": profile_name}
                )
                wx.CallAfter(self.set_acc_running, thread_index+1, profile_name)
                
                x = stt_Acc(profile_name)
                binary_location = os.path.join(profile, r"App\firefox64\firefox.exe")
                geckopath = os.path.join(profile, "geckodriver.exe")
                profile_path = os.path.join(profile, "Data", "profile")
                start_time = datetime.now()

                # Xử lý proxy
                if self.proxy_type_run != "none":
                    proxy_index = thread_index % len(self.proxies_run)
                    proxy = self.proxies_run[proxy_index]
                    print(f"[{profile_name}] Dùng proxy: {proxy}")
                    wait_proxy_count = 0
                    while not check_proxy_status(self.hostport_run, proxy):
                        print(f"Proxy {proxy} chưa sẵn sàng, đợi 2s...")
                        time.sleep(2)
                        wait_proxy_count += 1
                        if wait_proxy_count == 3 and self.proxy_type_run == "dynamic":
                            print(f"Reset proxy {proxy} sau 3 lần chờ...")
                            reset_proxy(self.hostport_run, proxy)
                            wait_proxy_count = 0
                else:
                    proxy = None

                # Khởi tạo DiscordBot với vị trí và kích thước đã tính toán
                captcha = self.captcha_checkbox.GetValue()
                while True:
                    bot = DiscordBot(
                        profile_path=profile_path,
                        url=self.url_run,
                        acc_name=profile_name,
                        position=(window_info['x'], window_info['y']),  # Thêm vị trí
                        size=(window_info['width'], window_info['height']),  # Thêm kích thước
                        geckopath=geckopath,
                        binary_location=binary_location,
                        mission_text=self.mission_text_run,
                        proxy=proxy,
                        SERVICE_ACCOUNT_FILE=self.json_path_run,
                        SHEET_ID=self.sheet_id_run,
                        sheet_name=self.sheet_name_discord_run,
                        zoom=self.zoom_percent_run,
                        size_goc=(window_info['width'], window_info['height']),  # Cập nhật size_goc
                        thread_index=thread_index,
                        restart_max=self.restart_attempts_run,
                        list_url=self.list_url,
                        log_file=self.log_file_run,
                        mode=self.mode,
                        stop_event=skip_event,
                        captcha=captcha,
                        captcha_ext_url=self.captcha_ext_url.GetValue()
                    )
                    
                    self.profile_bots[thread_index+1] = bot
                    result = bot.run()
                    elapsed = datetime.now() - start_time
                    mins, secs = divmod(int(elapsed.total_seconds()), 60)
                    elapsed_str = f"{mins} phút {secs} giây"
                    if result == True or self.chuyen_all_acc[thread_index+1] == True:
                        update_column_z_ok(self.path_data_excel_run, self.list_index_run[x])
                        try:
                            df = pd.read_excel("Bot_Running_Details.xlsx")
                            row = df[df['Thread'] == thread_index+1]
                            if not row.empty:
                                current = row.iloc[0]['Acc success']
                                try:
                                    acc_list = ast.literal_eval(current) if current and current != 'nan' else []
                                except Exception:
                                    acc_list = []
                            else:
                                acc_list = []
                        except Exception:
                            acc_list = []
                        acc_list.append((profile_name, elapsed_str))
                        update_bot_running_details_by_thread(
                            thread_id=thread_index+1,
                            update_dict={"Acc success": str(acc_list), "Acc đang chạy": ""}
                        )
                        wx.CallAfter(self.set_acc_running, thread_index+1, "")
                        if self.chuyen_all_acc[thread_index+1] == True:
                            self.chuyen_all_acc[thread_index+1] = False
                            self.skip_acc_flags[thread_index+1].clear()
                            self.profile_bots[thread_index+1]=None
                        break
                    elif result == "close":
                        # Đã bị dừng bởi skip_event/close acc, clear acc đang chạy, cập nhật Các acc đã close
                        if self.reset_acc_flags[thread_index+1] == 1:
                            print(f"[{profile_name}] Reset acc")
                        else:
                            print(f"[{profile_name}] Đã bị dừng bởi skip_event/close acc")
                            try:
                                df = pd.read_excel("Bot_Running_Details.xlsx")
                                row = df[df['Thread'] == thread_index+1]
                                if not row.empty:
                                    current = row.iloc[0]['Các acc đã close']
                                    try:
                                        acc_list = ast.literal_eval(current) if current and current != 'nan' else []
                                    except Exception:
                                        acc_list = []
                                else:
                                    acc_list = []
                            except Exception:
                                acc_list = []
                            acc_list.append(profile_name)
                            update_bot_running_details_by_thread(
                                thread_id=thread_index+1,
                                update_dict={"Các acc đã close": str(acc_list), "Acc đang chạy": ""}
                            )
                            wx.CallAfter(self.set_acc_running, thread_index+1, "")
                        self.profile_bots[thread_index+1]=None
                        self.skip_acc_flags[thread_index+1].clear()
                        if self.reset_acc_flags[thread_index+1] == 1:
                            self.reset_acc_flags[thread_index+1] = 0
                        else:
                            break
                    else:
                        # ACC ERROR
                        try:
                            df = pd.read_excel("Bot_Running_Details.xlsx")
                            row = df[df['Thread'] == thread_index+1]
                            if not row.empty:
                                current = row.iloc[0]['Acc error']
                                try:
                                    acc_list = ast.literal_eval(current) if current and current != 'nan' else []
                                except Exception:
                                    acc_list = []
                            else:
                                acc_list = []
                        except Exception:
                            acc_list = []
                        acc_list.append((profile_name, elapsed_str))
                        update_bot_running_details_by_thread(
                            thread_id=thread_index+1,
                            update_dict={"Acc error": str(acc_list), "Acc đang chạy": ""}
                        )
                        wx.CallAfter(self.set_acc_running, thread_index+1, "")
                        break
        for thread_index in range(self.thread_count):
            skip_event = threading.Event()
            stop_thread_event = threading.Event()
            self.skip_acc_flags[thread_index+1] = skip_event
            self.stop_thread_flags[thread_index+1] = stop_thread_event
            self.reset_acc_flags[thread_index+1] = 0
            self.chuyen_all_acc[thread_index+1] = False
            t = threading.Thread(target=worker, args=(thread_index,))
            self.threads_run[thread_index] = t
            t.start()
        for thread_index in range(self.thread_count):
            self.threads_run[thread_index].join()
        wx.CallAfter(wx.MessageBox, "Bot đã hoàn thành!", "Info", wx.ICON_INFORMATION)
        wx.CallAfter(self.show_status_panel, False)
        
    def on_status_timer(self, event):
        self.update_status_grid()

    def update_status_grid(self):
        df = load_status_grid_from_excel()
        if df is None:
            return
        n_rows, n_cols = df.shape
        col_order = [
            "Thread", "Thời gian bắt đầu", "Proxy tĩnh", "Proxy động", "Không dùng proxy",
            "Acc đang chạy", "Các acc đã close", "Acc success", "Acc error"
        ]
        for col in col_order:
            if col not in df.columns:
                df[col] = ""
        df = df[col_order]
        n_cols = len(col_order)
        self.status_grid.ClearGrid()
        if self.status_grid.GetNumberRows() < n_rows:
            self.status_grid.AppendRows(n_rows - self.status_grid.GetNumberRows())
        elif self.status_grid.GetNumberRows() > n_rows:
            self.status_grid.DeleteRows(0, self.status_grid.GetNumberRows() - n_rows)
        if self.status_grid.GetNumberCols() < n_cols+2:
            self.status_grid.AppendCols(n_cols+2 - self.status_grid.GetNumberCols())
        elif self.status_grid.GetNumberCols() > n_cols+2:
            self.status_grid.DeleteCols(0, self.status_grid.GetNumberCols() - (n_cols+2))
        # Kiểm tra dữ liệu proxy
        proxy_static_col = df["Proxy tĩnh"].astype(str)
        proxy_dynamic_col = df["Proxy động"].astype(str)
        has_static = any((v.strip() != '' and v.strip() != '0') for v in proxy_static_col)
        has_dynamic = any((v.strip() != '' and v.strip() != '0') for v in proxy_dynamic_col)
        # Đặt lại tên cột
        col_labels = [
            "Thread", "Thời gian chạy", "Proxy tĩnh", "Proxy động", "Không dùng proxy",
            "Acc đang chạy", "Các acc đã close", "Acc success", "Acc error", "Close acc", "Close thread", "Reset acc"
        ]
        col_widths = [60, 80, 80, 80, 80, 80, 80, 80, 80, 60, 60, 60]
        # Đảm bảo số cột của grid đúng với col_labels
        if self.status_grid.GetNumberCols() < len(col_labels):
            self.status_grid.AppendCols(len(col_labels) - self.status_grid.GetNumberCols())
        elif self.status_grid.GetNumberCols() > len(col_labels):
            self.status_grid.DeleteCols(0, self.status_grid.GetNumberCols() - len(col_labels))
        # Ẩn/hiện cột proxy và set label/size giữ nguyên như cũ
        if not has_static and not has_dynamic:
            # Ẩn cả 3 cột proxy
            for i in [2,3,4]:
                self.status_grid.SetColSize(i, 0)
                self.status_grid.SetColLabelValue(i, "")
        else:
            if has_static:
                self.status_grid.SetColSize(2, col_widths[2])
                self.status_grid.SetColLabelValue(2, col_labels[2])
            else:
                self.status_grid.SetColSize(2, 0)
                self.status_grid.SetColLabelValue(2, "")
            if has_dynamic:
                self.status_grid.SetColSize(3, col_widths[3])
                self.status_grid.SetColLabelValue(3, col_labels[3])
            else:
                self.status_grid.SetColSize(3, 0)
                self.status_grid.SetColLabelValue(3, "")
            # Nếu chỉ có 1 loại proxy, ẩn cột 'Không dùng proxy'
            if has_static and not has_dynamic:
                self.status_grid.SetColSize(4, 0)
                self.status_grid.SetColLabelValue(4, "")
            elif has_dynamic and not has_static:
                self.status_grid.SetColSize(4, 0)
                self.status_grid.SetColLabelValue(4, "")
            else:
                self.status_grid.SetColSize(4, col_widths[4])
                self.status_grid.SetColLabelValue(4, col_labels[4])
        # Các cột còn lại
        for i in [0,1,5,6,7,8,9,10,11]:
            self.status_grid.SetColLabelValue(i, col_labels[i])
            self.status_grid.SetColSize(i, col_widths[i])
        self.status_grid.SetColLabelAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        self.status_grid.EnableEditing(False)
        for r in range(n_rows):
            for c in range(n_cols):
                val = str(df.iloc[r, c]) if not pd.isna(df.iloc[r, c]) else ""
                if c == 1:
                    try:
                        t0 = datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
                        elapsed = datetime.now() - t0
                        mins, secs = divmod(int(elapsed.total_seconds()), 60)
                        val = f"{mins} phút {secs} giây"
                    except Exception:
                        pass
                self.status_grid.SetCellValue(r, c, val)
                attr = wx.grid.GridCellAttr()
                attr.SetAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
                self.status_grid.SetAttr(r, c, attr)
            self.status_grid.SetCellRenderer(r, 6, ButtonRenderer("Chi tiết"))  # Các acc đã close
            self.status_grid.SetCellRenderer(r, 7, ButtonRenderer("Chi tiết"))
            self.status_grid.SetCellRenderer(r, 8, ButtonRenderer("Chi tiết"))
            self.status_grid.SetCellRenderer(r, 9, IconRenderer())
            self.status_grid.SetCellRenderer(r, 10, IconRenderer())
            self.status_grid.SetCellRenderer(r, 11, IconRenderer())  # Reset acc
        self.status_grid.ForceRefresh()

    def on_grid_cell_click(self, event):
        row, col = event.GetRow(), event.GetCol()
        df = load_status_grid_from_excel()
        if df is None:
            return
        col_labels = [
            "Thread", "Thời gian chạy", "Proxy tĩnh", "Proxy động", "Không dùng proxy",
            "Acc đang chạy", "Các acc đã close", "Acc success", "Acc error", "Close acc", "Close thread", "Reset acc"
        ]
        if col == 6:
            accs = df.iloc[row, 6]
            wx.MessageBox(f"Chi tiết các acc đã close dòng {row+1}:\n{accs}")
        elif col == 7:
            wx.MessageBox(f"Chi tiết acc success dòng {row+1}")
        elif col == 8:
            wx.MessageBox(f"Chi tiết acc error dòng {row+1}")
        elif col == len(col_labels)-1:  # Reset acc
            thread_id = df.iloc[row, 0]
            acc_running = self.current_acc_running.get(thread_id, "")
            if acc_running:
                dlg = wx.MessageDialog(self, f"Bạn có chắc chắn muốn reset acc '{acc_running}' của thread {thread_id}?", "Xác nhận", wx.YES_NO | wx.ICON_QUESTION)
                if dlg.ShowModal() == wx.ID_YES:
                    try:
                        self.skip_acc_flags[thread_id].set()
                        self.profile_bots[thread_id].stop()
                        self.reset_acc_flags[thread_id] = 1
                    except Exception as e:
                        print(f"Lỗi khi reset acc trên thread {thread_id}: {e}")
                dlg.Destroy()
        elif col == len(col_labels)-3:  # Close acc
            thread_id = df.iloc[row, 0]
            acc_running = self.current_acc_running.get(thread_id, "")
            if acc_running:
                dlg = wx.MessageDialog(self, f"Bạn có chắc chắn muốn close acc '{acc_running}' của thread {thread_id}?", "Xác nhận", wx.YES_NO | wx.ICON_QUESTION)
                if dlg.ShowModal() == wx.ID_YES:
                    # Đánh dấu skip acc cho thread này
                    if thread_id in self.skip_acc_flags:
                        self.skip_acc_flags[thread_id].set()
                        self.profile_bots[thread_id].stop()
                dlg.Destroy()
        elif col == len(col_labels)-2:  # Close thread
            thread_id = df.iloc[row, 0]
            print(f"[{thread_id}] Đã chọn xóa thread")
            dlg = wx.MessageDialog(self, f"Bạn có chắc chắn muốn xóa thread {thread_id}? (Acc đang chạy trên thread này cũng sẽ bị dừng)", "Xác nhận", wx.YES_NO | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_YES:
                # Dừng acc đang chạy trên thread này nếu có
                if hasattr(self, 'profile_bots') and thread_id in self.profile_bots and self.profile_bots[thread_id]:
                    try:
                        self.skip_acc_flags[thread_id].set()
                        self.stop_thread_flags[thread_id].set()
                        self.profile_bots[thread_id].stop()
                    except Exception as e:
                        print(f"Lỗi khi stop acc trên thread {thread_id}: {e}")
                # KHÔNG join thread ở đây để tránh treo GUI
                # Cập nhật trạng thái acc đang chạy về rỗng
                delete_bot_running_details_by_thread(thread_id)
                self.update_status_grid()
            dlg.Destroy()
        else:
            event.Skip()

    def set_acc_running(self, thread_index, acc_name):
        self.current_acc_running[thread_index] = acc_name

    def calculate_window_dimensions(self, screen_width, screen_height, thread_count):
        """
        Tính toán kích thước và vị trí cho mỗi cửa sổ Firefox dựa trên kích thước màn hình và số luồng
        """
        # Tính toán chiều rộng cho mỗi cửa sổ
        screen_height-=60
        window_width = screen_width // thread_count
        
        # Đảm bảo chiều rộng tối thiểu là 400px
        if window_width < 400:
            window_width = 400
            thread_per_row = screen_width // window_width
        else:
            thread_per_row = thread_count
        
        # Tính số hàng cần thiết
        num_rows = (thread_count + thread_per_row - 1) // thread_per_row
        
        # Tính chiều cao cho mỗi cửa sổ
        window_height = screen_height // num_rows
        
        # Tạo danh sách vị trí và kích thước cho mỗi cửa sổ
        windows = []
        for i in range(thread_count):
            row = i // thread_per_row
            col = i % thread_per_row
            x = col * window_width
            y = row * window_height
            windows.append({
                'index': i,
                'x': x,
                'y': y,
                'width': window_width,
                'height': window_height,
                'name': f'Thread {i+1}'
            })
        
        return windows

    def on_switch_all_acc(self, event):
        dlg = wx.MessageDialog(self, "Bạn có chắc chắn muốn chuyển toàn bộ bot?", "Xác nhận", wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            # Dừng toàn bộ thread bot
            
            for thread_id in list(self.stop_thread_flags.keys()):
                if not self.stop_thread_flags[thread_id].is_set():
                        # Set flag dừng acc và dừng thread
                    self.chuyen_all_acc[thread_id] =  True
                    self.profile_bots[thread_id].stop()
                    self.skip_acc_flags[thread_id].set()
                    
            self.update_status_grid()
        dlg.Destroy()

def extract_urls_from_text(text):
    # Regex tìm các đường dẫn bắt đầu bằng http hoặc https
    urls = re.findall(r'https?://[^\s)]+', text)
    return urls

# # ⚙️ TÍCH HỢP PREVIEW FIREFOX VÀO BOT

# === HÀM TÌM CỬA SỔ FIREFOX ===
def find_firefox_window(profile_name):
    for w in gw.getWindowsWithTitle('Mozilla Firefox'):
        if profile_name in w.title:
            return w
    return None

# === LỚP PREVIEW MỖI PROFILE ===
class FirefoxPreview(wx.Frame):
    def __init__(self, parent, title, firefox_hwnd, width, height, zoom):
        scaled_width = int(width * zoom / 100)
        scaled_height = int(height * zoom / 100)

        wx.Frame.__init__(self, parent, title=title, size=(scaled_width + 10, scaled_height + 30))
        panel = wx.Panel(self)

        # Gắn cửa sổ Firefox vào panel
        win32gui.SetParent(firefox_hwnd, panel.GetHandle())
        win32gui.MoveWindow(firefox_hwnd, 0, 0, scaled_width, scaled_height, True)

        self.Show()

# === HÀM KHỞI TẠO PREVIEW SAU KHI CHẠY PROFILE ===
def start_preview_for_profile(profile_name, width, height, zoom):
    def wait_and_embed():
        time.sleep(3)  # chờ Firefox mở ổn định
        firefox_win = find_firefox_window(profile_name)
        if firefox_win:
            hwnd = firefox_win._hWnd
            app = wx.App(False)
            FirefoxPreview(None, f"Preview - {profile_name}", hwnd, width, height, zoom)
            app.MainLoop()
        else:
            print(f"❌ Không tìm thấy cửa sổ Firefox cho profile: {profile_name}")

    t = Thread(target=wait_and_embed)
    t.daemon = True
    t.start()

# === CÁCH GỌI SAU MỖI PROFILE CHẠY ===
# Trong worker() trong run_bot():
# start_preview_for_profile(profile_name, size_goc[0], size_goc[1], zoom_percent)

if __name__ == "__main__":
    app = wx.App(False)
    window = MainWindow()
    window.Show()
    app.MainLoop()