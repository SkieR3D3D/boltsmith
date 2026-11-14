# -*- coding: utf-8 -*-
# Boltsmith for Blender — fastener generator with real helical threads.
# The heavy CAD kernel (build123d / OpenCascade) runs outside Blender through `uv`;
# the add-on sends the parameters, receives the mesh and places it at the 3D cursor.

bl_info = {
    "name": "Boltsmith",
    "author": "Boltsmith",
    "version": (1, 1, 0),
    "blender": (4, 2, 0),
    "location": "3D Viewport > Sidebar (N) > Boltsmith",
    "description": "Bolts, nuts, washers, threaded rods and kits with real ISO threads",
    "category": "Add Mesh",
}

import json, math, os, shutil, subprocess, sys, tempfile, threading

import bpy
from bpy.props import (BoolProperty, EnumProperty, FloatProperty, PointerProperty,
                       StringProperty)

HERE = os.path.dirname(os.path.abspath(__file__))
CAT = json.load(open(os.path.join(HERE, "catalog.json"), encoding="utf-8"))
DEPS = ["--python", "3.12", "--with", "build123d==0.13.0", "--with", "bd_warehouse==0.4.0"]
PKG = __package__ or __name__


# ----------------------------------------------------------------- helpers
def _enum(lst):
    return [(str(i), lab, "") for i, lab in enumerate(lst)]


def _coarse(d):
    tbl = {float(k): v for k, v in CAT["coarse_pitch"].items()}
    k = min(tbl, key=lambda x: abs(x - d))
    return tbl[k]


_SIZE_CACHE = {}


def _size_items_for(kind, idx):
    key = (kind, idx)
    if key not in _SIZE_CACHE:
        try:
            sizes = CAT[kind][int(idx)]["sizes"]
        except Exception:
            sizes = []
        _SIZE_CACHE[key] = [(s, s, "") for s in sizes] or [("-", "-", "")]
    return _SIZE_CACHE[key]


def _preferred(items):
    ids = [i[0] for i in items]
    for pref in ("M6-1", "M6", "M5-0.8", "M5", "M4-0.7", "M4"):
        if pref in ids:
            return pref
    return ids[0]


def s_size_items(self, context):  return _size_items_for("screw", self.s_type)
def n_size_items(self, context):  return _size_items_for("nut", self.n_type)
def w_size_items(self, context):  return _size_items_for("washer", self.w_type)


def _upd_type(kind, typ_attr, size_attr):
    def f(self, context):
        items = _size_items_for(kind, getattr(self, typ_attr))
        try:
            setattr(self, size_attr, _preferred(items))
        except Exception:
            pass
    return f


def _upd_pitch(d_attr, p_attr):
    def f(self, context):
        setattr(self, p_attr, _coarse(getattr(self, d_attr)))
    return f


def find_uv(prefs):
    cands = []
    if prefs and prefs.uv_path:
        cands.append(bpy.path.abspath(prefs.uv_path))
    w = shutil.which("uv")
    if w:
        cands.append(w)
    home = os.path.expanduser("~")
    exe = "uv.exe" if sys.platform == "win32" else "uv"
    cands += [os.path.join(home, ".local", "bin", exe), os.path.join(home, ".cargo", "bin", exe),
              "/opt/homebrew/bin/uv", "/usr/local/bin/uv"]
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return None


def get_prefs(context):
    try:
        return context.preferences.addons[PKG].preferences
    except Exception:
        return None


