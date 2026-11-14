# -*- coding: utf-8 -*-
"""Fastener Generator -> STEP (real threads). tkinter GUI."""
import os, sys, threading, time, traceback, subprocess, re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

HERE = os.path.dirname(os.path.abspath(__file__))


def _data_dir():
    """Where settings/output go: next to the program, or ~/Documents/Boltsmith when
    running from a macOS .app bundle or a read-only location."""
    if ".app/Contents" not in HERE and os.access(HERE, os.W_OK):
        return HERE
    docs = os.path.join(os.path.expanduser("~"), "Documents")
    base = os.path.join(docs if os.path.isdir(docs) else os.path.expanduser("~"), "Boltsmith")
    os.makedirs(base, exist_ok=True)
    return base


DATA = _data_dir()
OUT_DEFAULT = os.path.join(DATA, "output")


def open_path(path):
    """Open a file or folder with the system default application (Win/macOS/Linux)."""
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


SETTINGS = os.path.join(DATA, "settings.json")


def _load_settings():
    try:
        import json
        with open(SETTINGS, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_settings(**kw):
    try:
        import json
        d = _load_settings(); d.update(kw)
        with open(SETTINGS, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


LANG = (os.environ.get("FASTENER_LANG") or _load_settings().get("lang") or "ua").lower()
UA = {'Boltsmith — fastener generator → STEP (real threads)': 'Boltsmith — генератор кріплення → STEP (справжня різьба)', 'fastener generator → STEP': 'генератор кріплення → STEP', 'Bolt / Screw': 'Болт / гвинт', 'Nut': 'Гайка', 'Washer': 'Шайба', 'Threaded rod': 'Шпилька', 'Kit': 'Комплект', 'Standard (ISO / DIN)': 'Стандарт (ISO / DIN)', 'Custom (M1–M100, any head & drive)': 'Власний (M1–M100, будь-яка головка й шліц)', 'Standard': 'Стандартний', 'Custom': 'Власний', 'Type': 'Тип', 'Size': 'Розмір', 'Length, mm': 'Довжина, мм', 'Length is measured under the head; overall for countersunk heads.': 'Довжина — під головкою; для потайних — загальна.', 'Head': 'Головка', 'Drive': 'Шліц / під ключ', 'Thread length, mm (0 = full)': 'Довжина різьби, мм (0 = повна)', 'Head diameter, mm (empty = auto)': 'Діаметр головки, мм (пусто = авто)', 'Head height, mm (empty = auto)': 'Висота головки, мм (пусто = авто)', 'Custom (M1–M100, nyloc, sleeve nut...)': 'Власна (M1–M100, самоконтрівна, меблева...)', 'Length, mm (sleeve / coupling; empty = auto)': 'Довжина, мм (меблева / подовж.; пусто = авто)', 'Drive (sleeve nut)': 'Шліц (для меблевої)', 'Custom (any size, spring lock)': 'Власна (будь-який розмір, гровер)', 'For bolt M, mm': 'Під болт M, мм', 'Threaded rod (DIN 975)': 'Шпилька / різьбовий пруток (DIN 975)', 'The bolt is taken from the «Bolt / Screw» tab (standard or custom).\nAn ISO 4032 nut and ISO 7089 washers of the same size are added automatically\n(non-standard sizes use formula-based parts).': 'Болт береться з вкладки «Болт / гвинт» (стандартний або власний).\nГайка ISO 4032 і шайби ISO 7089 того ж розміру додаються автоматично\n(для нестандартних розмірів — власні за формулами).', 'Assembly': 'Збірка', 'Grip (clamped stack thickness), mm': "Товщина з'єднання (пакет деталей), мм", 'Washer under head': 'Шайба під головку', 'Washer under nut': 'Шайба під гайку', 'Each part is a separate body in the STEP (bolt, nut, washer).': 'Кожна деталь у STEP — окреме тіло (bolt, nut, washer).', 'General': 'Загальне', 'Thread:': 'Різьба:', 'right-hand': 'права', 'left-hand (LH)': 'ліва (LH)', 'Single solid body (merge thread with part)': 'Одне суцільне тіло (злити різьбу з деталлю)', 'Also save STL (for printing)': 'Також зберегти STL (для друку)', 'Folder:': 'Папка:', 'Generate STEP': 'Згенерувати STEP', 'Open folder': 'Відкрити папку', 'Open file': 'Відкрити файл', 'Loading CAD kernel…': 'Завантаження CAD-ядра…', 'Diameter M, mm': 'Діаметр M, мм', 'Thread pitch, mm': 'Крок різьби, мм', 'Failed to load the CAD kernel:\n': 'Помилка завантаження ядра:\n', 'Ready. Choose parameters and press «Generate STEP».': 'Готово. Виберіть параметри й натисніть «Згенерувати STEP».', 'Error': 'Помилка', 'Generating… (real threads: a few seconds up to ~a minute)': 'Генерую… (справжня різьба: від кількох секунд до ~хвилини)', 'Assembly: {n} parts (each a separate body)': 'Збірка: {n} дет. (кожна — окреме тіло)', '1 solid body': '1 суцільне тіло', '2 bodies: steel nut + nylon insert': '2 тіла: сталева гайка + нейлонове кільце', '{n} bodies: part + thread separate (kernel could not merge — use Combine in your CAD)': '{n} тіла: деталь + різьба окремо (ядро не змогло злити — у CAD зробіть Combine)', 'Done in {t} s: {path}\n{note}': 'Готово за {t} с: {path}\n{note}', 'Error: ': 'Помилка: ', 'Socket head cap, hex socket — ISO 4762': 'Циліндрична, внутр. шестигранник — ISO 4762', 'Cheese head, Torx — ISO 14580': 'Циліндрична, Torx — ISO 14580', 'Cheese head, slotted — ISO 1207': 'Циліндрична, шліц — ISO 1207', 'Cheese head, Phillips — ISO 7048': 'Циліндрична, хрест Phillips — ISO 7048', 'Button head, hex socket — ISO 7380-1': 'Напівкругла, шестигранник — ISO 7380-1', 'Button head with collar — ISO 7380-2': 'Напівкругла з буртиком — ISO 7380-2', 'Countersunk 90°, hex socket — ISO 10642': 'Потайна 90°, шестигранник — ISO 10642', 'Countersunk, Torx — ISO 14581': 'Потайна, Torx — ISO 14581', 'Countersunk, Torx, high head — ISO 14582': 'Потайна, Torx, висока — ISO 14582', 'Countersunk, slotted — ISO 2009': 'Потайна, шліц — ISO 2009', 'Countersunk, Phillips — ISO 7046': 'Потайна, хрест Phillips — ISO 7046', 'Raised countersunk, slotted — ISO 2010': 'Напівпотайна, шліц — ISO 2010', 'Raised countersunk, Phillips — ISO 7047': 'Напівпотайна, Phillips — ISO 7047', 'Raised countersunk, Torx — ISO 14584': 'Напівпотайна, Torx — ISO 14584', 'Hex head, fully threaded — ISO 4017': 'Шестигранна головка, повна різьба — ISO 4017', 'Hex head, partially threaded — ISO 4014': 'Шестигранна головка, частк. різьба — ISO 4014', 'Hex head bolt — DIN 931': 'Шестигранна головка — DIN 931', 'Hex flange bolt — DIN 1665': 'Шестигранна з фланцем — DIN 1665', 'Hex flange bolt — DIN 1662': 'Шестигранна з фланцем — DIN 1662', 'Pan head, slotted — ISO 1580': 'Пан-головка, шліц — ISO 1580', 'Pan head, Torx — ISO 14583': 'Пан-головка, Torx — ISO 14583', 'Pan head, Phillips — ISO 7045': 'Пан-головка, хрест Phillips — ISO 7045', 'Pan head with collar — DIN 967': 'Пан-головка з буртиком — DIN 967', 'Set screw (headless) — ISO 4026': 'Установочний гвинт (без головки) — ISO 4026', 'Shoulder screw — ISO 7379': 'Плечовий (з точним пояском) — ISO 7379', 'Low profile — OpenBuilds': 'Низький профіль — OpenBuilds', 'Hex nut — ISO 4032': 'Шестигранна — ISO 4032', 'Hex nut, style 2 (taller) — ISO 4033': 'Шестигранна, тип 2 (вища) — ISO 4033', 'Thin / jam nut — ISO 4035': 'Низька / контргайка — ISO 4035', 'Hex nut, unchamfered — ISO 4036': 'Шестигранна без фасок — ISO 4036', 'Flange nut (built-in washer) — DIN 1665': 'З фланцем (вбудована шайба) — DIN 1665', 'Domed cap nut (acorn) — DIN 1587': 'Ковпачкова (глуха) — DIN 1587', 'Square nut — DIN 557': 'Квадратна — DIN 557', 'Heat-set insert (3D print) — McMaster-Carr': 'Термовставка (3D-друк) — McMaster-Carr', 'Heat-set insert (3D print) — CNC Kitchen': 'Термовставка (3D-друк) — CNC Kitchen', 'Heat-set insert (3D print) — ruthex': 'Термовставка (3D-друк) — ruthex', 'Heat-set insert (3D print) — Hilitchi': 'Термовставка (3D-друк) — Hilitchi', 'Flat washer — ISO 7089': 'Плоска — ISO 7089', 'Flat washer, normal grade — ISO 7091': 'Плоска, без фаски — ISO 7091', 'Large flat washer — ISO 7093': 'Збільшена — ISO 7093', 'Extra large flat washer — ISO 7094': 'Дуже велика — ISO 7094', 'Chamfered washer — ISO 7090': 'З фаскою — ISO 7090', 'Small washer (cheese head) — ISO 7092': 'Мала (під циліндричну головку) — ISO 7092', 'Internal tooth lock washer — DIN 6797': 'Зубчаста стопорна, внутр. зуб — DIN 6797', 'Socket cap (cylindrical)': 'Циліндрична', 'Button (dome)': 'Напівкругла (купол)', 'Countersunk 90°': 'Потайна 90°', 'Raised countersunk 90°': 'Напівпотайна 90°', 'Pan head': 'Пан-головка', 'Hex head': 'Шестигранна', 'Hex head with flange': 'Шестигранна з фланцем', 'Headless (set screw)': 'Без головки (установочний)', 'Hex socket (Allen)': 'Шестигранник (Allen)', 'Torx': 'Torx (зірочка)', 'Triangle': 'Трикутник', 'Square (Robertson)': 'Квадрат (Robertson)', 'Pentagon': "П'ятигранник", 'Slot': 'Шліц', 'Cross (Phillips)': 'Хрест (Phillips)', 'None': 'Немає', 'Hex nut (ISO 4032)': 'Шестигранна (ISO 4032)', 'Thin / jam nut (ISO 4035)': 'Низька / контргайка (ISO 4035)', 'Nylon-insert lock nut (ISO 7040)': 'Самоконтрівна з нейлоновим кільцем (ISO 7040)', 'Sleeve nut (furniture), flat head': 'Меблева гайка-втулка, плоска головка', 'Sleeve nut (furniture), countersunk head': 'Меблева гайка-втулка, потайна головка', 'Coupling nut (DIN 6334, 3d long)': 'Подовжувальна (DIN 6334, 3d)', 'Flat (ISO 7089)': 'Плоска (ISO 7089)', 'Spring lock / split (DIN 127)': 'Пружинна / гровер (DIN 127)', 'Language': 'Мова'}

def T(s):
    return UA.get(s, s) if LANG == "ua" else s

C = None  # fastener_core, imported lazily (the CAD kernel takes a few seconds)


def load_core():
    global C
    if C is None:
        sys.path.insert(0, HERE)
        import fastener_core as core
        C = core
    return C


def fnum(s, default=None):
    s = str(s).strip().replace(",", ".")
    if s == "":
        return default
    return float(s)


def fmt(x):
    return ("%g" % x)


# --------------------------------------------------------------------------
def build(spec):
    """spec -> (shape or list of (name, shape), file base name)"""
    C = load_core()
    hand = spec["hand"]; merge = spec["merge"]
    lh = "_LH" if hand == "left" else ""
    kind = spec["kind"]

    def screw_from(spec):
        if spec["s_mode"] == "std":
            lab, cls, ft = C.SCREW_CATALOG[spec["s_type"]]
            L = fnum(spec["s_len"])
            shp = C.make_std_screw(cls, ft, spec["s_size"], L, hand, merge)
            d, p = C.parse_size(spec["s_size"])
            return shp, f"{ft.upper()}_{spec['s_size']}x{fmt(L)}{lh}", d, p
        d = fnum(spec["c_d"]); p = fnum(spec["c_p"]); L = fnum(spec["c_len"])
        tl = fnum(spec["c_tl"], 0.0)
        dk = fnum(spec["c_dk"], None); k = fnum(spec["c_k"], None)
        head = C.CUSTOM_HEADS[spec["c_head"]]; drive = C.DRIVES[spec["c_drive"]]
        shp = C.make_custom_screw(d, p, L, head, drive, hand, tl, dk, k, merge)
        hcode = ["CYL", "BUTTON", "CSK", "RCSK", "PAN", "HEX", "HEXFL", "SET"][spec["c_head"]]
        dcode = ["HEX", "TORX", "TRI", "SQ", "PENTA", "SLOT", "PH", "NONE"][spec["c_drive"]]
        return shp, f"{hcode}-{dcode}_M{fmt(d)}x{fmt(p)}x{fmt(L)}{lh}", d, p

    if kind == "screw":
        shp, name, _, _ = screw_from(spec)
        return shp, name

    if kind == "nut":
        if spec["n_mode"] == "std":
            lab, cls, ft = C.NUT_CATALOG[spec["n_type"]]
            return C.make_std_nut(cls, ft, spec["n_size"], hand, merge), f"{ft.upper()}_{spec['n_size']}{lh}"
        d = fnum(spec["cn_d"]); p = fnum(spec["cn_p"])
        t = C.CUSTOM_NUTS[spec["cn_type"]]
        L = fnum(spec["cn_len"], None)
        drive = C.DRIVES[spec["cn_drive"]]
        code = ["HEXNUT", "THINNUT", "NYLOC", "SLEEVE", "SLEEVE-CSK", "COUPLING"][spec["cn_type"]]
        return C.make_custom_nut(d, p, t, hand, L, drive, merge), f"{code}_M{fmt(d)}x{fmt(p)}{lh}"

    if kind == "washer":
        if spec["w_mode"] == "std":
            lab, cls, ft = C.WASHER_CATALOG[spec["w_type"]]
            return C.make_std_washer(cls, ft, spec["w_size"]), f"{ft.upper()}_{spec['w_size']}"
        d = fnum(spec["cw_d"]); t = C.CUSTOM_WASHERS[spec["cw_type"]]
        code = ["WASHER", "SPRING"][spec["cw_type"]]
        return C.make_custom_washer(d, t), f"{code}_M{fmt(d)}"

    if kind == "rod":
        d = fnum(spec["r_d"]); p = fnum(spec["r_p"]); L = fnum(spec["r_len"])
        return C.make_threaded_rod(d, p, L, hand, merge), f"ROD_M{fmt(d)}x{fmt(p)}x{fmt(L)}{lh}"

    if kind == "kit":
        bolt, bname, d, p = screw_from(spec)
        from bd_warehouse import fastener as F
        size = f"M{fmt(d)}-{fmt(p)}"
        try:
            nut = C.make_std_nut(F.HexNut, "iso4032", size, hand, merge)
        except Exception:
            nut = C.make_custom_nut(d, p, C.CUSTOM_NUTS[0], hand, merge=merge)
        washer = None
        if spec["k_wh"] or spec["k_wn"]:
            try:
                washer = C.make_std_washer(F.PlainWasher, "iso7089", f"M{fmt(d)}")
            except Exception:
                washer = C.make_custom_washer(d, C.CUSTOM_WASHERS[0])
        grip = fnum(spec["k_grip"])
        items = C.make_kit(bolt, nut, washer, grip, spec["k_wh"], spec["k_wn"])
        return items, f"KIT_{bname}_grip{fmt(grip)}"
    raise ValueError(kind)


# --------------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(T("Boltsmith — fastener generator → STEP (real threads)"))

        try:
            if sys.platform == "win32":
                self.iconbitmap(default=os.path.join(HERE, "boltsmith.ico"))
            else:
                self._icon_img = tk.PhotoImage(file=os.path.join(HERE, "boltsmith.png"))
                self.iconphoto(True, self._icon_img)
        except Exception:
            pass
        sc = os.environ.get("FASTENER_SCALING")
        if sc:
            self.tk.call("tk", "scaling", float(sc))
        st = ttk.Style(self)
        if "vista" in st.theme_names():
            st.theme_use("vista")
        self.v = {}
        self.busy = False
        self.cat = None
        self._build()
        self.after(100, self._load_catalogs)

    # ---------------- helpers
    def var(self, key, val=""):
        v = tk.StringVar(value=val) if not isinstance(val, bool) else tk.BooleanVar(value=val)
        self.v[key] = v
        return v

    def row(self, parent, r, label, widget):
        ttk.Label(parent, text=label).grid(row=r, column=0, sticky="w", padx=6, pady=3)
        widget.grid(row=r, column=1, sticky="we", padx=6, pady=3)
        parent.columnconfigure(1, weight=1)

    def combo(self, parent, key, values, width=44, readonly=True, val=None):
        v = self.var(key, val if val is not None else (values[0] if values else ""))
        cb = ttk.Combobox(parent, textvariable=v, values=values, width=width,
                          state="readonly" if readonly else "normal")
        cb._ro = readonly
        return cb

    def entry(self, parent, key, val="", width=12):
        return ttk.Entry(parent, textvariable=self.var(key, val), width=width)

    # ---------------- layout
    def _build(self):
        top = ttk.Frame(self); top.pack(fill="both", expand=True, padx=8, pady=8)
        lb = ttk.Frame(top); lb.pack(fill="x", pady=(0, 4))
        try:
            if not hasattr(self, "_logo"):
                self._logo = tk.PhotoImage(file=os.path.join(HERE, "boltsmith.png")).subsample(8, 8)
            ttk.Label(lb, image=self._logo).pack(side="left")
        except Exception:
            pass
        ttk.Label(lb, text="Boltsmith", font=("Segoe UI", 13, "bold")).pack(side="left", padx=(6, 4))
        ttk.Label(lb, text=T("fastener generator → STEP"), foreground="#667").pack(side="left")
        self.lang_var = tk.StringVar(value="Українська" if LANG == "ua" else "English")
        cbl = ttk.Combobox(lb, textvariable=self.lang_var, values=["Українська", "English"],
                           state="readonly", width=12)
        cbl.pack(side="right")
        ttk.Label(lb, text="Мова / Language:").pack(side="right", padx=6)
        cbl.bind("<<ComboboxSelected>>", lambda e: self._switch_lang())
        self.nb = ttk.Notebook(top); self.nb.pack(fill="both", expand=True)
        self.tabs = {}
        for key, title in [("screw", T("Bolt / Screw")), ("nut", T("Nut")), ("washer", T("Washer")),
                           ("rod", T("Threaded rod")), ("kit", T("Kit"))]:
            f = ttk.Frame(self.nb, padding=8); self.nb.add(f, text=title); self.tabs[key] = f

        # --- screw tab
        f = self.tabs["screw"]
        self.var("s_mode", "std")
        mf = ttk.Frame(f); mf.pack(fill="x")
        ttk.Radiobutton(mf, text=T("Standard (ISO / DIN)"), variable=self.v["s_mode"], value="std",
                        command=self._modes).pack(side="left", padx=4)
        ttk.Radiobutton(mf, text=T("Custom (M1–M100, any head & drive)"),
                        variable=self.v["s_mode"], value="custom", command=self._modes).pack(side="left", padx=4)
        self.s_std = ttk.LabelFrame(f, text=T("Standard"), padding=6); self.s_std.pack(fill="x", pady=6)
        self.cb_s_type = self.combo(self.s_std, "s_type_lab", [], width=48)
        self.cb_s_type.bind("<<ComboboxSelected>>", lambda e: self._sizes("s"))
        self.row(self.s_std, 0, T("Type"), self.cb_s_type)
        self.cb_s_size = self.combo(self.s_std, "s_size", [], width=16)
        self.row(self.s_std, 1, T("Size"), self.cb_s_size)
        self.row(self.s_std, 2, T("Length, mm"), self.entry(self.s_std, "s_len", "20"))
        ttk.Label(self.s_std, text=T("Length is measured under the head; overall for countersunk heads."),
                  foreground="#666").grid(row=3, column=0, columnspan=2, sticky="w", padx=6)

        self.s_cus = ttk.LabelFrame(f, text=T("Custom"), padding=6); self.s_cus.pack(fill="x", pady=6)
        self._dp_rows(self.s_cus, "c", 0)
        self.cb_c_head = self.combo(self.s_cus, "c_head_lab", [], width=30)
        self.row(self.s_cus, 2, T("Head"), self.cb_c_head)
        self.cb_c_drive = self.combo(self.s_cus, "c_drive_lab", [], width=30)
        self.row(self.s_cus, 3, T("Drive"), self.cb_c_drive)
        self.row(self.s_cus, 4, T("Length, mm"), self.entry(self.s_cus, "c_len", "20"))
        self.row(self.s_cus, 5, T("Thread length, mm (0 = full)"), self.entry(self.s_cus, "c_tl", "0"))
        self.row(self.s_cus, 6, T("Head diameter, mm (empty = auto)"), self.entry(self.s_cus, "c_dk", ""))
        self.row(self.s_cus, 7, T("Head height, mm (empty = auto)"), self.entry(self.s_cus, "c_k", ""))

        # --- nut tab
        f = self.tabs["nut"]
        self.var("n_mode", "std")
        mf = ttk.Frame(f); mf.pack(fill="x")
        ttk.Radiobutton(mf, text=T("Standard (ISO / DIN)"), variable=self.v["n_mode"], value="std",
                        command=self._modes).pack(side="left", padx=4)
        ttk.Radiobutton(mf, text=T("Custom (M1–M100, nyloc, sleeve nut...)"),
                        variable=self.v["n_mode"], value="custom", command=self._modes).pack(side="left", padx=4)
        self.n_std = ttk.LabelFrame(f, text=T("Standard"), padding=6); self.n_std.pack(fill="x", pady=6)
        self.cb_n_type = self.combo(self.n_std, "n_type_lab", [], width=48)
        self.cb_n_type.bind("<<ComboboxSelected>>", lambda e: self._sizes("n"))
        self.row(self.n_std, 0, T("Type"), self.cb_n_type)
        self.cb_n_size = self.combo(self.n_std, "n_size", [], width=24)
        self.row(self.n_std, 1, T("Size"), self.cb_n_size)
        self.n_cus = ttk.LabelFrame(f, text=T("Custom"), padding=6); self.n_cus.pack(fill="x", pady=6)
        self._dp_rows(self.n_cus, "cn", 0)
        self.cb_cn_type = self.combo(self.n_cus, "cn_type_lab", [], width=44)
        self.row(self.n_cus, 2, T("Type"), self.cb_cn_type)
        self.row(self.n_cus, 3, T("Length, mm (sleeve / coupling; empty = auto)"), self.entry(self.n_cus, "cn_len", ""))
        self.cb_cn_drive = self.combo(self.n_cus, "cn_drive_lab", [], width=30)
        self.row(self.n_cus, 4, T("Drive (sleeve nut)"), self.cb_cn_drive)

        # --- washer tab
        f = self.tabs["washer"]
        self.var("w_mode", "std")
        mf = ttk.Frame(f); mf.pack(fill="x")
        ttk.Radiobutton(mf, text=T("Standard (ISO / DIN)"), variable=self.v["w_mode"], value="std",
                        command=self._modes).pack(side="left", padx=4)
        ttk.Radiobutton(mf, text=T("Custom (any size, spring lock)"), variable=self.v["w_mode"],
                        value="custom", command=self._modes).pack(side="left", padx=4)
        self.w_std = ttk.LabelFrame(f, text=T("Standard"), padding=6); self.w_std.pack(fill="x", pady=6)
        self.cb_w_type = self.combo(self.w_std, "w_type_lab", [], width=48)
        self.cb_w_type.bind("<<ComboboxSelected>>", lambda e: self._sizes("w"))
        self.row(self.w_std, 0, T("Type"), self.cb_w_type)
        self.cb_w_size = self.combo(self.w_std, "w_size", [], width=16)
        self.row(self.w_std, 1, T("Size"), self.cb_w_size)
        self.w_cus = ttk.LabelFrame(f, text=T("Custom"), padding=6); self.w_cus.pack(fill="x", pady=6)
        self.row(self.w_cus, 0, T("For bolt M, mm"), self.combo(self.w_cus, "cw_d", [], 10, readonly=False, val="8"))
        self.cb_cw_type = self.combo(self.w_cus, "cw_type_lab", [], width=30)
        self.row(self.w_cus, 1, T("Type"), self.cb_cw_type)

        # --- rod tab
        f = self.tabs["rod"]
        lf = ttk.LabelFrame(f, text=T("Threaded rod (DIN 975)"), padding=6); lf.pack(fill="x", pady=6)
        self._dp_rows(lf, "r", 0)
        self.row(lf, 2, T("Length, mm"), self.entry(lf, "r_len", "50"))

        # --- kit tab
        f = self.tabs["kit"]
        ttk.Label(f, text=T("The bolt is taken from the «Bolt / Screw» tab (standard or custom).\n"
                            "An ISO 4032 nut and ISO 7089 washers of the same size are added automatically\n"
                            "(non-standard sizes use formula-based parts)."),
                  justify="left").pack(anchor="w", pady=4)
        lf = ttk.LabelFrame(f, text=T("Assembly"), padding=6); lf.pack(fill="x", pady=6)
        self.row(lf, 0, T("Grip (clamped stack thickness), mm"), self.entry(lf, "k_grip", "10"))
        ttk.Checkbutton(lf, text=T("Washer under head"), variable=self.var("k_wh", True)).grid(row=1, column=0, sticky="w", padx=6)
        ttk.Checkbutton(lf, text=T("Washer under nut"), variable=self.var("k_wn", True)).grid(row=2, column=0, sticky="w", padx=6)
        ttk.Label(f, text=T("Each part is a separate body in the STEP (bolt, nut, washer)."),
                  foreground="#666").pack(anchor="w")

        # --- common
        cf = ttk.LabelFrame(top, text=T("General"), padding=6); cf.pack(fill="x", pady=6)
        self.var("hand", "right")
        hf = ttk.Frame(cf); hf.grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(hf, text=T("Thread:")).pack(side="left", padx=6)
        ttk.Radiobutton(hf, text=T("right-hand"), variable=self.v["hand"], value="right").pack(side="left")
        ttk.Radiobutton(hf, text=T("left-hand (LH)"), variable=self.v["hand"], value="left").pack(side="left", padx=6)
        ttk.Checkbutton(cf, text=T("Single solid body (merge thread with part)"),
                        variable=self.var("merge", True)).grid(row=1, column=0, columnspan=3, sticky="w", padx=6)
        ttk.Checkbutton(cf, text=T("Also save STL (for printing)"),
                        variable=self.var("stl", False)).grid(row=2, column=0, columnspan=3, sticky="w", padx=6)
        ttk.Label(cf, text=T("Folder:")).grid(row=3, column=0, sticky="w", padx=6)
        ttk.Entry(cf, textvariable=self.var("out", OUT_DEFAULT)).grid(row=3, column=1, sticky="we", padx=4)
        ttk.Button(cf, text="…", width=3, command=self._pick).grid(row=3, column=2)
        cf.columnconfigure(1, weight=1)

        bf = ttk.Frame(top); bf.pack(fill="x")
        self.btn = ttk.Button(bf, text=T("Generate STEP"), command=self._go)
        self.btn.pack(side="left", padx=4, ipadx=10, ipady=3)
        ttk.Button(bf, text=T("Open folder"), command=self._open_dir).pack(side="left", padx=4)
        self.btn_open = ttk.Button(bf, text=T("Open file"), command=self._open_file, state="disabled")
        self.btn_open.pack(side="left", padx=4)
        self.status = tk.StringVar(value=T("Loading CAD kernel…"))
        ttk.Label(top, textvariable=self.status, foreground="#245", wraplength=580,
                  justify="left").pack(fill="x", pady=6)
        if not hasattr(self, "last_file"):
            self.last_file = None
        self._modes()

    def _dp_rows(self, parent, pre, r0):
        cb = self.combo(parent, f"{pre}_d", [], 10, readonly=False, val="6")
        cbp = self.combo(parent, f"{pre}_p", [], 10, readonly=False, val="1")
        self.row(parent, r0, T("Diameter M, mm"), cb)
        self.row(parent, r0 + 1, T("Thread pitch, mm"), cbp)
        cb.bind("<<ComboboxSelected>>", lambda e, pre=pre: self._auto_pitch(pre))
        cb.bind("<FocusOut>", lambda e, pre=pre: self._auto_pitch(pre))
        setattr(self, f"cb_{pre}_d", cb); setattr(self, f"cb_{pre}_p", cbp)

    # ---------------- logic
    def _load_catalogs(self):
        def work():
            try:
                core = load_core()
                cat = {
                    "s": [(lab, [s for s in core.catalog_sizes(c, t)]) for lab, c, t in core.SCREW_CATALOG],
                    "n": [(lab, [s for s in core.catalog_sizes(c, t)]) for lab, c, t in core.NUT_CATALOG],
                    "w": [(lab, [s for s in core.catalog_sizes(c, t)]) for lab, c, t in core.WASHER_CATALOG],
                }
                self.after(0, lambda: self._fill(core, cat))
            except Exception as e:
                err = traceback.format_exc()
                self.after(0, lambda: self.status.set(T("Failed to load the CAD kernel:\n") + err[-600:]))
        threading.Thread(target=work, daemon=True).start()

    def _switch_lang(self):
        global LANG
        new = "ua" if self.lang_var.get() == "Українська" else "en"
        if new == LANG:
            return
        # snapshot
        vals = {k: v.get() for k, v in self.v.items()}
        idx = {name: getattr(self, name).current() for name in
               ("cb_s_type", "cb_n_type", "cb_w_type", "cb_c_head", "cb_c_drive",
                "cb_cn_type", "cb_cn_drive", "cb_cw_type")}
        tab = self.nb.index(self.nb.select())
        status_ready = not self.busy
        LANG = new
        _save_settings(lang=new)
        for w in self.winfo_children():
            w.destroy()
        self.v = {}
        self._build()
        self.title(T("Boltsmith — fastener generator → STEP (real threads)"))
        if self.cat:
            self._fill(load_core(), self.cat)
            for name, i in idx.items():
                if i >= 0:
                    getattr(self, name).current(i)
            for pre in ("s", "n", "w"):
                self._sizes(pre)
            for k, v in vals.items():
                if k in self.v and not k.endswith("_lab"):
                    self.v[k].set(v)
        self.nb.select(tab)
        self._modes()
        if self.last_file:
            self.btn_open.configure(state="normal")

    def _fill(self, core, cat):
        self.cat = cat
        for pre, cb in (("s", self.cb_s_type), ("n", self.cb_n_type), ("w", self.cb_w_type)):
            labs = [T(l) for l, _ in cat[pre]]
            cb["values"] = labs; cb.set(labs[0]); self._sizes(pre)
        sizes = [fmt(x) for x in core.NOMINAL_SIZES]
        pitches = [fmt(x) for x in core.STANDARD_PITCHES]
        for pre in ("c", "cn", "r"):
            getattr(self, f"cb_{pre}_d")["values"] = sizes
            getattr(self, f"cb_{pre}_p")["values"] = pitches
        for cb, vals in ((self.cb_c_head, core.CUSTOM_HEADS), (self.cb_c_drive, core.DRIVES),
                         (self.cb_cn_type, core.CUSTOM_NUTS), (self.cb_cn_drive, core.DRIVES),
                         (self.cb_cw_type, core.CUSTOM_WASHERS)):
            vals = [T(x) for x in vals]; cb["values"] = vals; cb.set(vals[0])
        self.v["cw_d"].set("8")
        self.status.set(T("Ready. Choose parameters and press «Generate STEP»."))
        self._fit()

    def _sizes(self, pre):
        if not self.cat:
            return
        cb_t = {"s": self.cb_s_type, "n": self.cb_n_type, "w": self.cb_w_type}[pre]
        cb_s = {"s": self.cb_s_size, "n": self.cb_n_size, "w": self.cb_w_size}[pre]
        i = cb_t.current()
        sizes = self.cat[pre][max(i, 0)][1]
        cb_s["values"] = sizes
        prefer = [s for s in sizes if s.startswith("M6-") or s == "M6"] or \
                 [s for s in sizes if s.startswith("M5") or s.startswith("M4")] or sizes
        cb_s.set(prefer[0] if prefer else "")

    def _auto_pitch(self, pre):
        try:
            d = fnum(self.v[f"{pre}_d"].get())
            self.v[f"{pre}_p"].set(fmt(load_core().coarse_pitch(d)))
        except Exception:
            pass

    def _modes(self):
        """Show only the active block (standard or custom) and resize the window to fit."""
        for mode_key, std, cus in (("s_mode", self.s_std, self.s_cus), ("n_mode", self.n_std, self.n_cus),
                                   ("w_mode", self.w_std, self.w_cus)):
            on_std = self.v[mode_key].get() == "std"
            std.pack_forget(); cus.pack_forget()
            (std if on_std else cus).pack(fill="x", pady=6)
        self._fit()

    def _fit(self):
        self.update_idletasks()
        w = max(self.winfo_reqwidth(), 560)
        h = self.winfo_reqheight()
        sh = self.winfo_screenheight() - 80
        h = min(h, sh)
        self.minsize(w, h)
        cur_w, cur_h = self.winfo_width(), self.winfo_height()
        if cur_w < w or cur_h != h:
            self.geometry(f"{max(cur_w, w)}x{h}")

    def _pick(self):
        d = filedialog.askdirectory(initialdir=self.v["out"].get() or HERE)
        if d:
            self.v["out"].set(d)

    def _open_dir(self):
        d = self.v["out"].get() or OUT_DEFAULT
        os.makedirs(d, exist_ok=True)
        open_path(d)

    def _open_file(self):
        if self.last_file and os.path.exists(self.last_file):
            open_path(self.last_file)

    def _spec(self):
        g = lambda k: self.v[k].get()
        kind = ["screw", "nut", "washer", "rod", "kit"][self.nb.index(self.nb.select())]
        spec = dict(kind=kind, hand=g("hand"), merge=bool(g("merge")),
                    s_mode=g("s_mode"), s_type=self.cb_s_type.current(), s_size=g("s_size"), s_len=g("s_len"),
                    c_d=g("c_d"), c_p=g("c_p"), c_head=self.cb_c_head.current(),
                    c_drive=self.cb_c_drive.current(), c_len=g("c_len"), c_tl=g("c_tl"),
                    c_dk=g("c_dk"), c_k=g("c_k"),
                    n_mode=g("n_mode"), n_type=self.cb_n_type.current(), n_size=g("n_size"),
                    cn_d=g("cn_d"), cn_p=g("cn_p"), cn_type=self.cb_cn_type.current(),
                    cn_len=g("cn_len"), cn_drive=self.cb_cn_drive.current(),
                    w_mode=g("w_mode"), w_type=self.cb_w_type.current(), w_size=g("w_size"),
                    cw_d=g("cw_d"), cw_type=self.cb_cw_type.current(),
                    r_d=g("r_d"), r_p=g("r_p"), r_len=g("r_len"),
                    k_grip=g("k_grip"), k_wh=bool(g("k_wh")), k_wn=bool(g("k_wn")))
        return spec

    def _go(self):
        if self.busy or not self.cat:
            return
        try:
            spec = self._spec()
        except Exception as e:
            messagebox.showerror(T("Error"), str(e)); return
        out = self.v["out"].get() or OUT_DEFAULT
        stl = bool(self.v["stl"].get())
        self.busy = True; self.btn.configure(state="disabled")
        self.status.set(T("Generating… (real threads: a few seconds up to ~a minute)"))
        t0 = time.time()

        def work():
            try:
                shp, name = build(spec)
                os.makedirs(out, exist_ok=True)
                path = os.path.join(out, re.sub(r"[^\w.\-]+", "_", name) + ".step")
                load_core().export(shp, path, also_stl=stl)
                if isinstance(shp, list):
                    nb = sum(len(s.solids()) for _, s in shp)
                    note = T("Assembly: {n} parts (each a separate body)").format(n=len(shp))
                else:
                    nb = len(shp.solids())
                    nyl = spec["kind"] == "nut" and spec["n_mode"] == "custom" and spec["cn_type"] == 2
                    note = T("1 solid body") if nb == 1 else (T("2 bodies: steel nut + nylon insert") if nyl and nb == 2 else
                            T("{n} bodies: part + thread separate (kernel could not merge — use Combine in your CAD)").format(n=nb))
                msg = T("Done in {t} s: {path}\n{note}").format(t="%.1f" % (time.time() - t0), path=path, note=note)
                self.after(0, lambda: self._done(msg, path))
            except Exception as e:
                err = str(e) or e.__class__.__name__
                tb = traceback.format_exc()
                print(tb)
                self.after(0, lambda: self._done(T("Error: ") + err, None))
        threading.Thread(target=work, daemon=True).start()

    def _done(self, msg, path):
        self.busy = False; self.btn.configure(state="normal")
        self.status.set(msg)
        self._fit()
        if path:
            self.last_file = path; self.btn_open.configure(state="normal")


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Boltsmith.FastenerGenerator")
        except Exception:
            pass
    App().mainloop()
