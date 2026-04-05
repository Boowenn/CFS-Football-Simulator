#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CFS 足球模拟器 - 游戏修改器 v1.0
Windows 桌面版 | 点击即用
"""

import sqlite3
import shutil
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

# ─── 路径检测 ────────────────────────────────────────────
def _detect_game_dir():
    """自动检测游戏根目录，兼容 .py 运行和 PyInstaller .exe 运行"""
    # PyInstaller 打包后用 sys.executable 的目录，否则用 __file__ 的目录
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))

    # 情况1: 运行位置本身就是游戏根目录 (CFS/)
    candidate = os.path.join(exe_dir, "CFS_Data", "StreamingAssets")
    if os.path.isdir(candidate):
        return exe_dir

    # 情况2: 运行位置在子目录 (CFS/Trainer/)
    parent = os.path.join(exe_dir, "..")
    candidate = os.path.join(parent, "CFS_Data", "StreamingAssets")
    if os.path.isdir(candidate):
        return os.path.normpath(parent)

    # 都找不到，回退到当前目录的父级
    return os.path.normpath(parent)


GAME_DIR = _detect_game_dir()
STREAMING_ASSETS = os.path.join(GAME_DIR, "CFS_Data", "StreamingAssets")
BACKUP_DIR = os.path.join(GAME_DIR, "Trainer", "backups")

PLAYER_ATTRS = [
    ("Pace", "速度"), ("Shooting", "射门"), ("ShortPass", "短传"),
    ("LongPass", "长传"), ("Tackling", "抢断"), ("Header", "头球"),
    ("Strength", "力量"), ("Agility", "敏捷"), ("Dribble", "盘带"),
    ("Stamina", "体能"), ("Composure", "镇定"),
    ("KeeperAnticipation", "门将预判"), ("KeeperSaving", "门将扑救"),
    ("WeakerFoot", "弱脚能力"),
]

PLAYER_INFO_FIELDS = [
    ("Age", "年龄"), ("MarketValue", "身价"), ("Salary", "薪资"),
    ("Level", "等级"), ("ExpPoints", "经验值"), ("Height", "身高"),
    ("Weight", "体重"),
]

PLAYER_MENTAL_ATTRS = [
    ("Ambition", "野心"), ("Professional", "职业素养"),
    ("Dirtyness", "脏动作"), ("AngerControl", "怒气控制"),
    ("SpeechMaking", "演讲能力"), ("DomesticPopulation", "国内人气"),
    ("InternationalPopulation", "国际人气"),
]


# ─── 数据库工具 ─────────────────────────────────────────
class DBHelper:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def execute(self, sql, params=None):
        cur = self.conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return cur

    def commit(self):
        self.conn.commit()

    def fetchone(self, sql, params=None):
        cur = self.execute(sql, params)
        return cur.fetchone()

    def fetchall(self, sql, params=None):
        cur = self.execute(sql, params)
        return cur.fetchall()


# ─── 存档备份 ─────────────────────────────────────────────
def backup_db(db_path):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    name = os.path.basename(db_path)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"{name}.{ts}.bak")
    shutil.copy2(db_path, backup_path)
    return backup_path


def find_save_files():
    """扫描 StreamingAssets 目录下的所有 .db 存档文件"""
    saves = []
    if not os.path.isdir(STREAMING_ASSETS):
        return saves
    for f in os.listdir(STREAMING_ASSETS):
        if f.endswith(".db"):
            full = os.path.join(STREAMING_ASSETS, f)
            size_mb = os.path.getsize(full) / (1024 * 1024)
            saves.append((f, full, size_mb))
    saves.sort(key=lambda x: os.path.getmtime(x[1]), reverse=True)
    return saves


# ═══════════════════════════════════════════════════════════
#  主界面
# ═══════════════════════════════════════════════════════════
class TrainerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CFS 足球模拟器 修改器 v1.0")
        self.root.geometry("960x720")
        self.root.minsize(800, 600)
        self.db = None
        self.current_db_path = None

        self._apply_theme()
        self._build_ui()

    # ─── 主题 ────────────────────────────────────────────
    def _apply_theme(self):
        style = ttk.Style()
        style.theme_use("clam")
        BG = "#1e1e2e"
        FG = "#cdd6f4"
        ACCENT = "#89b4fa"
        BTN_BG = "#313244"
        BTN_ACTIVE = "#45475a"
        ENTRY_BG = "#313244"

        self.root.configure(bg=BG)
        self.colors = {"bg": BG, "fg": FG, "accent": ACCENT, "btn": BTN_BG,
                        "btn_active": BTN_ACTIVE, "entry": ENTRY_BG,
                        "success": "#a6e3a1", "warning": "#f9e2af", "error": "#f38ba8"}

        style.configure(".", background=BG, foreground=FG, borderwidth=0,
                         font=("Microsoft YaHei UI", 10))
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=BTN_BG, foreground=FG,
                         padding=[16, 6], font=("Microsoft YaHei UI", 10, "bold"))
        style.map("TNotebook.Tab",
                   background=[("selected", ACCENT)],
                   foreground=[("selected", "#1e1e2e")])
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("TLabelframe", background=BG, foreground=ACCENT)
        style.configure("TLabelframe.Label", background=BG, foreground=ACCENT,
                         font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("TButton", background=BTN_BG, foreground=FG,
                         padding=[12, 6], font=("Microsoft YaHei UI", 10))
        style.map("TButton", background=[("active", BTN_ACTIVE)])
        style.configure("Accent.TButton", background=ACCENT, foreground="#1e1e2e",
                         font=("Microsoft YaHei UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#74c7ec")])
        style.configure("Success.TButton", background="#a6e3a1", foreground="#1e1e2e",
                         font=("Microsoft YaHei UI", 10, "bold"))
        style.map("Success.TButton", background=[("active", "#94e2d5")])
        style.configure("Warning.TButton", background="#f9e2af", foreground="#1e1e2e",
                         font=("Microsoft YaHei UI", 10, "bold"))
        style.map("Warning.TButton", background=[("active", "#f5c2e7")])
        style.configure("TEntry", fieldbackground=ENTRY_BG, foreground=FG,
                         insertcolor=FG)
        style.configure("TCombobox", fieldbackground=ENTRY_BG, foreground=FG)
        style.configure("Treeview", background=ENTRY_BG, foreground=FG,
                         fieldbackground=ENTRY_BG, rowheight=26,
                         font=("Microsoft YaHei UI", 9))
        style.configure("Treeview.Heading", background=BTN_BG, foreground=ACCENT,
                         font=("Microsoft YaHei UI", 9, "bold"))
        style.map("Treeview", background=[("selected", ACCENT)],
                   foreground=[("selected", "#1e1e2e")])

    # ─── 构建界面 ────────────────────────────────────────
    def _build_ui(self):
        # 顶部：存档选择
        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(top, text="选择存档：",
                  font=("Microsoft YaHei UI", 11, "bold")).pack(side="left")
        self.save_combo = ttk.Combobox(top, state="readonly", width=50)
        self.save_combo.pack(side="left", padx=(5, 10))
        ttk.Button(top, text="加载", style="Accent.TButton",
                   command=self._load_save).pack(side="left", padx=2)
        ttk.Button(top, text="刷新", command=self._refresh_saves).pack(side="left", padx=2)
        ttk.Button(top, text="浏览...", command=self._browse_db).pack(side="left", padx=2)

        self.status_label = ttk.Label(top, text="未加载存档", foreground=self.colors["warning"])
        self.status_label.pack(side="right")

        # 标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        self._build_tab_quick()
        self._build_tab_players()
        self._build_tab_team()
        self._build_tab_unlock()
        self._build_tab_youth()

        # 底部状态栏
        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x", padx=10, pady=(0, 10))
        self.bottom_status = ttk.Label(bottom, text="提示：修改前请先关闭游戏，修改后重新启动游戏即可生效",
                                        foreground=self.colors["warning"],
                                        font=("Microsoft YaHei UI", 9))
        self.bottom_status.pack(side="left")

        self._refresh_saves()

    # ─── Tab 1: 快速修改 ────────────────────────────────
    def _build_tab_quick(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=" 快速修改 ")

        # 资金
        f1 = ttk.LabelFrame(tab, text="资金管理", padding=10)
        f1.pack(fill="x", padx=10, pady=5)

        row = ttk.Frame(f1)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="当前资金：").pack(side="left")
        self.cash_var = tk.StringVar(value="---")
        ttk.Label(row, textvariable=self.cash_var, foreground=self.colors["success"],
                  font=("Microsoft YaHei UI", 12, "bold")).pack(side="left", padx=5)

        row2 = ttk.Frame(f1)
        row2.pack(fill="x", pady=5)
        ttk.Label(row2, text="设置资金：").pack(side="left")
        self.cash_entry = ttk.Entry(row2, width=20)
        self.cash_entry.pack(side="left", padx=5)
        self.cash_entry.insert(0, "999999999")
        ttk.Button(row2, text="修改资金", style="Success.TButton",
                   command=self._set_cash).pack(side="left", padx=5)

        quick_btns = ttk.Frame(f1)
        quick_btns.pack(fill="x", pady=5)
        for amount, label in [(100000, "10万"), (1000000, "100万"),
                               (10000000, "1000万"), (100000000, "1亿"),
                               (999999999, "9.99亿")]:
            ttk.Button(quick_btns, text=label,
                       command=lambda a=amount: self._quick_cash(a)).pack(side="left", padx=3)

        # 经理属性
        f2 = ttk.LabelFrame(tab, text="经理/教练属性", padding=10)
        f2.pack(fill="x", padx=10, pady=5)

        self.manager_vars = {}
        mgr_fields = [
            ("PlayerBaseFame", "声望"), ("PlayerBaseLeadership", "领导力"),
            ("PlayerBaseCommunication", "沟通能力"), ("PlayerBaseOperations", "运营能力"),
            ("PlayerTacticalPointsAmount", "战术点数"), ("PlayerMianziAmount", "面子值"),
            ("PlayerTotalExperience", "总经验值"),
        ]
        grid = ttk.Frame(f2)
        grid.pack(fill="x")
        for i, (field, label) in enumerate(mgr_fields):
            r, c = divmod(i, 3)
            fr = ttk.Frame(grid)
            fr.grid(row=r, column=c, padx=8, pady=3, sticky="w")
            ttk.Label(fr, text=f"{label}：").pack(side="left")
            var = tk.StringVar(value="---")
            self.manager_vars[field] = var
            e = ttk.Entry(fr, textvariable=var, width=12)
            e.pack(side="left", padx=3)

        btn_row = ttk.Frame(f2)
        btn_row.pack(fill="x", pady=(8, 0))
        ttk.Button(btn_row, text="保存经理属性", style="Success.TButton",
                   command=self._save_manager).pack(side="left", padx=3)
        ttk.Button(btn_row, text="一键满属性", style="Warning.TButton",
                   command=self._max_manager).pack(side="left", padx=3)

        # 球队快速
        f3 = ttk.LabelFrame(tab, text="球队快速修改", padding=10)
        f3.pack(fill="x", padx=10, pady=5)

        self.team_quick_vars = {}
        tq_fields = [
            ("TeamWealth", "球队财富"), ("TeamFame", "球队声望"),
            ("SupporterCount", "球迷数量"), ("StadiumCapacity", "球场容量"),
        ]
        grid2 = ttk.Frame(f3)
        grid2.pack(fill="x")
        for i, (field, label) in enumerate(tq_fields):
            fr = ttk.Frame(grid2)
            fr.grid(row=0, column=i, padx=8, pady=3, sticky="w")
            ttk.Label(fr, text=f"{label}：").pack(side="left")
            var = tk.StringVar(value="---")
            self.team_quick_vars[field] = var
            ttk.Entry(fr, textvariable=var, width=12).pack(side="left", padx=3)

        btn_row2 = ttk.Frame(f3)
        btn_row2.pack(fill="x", pady=(8, 0))
        ttk.Button(btn_row2, text="保存球队属性", style="Success.TButton",
                   command=self._save_team_quick).pack(side="left", padx=3)

    # ─── Tab 2: 球员编辑 ────────────────────────────────
    def _build_tab_players(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=" 球员编辑 ")

        # 搜索栏
        search_frame = ttk.Frame(tab)
        search_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(search_frame, text="搜索球员：").pack(side="left")
        self.player_search_var = tk.StringVar()
        se = ttk.Entry(search_frame, textvariable=self.player_search_var, width=20)
        se.pack(side="left", padx=5)
        se.bind("<Return>", lambda e: self._search_players())
        ttk.Button(search_frame, text="搜索", command=self._search_players).pack(side="left", padx=3)
        ttk.Label(search_frame, text="筛选：").pack(side="left", padx=(15, 0))
        self.player_filter = ttk.Combobox(search_frame, values=["全部", "我的球队", "自由球员"], width=10, state="readonly")
        self.player_filter.set("我的球队")
        self.player_filter.pack(side="left", padx=5)
        ttk.Button(search_frame, text="筛选", command=self._search_players).pack(side="left", padx=3)

        # 球员列表
        list_frame = ttk.Frame(tab)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        left = ttk.Frame(list_frame)
        left.pack(side="left", fill="both", expand=True)

        cols = ("ID", "姓名", "年龄", "位置", "等级", "速度", "射门", "短传", "抢断", "力量")
        self.player_tree = ttk.Treeview(left, columns=cols, show="headings", height=12)
        for col in cols:
            w = 50 if col in ("ID", "年龄", "等级", "速度", "射门", "短传", "抢断", "力量") else 80
            self.player_tree.heading(col, text=col)
            self.player_tree.column(col, width=w, anchor="center")
        self.player_tree.column("姓名", width=120, anchor="w")
        self.player_tree.column("位置", width=70, anchor="center")

        scrollbar = ttk.Scrollbar(left, orient="vertical", command=self.player_tree.yview)
        self.player_tree.configure(yscrollcommand=scrollbar.set)
        self.player_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.player_tree.bind("<<TreeviewSelect>>", self._on_player_select)

        # 右侧编辑区
        right = ttk.Frame(list_frame, width=300)
        right.pack(side="right", fill="y", padx=(10, 0))
        right.pack_propagate(False)

        ttk.Label(right, text="球员属性编辑", font=("Microsoft YaHei UI", 11, "bold"),
                  foreground=self.colors["accent"]).pack(pady=(0, 5))

        self.player_name_var = tk.StringVar(value="未选择球员")
        ttk.Label(right, textvariable=self.player_name_var,
                  font=("Microsoft YaHei UI", 10)).pack()

        self.player_id_var = tk.IntVar(value=0)

        edit_canvas = tk.Canvas(right, bg=self.colors["bg"], highlightthickness=0)
        edit_scrollbar = ttk.Scrollbar(right, orient="vertical", command=edit_canvas.yview)
        edit_inner = ttk.Frame(edit_canvas)

        edit_inner.bind("<Configure>", lambda e: edit_canvas.configure(scrollregion=edit_canvas.bbox("all")))
        edit_canvas.create_window((0, 0), window=edit_inner, anchor="nw")
        edit_canvas.configure(yscrollcommand=edit_scrollbar.set)
        edit_canvas.pack(side="left", fill="both", expand=True)
        edit_scrollbar.pack(side="right", fill="y")
        # 鼠标滚轮
        edit_canvas.bind("<MouseWheel>", lambda e: edit_canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        self.player_attr_vars = {}

        ttk.Label(edit_inner, text="── 基本信息 ──", foreground=self.colors["accent"]).pack(pady=(5, 2))
        for field, label in PLAYER_INFO_FIELDS:
            fr = ttk.Frame(edit_inner)
            fr.pack(fill="x", padx=5, pady=1)
            ttk.Label(fr, text=f"{label}：", width=10, anchor="e").pack(side="left")
            var = tk.StringVar()
            self.player_attr_vars[field] = var
            ttk.Entry(fr, textvariable=var, width=10).pack(side="left", padx=3)

        ttk.Label(edit_inner, text="── 技术属性 ──", foreground=self.colors["accent"]).pack(pady=(8, 2))
        for field, label in PLAYER_ATTRS:
            fr = ttk.Frame(edit_inner)
            fr.pack(fill="x", padx=5, pady=1)
            ttk.Label(fr, text=f"{label}：", width=10, anchor="e").pack(side="left")
            var = tk.StringVar()
            self.player_attr_vars[field] = var
            ttk.Entry(fr, textvariable=var, width=10).pack(side="left", padx=3)

        ttk.Label(edit_inner, text="── 精神属性 ──", foreground=self.colors["accent"]).pack(pady=(8, 2))
        for field, label in PLAYER_MENTAL_ATTRS:
            fr = ttk.Frame(edit_inner)
            fr.pack(fill="x", padx=5, pady=1)
            ttk.Label(fr, text=f"{label}：", width=10, anchor="e").pack(side="left")
            var = tk.StringVar()
            self.player_attr_vars[field] = var
            ttk.Entry(fr, textvariable=var, width=10).pack(side="left", padx=3)

        btn_frame = ttk.Frame(right)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="保存此球员", style="Success.TButton",
                   command=self._save_player).pack(fill="x", padx=5, pady=2)
        ttk.Button(btn_frame, text="一键满属性", style="Warning.TButton",
                   command=self._max_player).pack(fill="x", padx=5, pady=2)
        ttk.Button(btn_frame, text="全队满属性", style="Warning.TButton",
                   command=self._max_all_team_players).pack(fill="x", padx=5, pady=2)

    # ─── Tab 3: 球队编辑 ────────────────────────────────
    def _build_tab_team(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=" 球队/球场 ")

        # 球场信息
        f1 = ttk.LabelFrame(tab, text="球场信息", padding=10)
        f1.pack(fill="x", padx=10, pady=5)

        self.stadium_vars = {}
        stadium_fields = [
            ("TicketPrice", "票价"), ("Seats", "座位数"),
            ("ParkingSpots", "停车位"), ("LoungeCount", "贵宾室数"),
            ("ShopsCount", "商店数"), ("PitchQuality", "球场质量"),
            ("StadiumLevel", "球场等级"), ("SecurityCost", "安保费用"),
        ]
        grid = ttk.Frame(f1)
        grid.pack(fill="x")
        for i, (field, label) in enumerate(stadium_fields):
            r, c = divmod(i, 4)
            fr = ttk.Frame(grid)
            fr.grid(row=r, column=c, padx=8, pady=3, sticky="w")
            ttk.Label(fr, text=f"{label}：").pack(side="left")
            var = tk.StringVar(value="---")
            self.stadium_vars[field] = var
            ttk.Entry(fr, textvariable=var, width=10).pack(side="left", padx=3)

        ttk.Button(f1, text="保存球场信息", style="Success.TButton",
                   command=self._save_stadium).pack(pady=(8, 0))

        # 赞助管理
        f2 = ttk.LabelFrame(tab, text="赞助商", padding=10)
        f2.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("名称", "类型", "年数", "金额", "已解锁")
        self.sponsor_tree = ttk.Treeview(f2, columns=cols, show="headings", height=8)
        for col in cols:
            self.sponsor_tree.heading(col, text=col)
            self.sponsor_tree.column(col, width=100, anchor="center")
        self.sponsor_tree.column("名称", width=150, anchor="w")
        self.sponsor_tree.pack(fill="both", expand=True)

        btn_row = ttk.Frame(f2)
        btn_row.pack(fill="x", pady=(5, 0))
        ttk.Button(btn_row, text="解锁全部赞助商", style="Warning.TButton",
                   command=self._unlock_all_sponsors).pack(side="left", padx=3)
        ttk.Button(btn_row, text="赞助金额全部翻10倍", style="Warning.TButton",
                   command=self._boost_sponsors).pack(side="left", padx=3)

    # ─── Tab 4: 一键解锁 ────────────────────────────────
    def _build_tab_unlock(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=" 一键解锁 ")

        ttk.Label(tab, text="一键解锁各种游戏内容",
                  font=("Microsoft YaHei UI", 14, "bold"),
                  foreground=self.colors["accent"]).pack(pady=15)

        items = [
            ("解锁全部设施", "Facilities 表 → Unlocked=1", self._unlock_facilities),
            ("解锁全部战术", "TacticsKnowledge 表 → IsUnlocked=1", self._unlock_tactics),
            ("解锁全部训练方案", "TrainingBuilds 表 → IsUnlocked=1", self._unlock_training),
            ("解锁全部比赛日方案", "GameDayOperationPlans 表 → IsUnlocked=1", self._unlock_gameday),
            ("解锁全部物品", "Items 表 → IsUnlocked=1, 库存+99", self._unlock_items),
            ("解锁全部合作伙伴", "Partners 表 → IsUnlocked=1", self._unlock_partners),
            ("解锁全部留洋目的地", "AbroadDestinations 表 → Unlocked=1", self._unlock_abroad),
            ("解锁全部巡回赛", "TourDestinations 表 → Unlocked=1", self._unlock_tours),
            ("解锁全部地块", "LandInfo 表 → IsUnlocked=1", self._unlock_lands),
            ("解锁全部建筑", "LandBuildingInfo 表 → IsUnlocked=1", self._unlock_buildings),
            ("解锁全部青训设施", "YouthFacilities 表 → IsUnlocked=1", self._unlock_youth_facilities),
            ("完成全部任务", "Missions 表 → MissionComplete=1", self._complete_missions),
            ("═══ 以上全部一键解锁 ═══", "", self._unlock_everything),
        ]

        for text, desc, cmd in items:
            fr = ttk.Frame(tab)
            fr.pack(fill="x", padx=20, pady=2)
            is_all = "全部一键" in text
            style = "Accent.TButton" if is_all else "TButton"
            btn = ttk.Button(fr, text=text, style=style, command=cmd, width=30)
            btn.pack(side="left", padx=5)
            if desc:
                ttk.Label(fr, text=desc, foreground=self.colors["warning"],
                          font=("Microsoft YaHei UI", 9)).pack(side="left", padx=10)

    # ─── Tab 5: 青训 ────────────────────────────────────
    def _build_tab_youth(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=" 青训球员 ")

        search_frame = ttk.Frame(tab)
        search_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(search_frame, text="加载青训球员", style="Accent.TButton",
                   command=self._load_youth).pack(side="left", padx=3)
        ttk.Button(search_frame, text="全部青训球员满潜力", style="Warning.TButton",
                   command=self._max_youth).pack(side="left", padx=3)

        cols = ("ID", "姓名", "年龄", "位置", "能力", "潜力", "成长", "纪律")
        self.youth_tree = ttk.Treeview(tab, columns=cols, show="headings", height=15)
        for col in cols:
            w = 50 if col != "姓名" else 120
            self.youth_tree.heading(col, text=col)
            self.youth_tree.column(col, width=w, anchor="center")
        self.youth_tree.column("姓名", anchor="w")
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=self.youth_tree.yview)
        self.youth_tree.configure(yscrollcommand=scrollbar.set)
        self.youth_tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=5)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=5)

        self.youth_tree.bind("<Double-1>", self._edit_youth_player)

    # ═══════════════════════════════════════════════════════
    #  数据加载
    # ═══════════════════════════════════════════════════════
    def _refresh_saves(self):
        saves = find_save_files()
        display = [f"{s[0]}  ({s[2]:.1f} MB)" for s in saves]
        self.save_combo["values"] = display
        self._save_paths = {d: s[1] for d, s in zip(display, saves)}
        if display:
            self.save_combo.current(0)

    def _browse_db(self):
        path = filedialog.askopenfilename(
            title="选择存档文件",
            initialdir=STREAMING_ASSETS,
            filetypes=[("SQLite 数据库", "*.db"), ("所有文件", "*.*")]
        )
        if path:
            self._open_db(path)

    def _load_save(self):
        sel = self.save_combo.get()
        if not sel or sel not in self._save_paths:
            messagebox.showwarning("提示", "请先选择一个存档文件")
            return
        self._open_db(self._save_paths[sel])

    def _open_db(self, path):
        if self.db:
            self.db.close()
        try:
            # 备份
            bak = backup_db(path)
            self.current_db_path = path
            self.db = DBHelper(path)
            self.db.connect()
            self.status_label.config(text=f"已加载: {os.path.basename(path)}",
                                      foreground=self.colors["success"])
            self.bottom_status.config(text=f"已备份至: {os.path.basename(bak)}")
            self._load_all_data()
        except Exception as e:
            messagebox.showerror("错误", f"无法打开数据库：\n{e}")

    def _load_all_data(self):
        self._load_quick_data()
        self._load_stadium_data()
        self._load_sponsors()
        self._search_players()
        self._load_youth()

    def _require_db(self):
        if not self.db or not self.db.conn:
            messagebox.showwarning("提示", "请先加载存档文件")
            return False
        return True

    # ─── 快速修改数据加载 ────────────────────────────────
    def _load_quick_data(self):
        row = self.db.fetchone("SELECT CashRemaining FROM TeamOtherInfo")
        if row:
            self.cash_var.set(f"{row['CashRemaining']:,}")

        misc = self.db.fetchone(
            "SELECT PlayerBaseFame,PlayerBaseLeadership,PlayerBaseCommunication,"
            "PlayerBaseOperations,PlayerTacticalPointsAmount,PlayerMianziAmount,"
            "PlayerTotalExperience,UserTeamID FROM Misc"
        )
        if misc:
            for field, var in self.manager_vars.items():
                var.set(str(misc[field]) if misc[field] is not None else "0")

            team = self.db.fetchone(
                "SELECT TeamWealth,TeamFame,SupporterCount,StadiumCapacity FROM Teams WHERE ID=?",
                (misc["UserTeamID"],)
            )
            if team:
                for field, var in self.team_quick_vars.items():
                    var.set(str(team[field]) if team[field] is not None else "0")

    def _load_stadium_data(self):
        misc = self.db.fetchone("SELECT UserTeamID FROM Misc")
        if not misc:
            return
        row = self.db.fetchone("SELECT * FROM StadiumInfo WHERE OccupyingClubID=?",
                                (misc["UserTeamID"],))
        if not row:
            row = self.db.fetchone("SELECT * FROM StadiumInfo LIMIT 1")
        if row:
            for field, var in self.stadium_vars.items():
                var.set(str(row[field]) if row[field] is not None else "0")

    def _load_sponsors(self):
        for item in self.sponsor_tree.get_children():
            self.sponsor_tree.delete(item)
        rows = self.db.fetchall("SELECT SponsorName,Type,SignedYears,PaidAmount,Unlocked FROM Sponsor")
        for r in rows:
            self.sponsor_tree.insert("", "end", values=(
                r["SponsorName"] or "", r["Type"] or "",
                r["SignedYears"] or 0, r["PaidAmount"] or 0,
                "是" if r["Unlocked"] else "否"
            ))

    # ═══════════════════════════════════════════════════════
    #  修改操作
    # ═══════════════════════════════════════════════════════

    # ─── 资金 ────────────────────────────────────────────
    def _set_cash(self):
        if not self._require_db():
            return
        try:
            val = int(self.cash_entry.get().replace(",", "").strip())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
            return
        self.db.execute("UPDATE TeamOtherInfo SET CashRemaining=?", (val,))
        self.db.commit()
        self.cash_var.set(f"{val:,}")
        self._show_success("资金已修改")

    def _quick_cash(self, amount):
        self.cash_entry.delete(0, "end")
        self.cash_entry.insert(0, str(amount))
        self._set_cash()

    # ─── 经理 ────────────────────────────────────────────
    def _save_manager(self):
        if not self._require_db():
            return
        sets = []
        vals = []
        for field, var in self.manager_vars.items():
            try:
                v = int(var.get().replace(",", "").strip())
            except ValueError:
                v = 0
            sets.append(f"{field}=?")
            vals.append(v)
        self.db.execute(f"UPDATE Misc SET {','.join(sets)}", vals)
        self.db.commit()
        self._show_success("经理属性已保存")

    def _max_manager(self):
        if not self._require_db():
            return
        maxvals = {
            "PlayerBaseFame": 99, "PlayerBaseLeadership": 99,
            "PlayerBaseCommunication": 99, "PlayerBaseOperations": 99,
            "PlayerTacticalPointsAmount": 9999, "PlayerMianziAmount": 99999,
            "PlayerTotalExperience": 99999999,
        }
        for field, val in maxvals.items():
            self.manager_vars[field].set(str(val))
        self._save_manager()

    # ─── 球队快速 ────────────────────────────────────────
    def _save_team_quick(self):
        if not self._require_db():
            return
        misc = self.db.fetchone("SELECT UserTeamID FROM Misc")
        if not misc:
            return
        sets = []
        vals = []
        for field, var in self.team_quick_vars.items():
            try:
                v = int(var.get().replace(",", "").strip())
            except ValueError:
                v = 0
            sets.append(f"{field}=?")
            vals.append(v)
        vals.append(misc["UserTeamID"])
        self.db.execute(f"UPDATE Teams SET {','.join(sets)} WHERE ID=?", vals)
        self.db.commit()
        self._show_success("球队属性已保存")

    # ─── 球员搜索 ────────────────────────────────────────
    def _search_players(self):
        if not self._require_db():
            return
        for item in self.player_tree.get_children():
            self.player_tree.delete(item)

        keyword = self.player_search_var.get().strip()
        filter_type = self.player_filter.get()

        sql = ("SELECT ID,PlayerName,Age,Position,Level,Pace,Shooting,ShortPass,"
               "Tackling,Strength FROM Players WHERE 1=1")
        params = []

        if keyword:
            sql += " AND PlayerName LIKE ?"
            params.append(f"%{keyword}%")

        if filter_type == "我的球队":
            misc = self.db.fetchone("SELECT UserTeamID FROM Misc")
            if misc:
                sql += " AND CurrentTeam=?"
                params.append(misc["UserTeamID"])
        elif filter_type == "自由球员":
            sql += " AND (CurrentTeam IS NULL OR CurrentTeam=-1)"

        sql += " ORDER BY Level DESC LIMIT 500"

        rows = self.db.fetchall(sql, params if params else None)
        for r in rows:
            self.player_tree.insert("", "end", values=(
                r["ID"], r["PlayerName"] or "", r["Age"] or 0,
                r["Position"] or "", r["Level"] or 0,
                r["Pace"] or 0, r["Shooting"] or 0, r["ShortPass"] or 0,
                r["Tackling"] or 0, r["Strength"] or 0
            ), iid=str(r["ID"]))

    def _on_player_select(self, event):
        sel = self.player_tree.selection()
        if not sel:
            return
        pid = int(sel[0])
        self.player_id_var.set(pid)

        all_fields = [f for f, _ in PLAYER_INFO_FIELDS + PLAYER_ATTRS + PLAYER_MENTAL_ATTRS]
        sql = f"SELECT PlayerName,{','.join(all_fields)} FROM Players WHERE ID=?"
        row = self.db.fetchone(sql, (pid,))
        if not row:
            return

        self.player_name_var.set(f"{row['PlayerName']}  (ID: {pid})")
        for field in all_fields:
            if field in self.player_attr_vars:
                val = row[field]
                self.player_attr_vars[field].set(str(val) if val is not None else "0")

    def _save_player(self):
        if not self._require_db():
            return
        pid = self.player_id_var.get()
        if pid == 0:
            messagebox.showwarning("提示", "请先选择一个球员")
            return
        all_fields = [f for f, _ in PLAYER_INFO_FIELDS + PLAYER_ATTRS + PLAYER_MENTAL_ATTRS]
        sets = []
        vals = []
        for field in all_fields:
            var = self.player_attr_vars.get(field)
            if var:
                try:
                    v = float(var.get().replace(",", "").strip())
                    if v == int(v):
                        v = int(v)
                except ValueError:
                    v = 0
                sets.append(f"{field}=?")
                vals.append(v)
        vals.append(pid)
        self.db.execute(f"UPDATE Players SET {','.join(sets)} WHERE ID=?", vals)
        self.db.commit()
        self._search_players()
        self._show_success(f"球员 (ID:{pid}) 已保存")

    def _max_player(self):
        if not self._require_db():
            return
        pid = self.player_id_var.get()
        if pid == 0:
            messagebox.showwarning("提示", "请先选择一个球员")
            return
        for field, _ in PLAYER_ATTRS:
            self.player_attr_vars[field].set("150")
        self.player_attr_vars["WeakerFoot"].set("5")
        self.player_attr_vars["Level"].set("99")
        self.player_attr_vars["ExpPoints"].set("99999")
        self._save_player()

    def _max_all_team_players(self):
        if not self._require_db():
            return
        misc = self.db.fetchone("SELECT UserTeamID FROM Misc")
        if not misc:
            return
        if not messagebox.askyesno("确认", "确定要将全队所有球员属性拉满吗？"):
            return

        attr_fields = [f for f, _ in PLAYER_ATTRS]
        sets = [f"{f}=150" for f in attr_fields]
        sets.append("WeakerFoot=5")
        sets.append("Level=99")
        sets.append("ExpPoints=99999")
        self.db.execute(
            f"UPDATE Players SET {','.join(sets)} WHERE CurrentTeam=?",
            (misc["UserTeamID"],)
        )
        self.db.commit()
        self._search_players()
        self._show_success("全队球员已拉满")

    # ─── 球场 ────────────────────────────────────────────
    def _save_stadium(self):
        if not self._require_db():
            return
        misc = self.db.fetchone("SELECT UserTeamID FROM Misc")
        if not misc:
            return
        sets = []
        vals = []
        for field, var in self.stadium_vars.items():
            try:
                v = int(var.get().replace(",", "").strip())
            except ValueError:
                v = 0
            sets.append(f"{field}=?")
            vals.append(v)
        vals.append(misc["UserTeamID"])
        self.db.execute(
            f"UPDATE StadiumInfo SET {','.join(sets)} WHERE OccupyingClubID=?", vals
        )
        self.db.commit()
        self._show_success("球场信息已保存")

    # ─── 赞助 ────────────────────────────────────────────
    def _unlock_all_sponsors(self):
        if not self._require_db():
            return
        self.db.execute("UPDATE Sponsor SET Unlocked=1")
        self.db.commit()
        self._load_sponsors()
        self._show_success("全部赞助商已解锁")

    def _boost_sponsors(self):
        if not self._require_db():
            return
        self.db.execute(
            "UPDATE Sponsor SET PaidAmount=PaidAmount*10,"
            "BrandOffer=BrandOffer*10,ChestOffer=ChestOffer*10,"
            "BackOffer=BackOffer*10,SleeveOffer=SleeveOffer*10,"
            "BillboardOffer=BillboardOffer*10,BibOffer=BibOffer*10,"
            "BannerOffer=BannerOffer*10"
        )
        self.db.commit()
        self._load_sponsors()
        self._show_success("赞助金额已翻10倍")

    # ─── 一键解锁 ────────────────────────────────────────
    def _unlock_facilities(self):
        if not self._require_db(): return
        self.db.execute("UPDATE Facilities SET Unlocked=1")
        self.db.commit()
        self._show_success("全部设施已解锁")

    def _unlock_tactics(self):
        if not self._require_db(): return
        self.db.execute("UPDATE TacticsKnowledge SET IsUnlocked=1")
        self.db.commit()
        self._show_success("全部战术已解锁")

    def _unlock_training(self):
        if not self._require_db(): return
        self.db.execute("UPDATE TrainingBuilds SET IsUnlocked=1")
        self.db.commit()
        self._show_success("全部训练方案已解锁")

    def _unlock_gameday(self):
        if not self._require_db(): return
        self.db.execute("UPDATE GameDayOperationPlans SET IsUnlocked=1")
        self.db.commit()
        self._show_success("全部比赛日方案已解锁")

    def _unlock_items(self):
        if not self._require_db(): return
        self.db.execute("UPDATE Items SET IsUnlocked=1, PlayerOwningAmount=PlayerOwningAmount+99")
        self.db.commit()
        self._show_success("全部物品已解锁，库存+99")

    def _unlock_partners(self):
        if not self._require_db(): return
        self.db.execute("UPDATE Partners SET IsUnlocked=1")
        self.db.commit()
        self._show_success("全部合作伙伴已解锁")

    def _unlock_abroad(self):
        if not self._require_db(): return
        self.db.execute("UPDATE AbroadDestinations SET Unlocked=1")
        self.db.commit()
        self._show_success("全部留洋目的地已解锁")

    def _unlock_tours(self):
        if not self._require_db(): return
        self.db.execute("UPDATE TourDestinations SET Unlocked=1")
        self.db.commit()
        self._show_success("全部巡回赛已解锁")

    def _unlock_lands(self):
        if not self._require_db(): return
        self.db.execute("UPDATE LandInfo SET IsUnlocked=1")
        self.db.commit()
        self._show_success("全部地块已解锁")

    def _unlock_buildings(self):
        if not self._require_db(): return
        self.db.execute("UPDATE LandBuildingInfo SET IsUnlocked=1")
        self.db.commit()
        self._show_success("全部建筑已解锁")

    def _unlock_youth_facilities(self):
        if not self._require_db(): return
        self.db.execute("UPDATE YouthFacilities SET IsUnlocked=1")
        self.db.commit()
        self._show_success("全部青训设施已解锁")

    def _complete_missions(self):
        if not self._require_db(): return
        self.db.execute("UPDATE Missions SET MissionComplete=1")
        self.db.commit()
        self._show_success("全部任务已完成")

    def _unlock_everything(self):
        if not self._require_db(): return
        if not messagebox.askyesno("确认", "确定要一键解锁所有内容吗？"):
            return
        self._unlock_facilities()
        self._unlock_tactics()
        self._unlock_training()
        self._unlock_gameday()
        self._unlock_items()
        self._unlock_partners()
        self._unlock_abroad()
        self._unlock_tours()
        self._unlock_lands()
        self._unlock_buildings()
        self._unlock_youth_facilities()
        self._complete_missions()
        self._show_success("全部内容已解锁！")

    # ─── 青训 ────────────────────────────────────────────
    def _load_youth(self):
        if not self._require_db():
            return
        for item in self.youth_tree.get_children():
            self.youth_tree.delete(item)
        rows = self.db.fetchall(
            "SELECT ID,PlayerName,Age,Position,AbilityLevel,PotentialLevel,"
            "GrowthLevel,DisciplineLevel FROM YouthPlayers ORDER BY PotentialLevel DESC"
        )
        for r in rows:
            self.youth_tree.insert("", "end", values=(
                r["ID"], r["PlayerName"] or "", r["Age"] or 0,
                r["Position"] or "", r["AbilityLevel"] or 0,
                r["PotentialLevel"] or 0, r["GrowthLevel"] or 0,
                r["DisciplineLevel"] or 0
            ), iid=str(r["ID"]))

    def _max_youth(self):
        if not self._require_db(): return
        if not messagebox.askyesno("确认", "将全部青训球员的潜力和成长拉满？"):
            return
        self.db.execute(
            "UPDATE YouthPlayers SET PotentialLevel=10,GrowthLevel=10,"
            "AbilityLevel=CASE WHEN AbilityLevel<8 THEN 8 ELSE AbilityLevel END,"
            "DisciplineLevel=10"
        )
        self.db.commit()
        self._load_youth()
        self._show_success("全部青训球员已拉满")

    def _edit_youth_player(self, event):
        sel = self.youth_tree.selection()
        if not sel:
            return
        yid = int(sel[0])
        row = self.db.fetchone("SELECT * FROM YouthPlayers WHERE ID=?", (yid,))
        if not row:
            return

        win = tk.Toplevel(self.root)
        win.title(f"编辑青训球员 - {row['PlayerName']}")
        win.geometry("350x350")
        win.configure(bg=self.colors["bg"])
        win.transient(self.root)
        win.grab_set()

        fields = [
            ("AbilityLevel", "能力等级"), ("PotentialLevel", "潜力等级"),
            ("GrowthLevel", "成长速度"), ("DisciplineLevel", "纪律等级"),
            ("FinancialLevel", "经济等级"), ("Age", "年龄"),
            ("Height", "身高"), ("Weight", "体重"),
            ("InvestedMoney", "已投入资金"),
        ]
        vars_map = {}
        for i, (field, label) in enumerate(fields):
            fr = ttk.Frame(win)
            fr.pack(fill="x", padx=15, pady=3)
            ttk.Label(fr, text=f"{label}：", width=12, anchor="e").pack(side="left")
            var = tk.StringVar(value=str(row[field]) if row[field] is not None else "0")
            vars_map[field] = var
            ttk.Entry(fr, textvariable=var, width=12).pack(side="left", padx=5)

        def save():
            sets = []
            vals = []
            for field, var in vars_map.items():
                try:
                    v = int(var.get().strip())
                except ValueError:
                    v = 0
                sets.append(f"{field}=?")
                vals.append(v)
            vals.append(yid)
            self.db.execute(f"UPDATE YouthPlayers SET {','.join(sets)} WHERE ID=?", vals)
            self.db.commit()
            self._load_youth()
            win.destroy()
            self._show_success(f"青训球员 {row['PlayerName']} 已保存")

        ttk.Button(win, text="保存", style="Success.TButton", command=save).pack(pady=15)

    # ─── 工具 ────────────────────────────────────────────
    def _show_success(self, msg):
        self.bottom_status.config(text=f"✓ {msg}", foreground=self.colors["success"])
        self.root.after(5000, lambda: self.bottom_status.config(
            text="提示：修改前请先关闭游戏，修改后重新启动游戏即可生效",
            foreground=self.colors["warning"]
        ))


# ═══════════════════════════════════════════════════════════
#  启动
# ═══════════════════════════════════════════════════════════
def main():
    root = tk.Tk()
    root.iconname("CFS Trainer")
    app = TrainerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