# ----------------------------------------------------------------- properties
class BoltsmithProps(bpy.types.PropertyGroup):
    kind: EnumProperty(name="Part", items=[("screw", "Bolt", "Bolt / screw"), ("nut", "Nut", ""),
                                           ("washer", "Washer", ""), ("rod", "Rod", "Threaded rod"),
                                           ("kit", "Kit", "Bolt + nut + washers")], default="screw")
    # screw
    s_mode: EnumProperty(name="Mode", items=[("std", "Standard", "ISO / DIN tables"),
                                             ("custom", "Custom", "M1–M100, any head and drive")])
    s_type: EnumProperty(name="Type", items=_enum([x["label"] for x in CAT["screw"]]),
                         update=_upd_type("screw", "s_type", "s_size"))
    s_size: EnumProperty(name="Size", items=s_size_items)
    s_len: FloatProperty(name="Length (mm)", default=20, min=1, max=1000)
    c_d: FloatProperty(name="Diameter M (mm)", default=6, min=1, max=100, update=_upd_pitch("c_d", "c_p"))
    c_p: FloatProperty(name="Pitch (mm)", default=1, min=0.2, max=6, step=5, precision=2)
    c_head: EnumProperty(name="Head", items=_enum(CAT["custom_heads"]))
    c_drive: EnumProperty(name="Drive", items=_enum(CAT["drives"]))
    c_len: FloatProperty(name="Length (mm)", default=20, min=1, max=1000)
    c_tl: FloatProperty(name="Thread length (0 = full)", default=0, min=0, max=1000)
    c_dk: FloatProperty(name="Head Ø (0 = auto)", default=0, min=0, max=300)
    c_k: FloatProperty(name="Head height (0 = auto)", default=0, min=0, max=200)
    # nut
    n_mode: EnumProperty(name="Mode", items=[("std", "Standard", ""), ("custom", "Custom", "")])
    n_type: EnumProperty(name="Type", items=_enum([x["label"] for x in CAT["nut"]]),
                         update=_upd_type("nut", "n_type", "n_size"))
    n_size: EnumProperty(name="Size", items=n_size_items)
    cn_d: FloatProperty(name="Diameter M (mm)", default=6, min=1, max=100, update=_upd_pitch("cn_d", "cn_p"))
    cn_p: FloatProperty(name="Pitch (mm)", default=1, min=0.2, max=6, step=5, precision=2)
    cn_type: EnumProperty(name="Type", items=_enum(CAT["custom_nuts"]))
    cn_len: FloatProperty(name="Length (0 = auto)", default=0, min=0, max=1000)
    cn_drive: EnumProperty(name="Drive", items=_enum(CAT["drives"]))
    # washer
    w_mode: EnumProperty(name="Mode", items=[("std", "Standard", ""), ("custom", "Custom", "")])
    w_type: EnumProperty(name="Type", items=_enum([x["label"] for x in CAT["washer"]]),
                         update=_upd_type("washer", "w_type", "w_size"))
    w_size: EnumProperty(name="Size", items=w_size_items)
    cw_d: FloatProperty(name="For bolt M (mm)", default=8, min=1, max=100)
    cw_type: EnumProperty(name="Type", items=_enum(CAT["custom_washers"]))
    # rod
    r_d: FloatProperty(name="Diameter M (mm)", default=10, min=1, max=100, update=_upd_pitch("r_d", "r_p"))
    r_p: FloatProperty(name="Pitch (mm)", default=1.5, min=0.2, max=6, step=5, precision=2)
    r_len: FloatProperty(name="Length (mm)", default=50, min=1, max=3000)
    # kit
    k_grip: FloatProperty(name="Grip (mm)", description="Thickness of the clamped parts", default=10, min=0, max=1000)
    k_wh: BoolProperty(name="Washer under head", default=True)
    k_wn: BoolProperty(name="Washer under nut", default=True)
    # general
    hand: EnumProperty(name="Thread", items=[("right", "Right-hand", ""), ("left", "Left-hand", "")])
    merge: BoolProperty(name="Single solid (merge thread)", default=True)
    detail: EnumProperty(name="Mesh detail", default="MED",
                         items=[("LOW", "Low", "Fast, light mesh"), ("MED", "Medium", ""),
                                ("HIGH", "High", "Fine mesh for close-up renders")])
    save_step: BoolProperty(name="Also save STEP", default=False,
                            description="Save a STEP file too (folder in add-on preferences)")


class BoltsmithPrefs(bpy.types.AddonPreferences):
    bl_idname = PKG
    uv_path: StringProperty(name="uv executable", subtype="FILE_PATH",
                            description="Leave empty to auto-detect")
    step_dir: StringProperty(name="STEP folder", subtype="DIR_PATH",
                             default=os.path.join(os.path.expanduser("~"), "Documents", "Boltsmith", "step"))

    def draw(self, context):
        col = self.layout.column()
        uv = find_uv(self)
        col.label(text=("uv found: " + uv) if uv else "uv not found — install Boltsmith (or uv) first",
                  icon="CHECKMARK" if uv else "ERROR")
        col.prop(self, "uv_path")
        col.prop(self, "step_dir")


class BoltsmithState(bpy.types.PropertyGroup):
    busy: BoolProperty(default=False)
    message: StringProperty(default="")


# ----------------------------------------------------------------- spec
def make_spec(p, prefs):
    f = lambda x: ("%g" % x)
    tol = {"LOW": (0.06, 0.35), "MED": (0.02, 0.2), "HIGH": (0.005, 0.1)}[p.detail]
    return dict(
        kind=p.kind, hand=p.hand, merge=p.merge, tol=tol[0], ang=tol[1],
        step_dir=(bpy.path.abspath(prefs.step_dir) if (p.save_step and prefs) else None),
        s_mode=p.s_mode, s_type=int(p.s_type), s_size=p.s_size, s_len=f(p.s_len),
        c_d=f(p.c_d), c_p=f(p.c_p), c_head=int(p.c_head), c_drive=int(p.c_drive), c_len=f(p.c_len),
        c_tl=f(p.c_tl), c_dk=(f(p.c_dk) if p.c_dk > 0 else ""), c_k=(f(p.c_k) if p.c_k > 0 else ""),
        n_mode=p.n_mode, n_type=int(p.n_type), n_size=p.n_size, cn_d=f(p.cn_d), cn_p=f(p.cn_p),
        cn_type=int(p.cn_type), cn_len=(f(p.cn_len) if p.cn_len > 0 else ""), cn_drive=int(p.cn_drive),
        w_mode=p.w_mode, w_type=int(p.w_type), w_size=p.w_size, cw_d=f(p.cw_d), cw_type=int(p.cw_type),
        r_d=f(p.r_d), r_p=f(p.r_p), r_len=f(p.r_len),
        k_grip=f(p.k_grip), k_wh=p.k_wh, k_wn=p.k_wn)


# ----------------------------------------------------------------- import
def import_result(context, res):
    scene = context.scene
    unit = scene.unit_settings.scale_length or 1.0
    scale = 0.001 / unit                      # mm -> scene units
    cursor = scene.cursor.location.copy()
    created = []
    for part in res["parts"]:
        before = set(bpy.data.objects)
        bpy.ops.wm.stl_import(filepath=part["stl"], global_scale=scale)
        new = [o for o in bpy.data.objects if o not in before]
        for o in new:
            o.name = part["name"]
            if o.data:
                o.data.name = part["name"]
        created += new
        try:
            os.remove(part["stl"])
        except Exception:
            pass
    if not created:
        return []
    bpy.ops.object.select_all(action="DESELECT")
    for o in created:
        o.select_set(True)
    context.view_layer.objects.active = created[0]
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    except Exception:
        try:
            bpy.ops.object.shade_smooth()
        except Exception:
            pass
    if len(created) > 1:                      # kit: group under an empty
        empty = bpy.data.objects.new(res["name"], None)
        empty.empty_display_type = "PLAIN_AXES"
        empty.empty_display_size = 0.01 / unit
        context.collection.objects.link(empty)
        empty.location = cursor
        for o in created:
            o.parent = empty
        created.insert(0, empty)
    else:
        created[0].location = cursor
    return created


# ----------------------------------------------------------------- operator
class BOLTSMITH_OT_generate(bpy.types.Operator):
    bl_idname = "boltsmith.generate"
    bl_label = "Generate"
    bl_description = "Generate the fastener with real threads and add it at the 3D cursor"
    bl_options = {"REGISTER", "UNDO"}

    _timer = None
    _proc = None
    _lines = None

    def execute(self, context):
        return self.invoke(context, None)

    def invoke(self, context, event):
        st = context.window_manager.boltsmith_state
        if st.busy:
            self.report({"WARNING"}, "Boltsmith is already generating")
            return {"CANCELLED"}
        prefs = get_prefs(context)
        uv = find_uv(prefs)
        if not uv:
            self.report({"ERROR"}, "uv not found. Install Boltsmith first or set the uv path in add-on preferences")
            return {"CANCELLED"}
        spec = make_spec(context.scene.boltsmith, prefs)
        self._tmp = tempfile.mkdtemp(prefix="boltsmith_")
        sp = os.path.join(self._tmp, "spec.json")
        json.dump(spec, open(sp, "w", encoding="utf-8"))
        offline = [] if getattr(bpy.app, "online_access", True) else ["--offline"]
        cmd = [uv, "run", *offline, *DEPS, "python", os.path.join(HERE, "boltsmith_cli.py"), sp, self._tmp]
        flags = 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW
        self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      text=True, encoding="utf-8", errors="replace",
                                      creationflags=flags, cwd=HERE)
        self._lines = []
        self._offline = bool(offline)
        threading.Thread(target=self._reader, daemon=True).start()
        st.busy = True
        st.message = ("Generating… (first run downloads the CAD kernel)" if not offline
                      else "Generating… (offline: uses the cached CAD kernel)")
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.3, window=context.window)
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def _reader(self):
        for line in self._proc.stdout:
            self._lines.append(line.rstrip())

    def _finish(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
        wm.boltsmith_state.busy = False
        for a in context.screen.areas:
            a.tag_redraw()

    def modal(self, context, event):
        st = context.window_manager.boltsmith_state
        if event.type == "ESC":
            self._proc.terminate()
            st.message = "Cancelled"
            self._finish(context)
            return {"CANCELLED"}
        if event.type != "TIMER":
            return {"PASS_THROUGH"}
        if self._proc.poll() is None:
            for a in context.screen.areas:
                if a.type == "VIEW_3D":
                    a.tag_redraw()
            return {"PASS_THROUGH"}
        # finished
        import time
        time.sleep(0.05)
        res = None
        for ln in reversed(self._lines):
            if ln.startswith("BOLTSMITH_RESULT "):
                try:
                    res = json.loads(ln[len("BOLTSMITH_RESULT "):])
                except Exception:
                    pass
                break
        self._finish(context)
        if not res or not res.get("ok"):
            err = (res or {}).get("error") or ("\n".join(self._lines[-6:]) or "unknown error")
            if self._offline and not res:
                err = ("CAD kernel not downloaded yet. Enable Preferences > System > Network > "
                       "Allow Online Access for the first run. " + err)
            st.message = "Error: " + err[:300]
            self.report({"ERROR"}, "Boltsmith: " + err[:300])
            return {"CANCELLED"}
        objs = import_result(context, res)
        bodies = sum(p.get("bodies", 1) for p in res["parts"])
        st.message = f"Added: {res['name']}" + (f"  •  STEP: {res['step']}" if res.get("step") else "")
        self.report({"INFO"}, f"Boltsmith: {res['name']} ({len(res['parts'])} part(s), {bodies} body/bodies)")
        return {"FINISHED"}


class BOLTSMITH_OT_install_uv(bpy.types.Operator):
    bl_idname = "boltsmith.install_uv"
    bl_label = "Install uv"
    bl_description = "Download and install uv (official installer from astral.sh) — needed once"

    _timer = None
    _proc = None

    def invoke(self, context, event):
        st = context.window_manager.boltsmith_state
        if not getattr(bpy.app, "online_access", True):
            self.report({"ERROR"}, "Enable Preferences > System > Network > Allow Online Access first")
            return {"CANCELLED"}
        if sys.platform == "win32":
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "ByPass", "-Command",
                   "irm https://astral.sh/uv/install.ps1 | iex"]
        else:
            cmd = ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"]
        flags = 0x08000000 if sys.platform == "win32" else 0
        self._proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                      creationflags=flags)
        st.busy = True
        st.message = "Installing uv…"
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type != "TIMER" or self._proc.poll() is None:
            return {"PASS_THROUGH"}
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        wm.boltsmith_state.busy = False
        uv = find_uv(get_prefs(context))
        if uv:
            wm.boltsmith_state.message = "uv installed. Press Generate (first run downloads the CAD kernel)"
            self.report({"INFO"}, "Boltsmith: uv installed")
        else:
            wm.boltsmith_state.message = "uv installation failed — see https://docs.astral.sh/uv/"
            self.report({"ERROR"}, "Boltsmith: uv installation failed")
        for a in context.screen.areas:
            a.tag_redraw()
        return {"FINISHED"}


# ----------------------------------------------------------------- UI
class BOLTSMITH_PT_panel(bpy.types.Panel):
    bl_label = "Boltsmith"
    bl_idname = "BOLTSMITH_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Boltsmith"

    def draw(self, context):
        p = context.scene.boltsmith
        st = context.window_manager.boltsmith_state
        L = self.layout
        L.row().prop(p, "kind", expand=True)
        box = L.box()
        k = p.kind
        if k in ("screw", "kit"):
            box.row().prop(p, "s_mode", expand=True)
            if p.s_mode == "std":
                box.prop(p, "s_type", text="")
                box.prop(p, "s_size")
                box.prop(p, "s_len")
            else:
                c = box.column(align=True)
                c.prop(p, "c_d"); c.prop(p, "c_p")
                box.prop(p, "c_head"); box.prop(p, "c_drive")
                c = box.column(align=True)
                c.prop(p, "c_len"); c.prop(p, "c_tl"); c.prop(p, "c_dk"); c.prop(p, "c_k")
            if k == "kit":
                b2 = L.box()
                b2.label(text="Kit: + ISO 4032 nut, ISO 7089 washers")
                b2.prop(p, "k_grip")
                r = b2.row(); r.prop(p, "k_wh"); r.prop(p, "k_wn")
        elif k == "nut":
            box.row().prop(p, "n_mode", expand=True)
            if p.n_mode == "std":
                box.prop(p, "n_type", text=""); box.prop(p, "n_size")
            else:
                c = box.column(align=True); c.prop(p, "cn_d"); c.prop(p, "cn_p")
                box.prop(p, "cn_type", text="")
                if int(p.cn_type) >= 3:
                    box.prop(p, "cn_len")
                if int(p.cn_type) in (3, 4):
                    box.prop(p, "cn_drive")
        elif k == "washer":
            box.row().prop(p, "w_mode", expand=True)
            if p.w_mode == "std":
                box.prop(p, "w_type", text=""); box.prop(p, "w_size")
            else:
                box.prop(p, "cw_d"); box.prop(p, "cw_type", text="")
        elif k == "rod":
            c = box.column(align=True)
            c.prop(p, "r_d"); c.prop(p, "r_p"); c.prop(p, "r_len")

        g = L.box()
        g.row().prop(p, "hand", expand=True)
        g.prop(p, "merge")
        g.prop(p, "detail")
        g.prop(p, "save_step")
        if not find_uv(get_prefs(context)):
            w = L.box()
            w.label(text="One-time setup: uv is not installed", icon="INFO")
            w.label(text="It runs the CAD kernel outside Blender.")
            rr = w.row(); rr.scale_y = 1.4; rr.enabled = not st.busy
            rr.operator("boltsmith.install_uv", icon="IMPORT")
            if st.message:
                L.label(text=st.message[:60])
            return
        r = L.row()
        r.scale_y = 1.6
        r.enabled = not st.busy
        r.operator("boltsmith.generate", text="Generating…" if st.busy else "Generate",
                   icon="TIME" if st.busy else "MESH_CYLINDER")
        if st.message:
            for line in [st.message[i:i + 42] for i in range(0, min(len(st.message), 210), 42)]:
                L.label(text=line)


classes = (BoltsmithProps, BoltsmithPrefs, BoltsmithState, BOLTSMITH_OT_generate,
           BOLTSMITH_OT_install_uv, BOLTSMITH_PT_panel)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.boltsmith = PointerProperty(type=BoltsmithProps)
    bpy.types.WindowManager.boltsmith_state = PointerProperty(type=BoltsmithState)


def unregister():
    del bpy.types.WindowManager.boltsmith_state
    del bpy.types.Scene.boltsmith
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
