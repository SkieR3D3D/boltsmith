# -*- coding: utf-8 -*-
"""
Fastener generator core: standard ISO/DIN fasteners (bd_warehouse tables)
+ custom parametric fasteners M1..M100 with real helical threads.
Units: mm. Screws: head bearing face at Z=0, shank along -Z
(countersunk: head top flush with Z=0). Nuts/washers: from Z=0 up.
"""
import math, os, re, bisect
from build123d import (Solid, Part, Compound, Plane, Pos, Rot, Axis, Location,
                       Circle, Rectangle, RegularPolygon, Polyline, make_face,
                       extrude, revolve, offset, Sketch, Helix, sweep,
                       export_step, export_stl, Vector)
from bd_warehouse import fastener as F
from bd_warehouse.thread import IsoThread

CORE_GAP = 0.02  # core slightly thinner than thread root: avoids coincident faces

# ---------------------------------------------------------------- tables
def _interp(table, d):
    ks = sorted(table)
    if d <= ks[0]:
        return table[ks[0]] * d / ks[0]
    if d >= ks[-1]:
        return table[ks[-1]] * d / ks[-1]
    i = bisect.bisect_left(ks, d)
    if ks[i] == d:
        return table[d]
    a, b = ks[i - 1], ks[i]
    return table[a] + (table[b] - table[a]) * (d - a) / (b - a)

COARSE_PITCH = {1: .25, 1.2: .25, 1.4: .3, 1.6: .35, 1.8: .35, 2: .4, 2.2: .45, 2.5: .45,
    3: .5, 3.5: .6, 4: .7, 4.5: .75, 5: .8, 6: 1, 7: 1, 8: 1.25, 10: 1.5, 12: 1.75, 14: 2,
    16: 2, 18: 2.5, 20: 2.5, 22: 2.5, 24: 3, 27: 3, 30: 3.5, 33: 3.5, 36: 4, 39: 4,
    42: 4.5, 45: 4.5, 48: 5, 52: 5, 56: 5.5, 60: 5.5, 64: 6, 68: 6, 72: 6, 76: 6,
    80: 6, 85: 6, 90: 6, 95: 6, 100: 6}
STANDARD_PITCHES = [0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.6, 0.7, 0.75, 0.8, 1.0,
                    1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
NOMINAL_SIZES = sorted(COARSE_PITCH)

def coarse_pitch(d):
    if d in COARSE_PITCH:
        return COARSE_PITCH[d]
    ks = sorted(COARSE_PITCH)
    return COARSE_PITCH[min(ks, key=lambda k: abs(k - d))]

HEX_S = {1: 2.5, 1.2: 3, 1.4: 3, 1.6: 3.2, 2: 4, 2.5: 5, 3: 5.5, 3.5: 6, 4: 7, 5: 8,
         6: 10, 7: 11, 8: 13, 10: 16, 12: 18, 14: 21, 16: 24, 18: 27, 20: 30, 22: 34,
         24: 36, 27: 41, 30: 46, 33: 50, 36: 55, 39: 60, 42: 65, 45: 70, 48: 75,
         52: 80, 56: 85, 60: 90, 64: 95, 72: 105, 80: 115, 90: 130, 100: 145}
NUT_M = {1: .8, 1.2: 1, 1.4: 1.2, 1.6: 1.3, 2: 1.6, 2.5: 2, 3: 2.4, 3.5: 2.8, 4: 3.2,
         5: 4.7, 6: 5.2, 8: 6.8, 10: 8.4, 12: 10.8, 14: 12.8, 16: 14.8, 18: 15.8,
         20: 18, 22: 19.4, 24: 21.5, 27: 23.8, 30: 25.6, 33: 28.7, 36: 31, 39: 33.4,
         42: 34, 45: 36, 48: 38, 52: 42, 56: 45, 60: 48, 64: 51, 100: 80}
SOCKET_KEY = {1: .9, 1.6: 1.5, 2: 1.5, 2.5: 2, 3: 2.5, 4: 3, 5: 4, 6: 5, 8: 6, 10: 8,
              12: 10, 14: 12, 16: 14, 20: 17, 24: 19, 30: 22, 36: 27, 42: 32, 48: 36,
              56: 41, 64: 46, 100: 70}
SOCKET_DK = {1: 2, 1.6: 3, 2: 3.8, 2.5: 4.5, 3: 5.5, 4: 7, 5: 8.5, 6: 10, 8: 13,
             10: 16, 12: 18, 14: 21, 16: 24, 20: 30, 24: 36, 30: 45, 36: 54}
BUTTON_DK = {3: 5.7, 4: 7.6, 5: 9.5, 6: 10.5, 8: 14, 10: 17.5, 12: 21, 16: 28}
CSK_DK = {3: 6, 4: 8, 5: 10, 6: 12, 8: 16, 10: 20, 12: 24, 16: 30, 20: 36, 24: 39}
TORX_A = {1: .8, 1.6: 1.42, 2: 1.70, 2.5: 2.31, 3: 2.74, 3.5: 3.27, 4: 3.86, 5: 4.43,
          6: 5.52, 8: 6.65, 10: 8.83, 12: 11.22, 14: 13.25, 16: 15.51, 20: 19.92,
          24: 22.13}

def hex_s(d):   return round(_interp(HEX_S, d), 2)
def nut_m(d):   return round(_interp(NUT_M, d), 2)
def key_s(d):   return round(_interp(SOCKET_KEY, d), 2)
def torx_a(d):  return _interp(TORX_A, d) if d <= 24 else 0.92 * d

# ---------------------------------------------------------------- catalogs
SCREW_CATALOG = [
    ("Socket head cap, hex socket — ISO 4762", F.SocketHeadCapScrew, "iso4762"),
    ("Cheese head, Torx — ISO 14580", F.CheeseHeadScrew, "iso14580"),
    ("Cheese head, slotted — ISO 1207", F.CheeseHeadScrew, "iso1207"),
    ("Cheese head, Phillips — ISO 7048", F.CheeseHeadScrew, "iso7048"),
    ("Button head, hex socket — ISO 7380-1", F.ButtonHeadScrew, "iso7380_1"),
    ("Button head with collar — ISO 7380-2", F.ButtonHeadWithCollarScrew, "iso7380_2"),
    ("Countersunk 90°, hex socket — ISO 10642", F.CounterSunkScrew, "iso10642"),
    ("Countersunk, Torx — ISO 14581", F.CounterSunkScrew, "iso14581"),
    ("Countersunk, Torx, high head — ISO 14582", F.CounterSunkScrew, "iso14582"),
    ("Countersunk, slotted — ISO 2009", F.CounterSunkScrew, "iso2009"),
    ("Countersunk, Phillips — ISO 7046", F.CounterSunkScrew, "iso7046"),
    ("Raised countersunk, slotted — ISO 2010", F.RaisedCounterSunkOvalHeadScrew, "iso2010"),
    ("Raised countersunk, Phillips — ISO 7047", F.RaisedCounterSunkOvalHeadScrew, "iso7047"),
    ("Raised countersunk, Torx — ISO 14584", F.RaisedCounterSunkOvalHeadScrew, "iso14584"),
    ("Hex head, fully threaded — ISO 4017", F.HexHeadScrew, "iso4017"),
    ("Hex head, partially threaded — ISO 4014", F.HexHeadScrew, "iso4014"),
    ("Hex head bolt — DIN 931", F.HexHeadScrew, "din931"),
    ("Hex flange bolt — DIN 1665", F.HexHeadWithFlangeScrew, "din1665"),
    ("Hex flange bolt — DIN 1662", F.HexHeadWithFlangeScrew, "din1662"),
    ("Pan head, slotted — ISO 1580", F.PanHeadScrew, "iso1580"),
    ("Pan head, Torx — ISO 14583", F.PanHeadScrew, "iso14583"),
    ("Pan head, Phillips — ISO 7045", F.RaisedCheeseHeadScrew, "iso7045"),
    ("Pan head with collar — DIN 967", F.PanHeadWithCollarScrew, "din967"),
    ("Set screw (headless) — ISO 4026", F.SetScrew, "iso4026"),
    ("Shoulder screw — ISO 7379", F.ShoulderScrew, "iso7379"),
    ("Low profile — OpenBuilds", F.LowProfileScrew, "OpenBuilds"),
]
NUT_CATALOG = [
    ("Hex nut — ISO 4032", F.HexNut, "iso4032"),
    ("Hex nut, style 2 (taller) — ISO 4033", F.HexNut, "iso4033"),
    ("Thin / jam nut — ISO 4035", F.HexNut, "iso4035"),
    ("Hex nut, unchamfered — ISO 4036", F.UnchamferedHexagonNut, "iso4036"),
    ("Flange nut (built-in washer) — DIN 1665", F.HexNutWithFlange, "din1665"),
    ("Domed cap nut (acorn) — DIN 1587", F.DomedCapNut, "din1587"),
    ("Square nut — DIN 557", F.SquareNut, "din557"),
    ("Heat-set insert (3D print) — McMaster-Carr", F.HeatSetNut, "McMaster-Carr"),
    ("Heat-set insert (3D print) — CNC Kitchen", F.HeatSetNut, "CNCKitchen"),
    ("Heat-set insert (3D print) — ruthex", F.HeatSetNut, "ruthex"),
    ("Heat-set insert (3D print) — Hilitchi", F.HeatSetNut, "Hilitchi"),
]
WASHER_CATALOG = [
    ("Flat washer — ISO 7089", F.PlainWasher, "iso7089"),
    ("Flat washer, normal grade — ISO 7091", F.PlainWasher, "iso7091"),
    ("Large flat washer — ISO 7093", F.PlainWasher, "iso7093"),
    ("Extra large flat washer — ISO 7094", F.PlainWasher, "iso7094"),
    ("Chamfered washer — ISO 7090", F.ChamferedWasher, "iso7090"),
    ("Small washer (cheese head) — ISO 7092", F.CheeseHeadWasher, "iso7092"),
    ("Internal tooth lock washer — DIN 6797", F.InternalToothLockWasher, "din6797"),
]

def catalog_sizes(cls, ftype):
    sizes = [s for s in cls.sizes(ftype) if s.startswith("M")]
    def key(s):
        m = re.match(r"M([\d.]+)", s)
        return (float(m.group(1)) if m else 0, s)
    return sorted(sizes, key=key)

CUSTOM_HEADS = ["Socket cap (cylindrical)", "Button (dome)", "Countersunk 90°",
                "Raised countersunk 90°", "Pan head", "Hex head", "Hex head with flange",
                "Headless (set screw)"]
DRIVES = ["Hex socket (Allen)", "Torx", "Triangle", "Square (Robertson)",
          "Pentagon", "Slot", "Cross (Phillips)", "None"]
CUSTOM_NUTS = ["Hex nut (ISO 4032)", "Thin / jam nut (ISO 4035)",
               "Nylon-insert lock nut (ISO 7040)",
               "Sleeve nut (furniture), flat head",
               "Sleeve nut (furniture), countersunk head",
               "Coupling nut (DIN 6334, 3d long)"]
CUSTOM_WASHERS = ["Flat (ISO 7089)", "Spring lock / split (DIN 127)"]

# ---------------------------------------------------------------- helpers
def _to_solid_or_compound(obj):
    """bd_warehouse objects -> single Solid when possible."""
    sols = obj.solids()
    if len(sols) == 1:
        return sols[0]
    return Compound(children=list(sols))

def _bbox_tuple(shapes):
    xs0=ys0=zs0=1e9; xs1=ys1=zs1=-1e9
    for sh in shapes:
        b = sh.bounding_box()
        xs0=min(xs0,b.min.X); ys0=min(ys0,b.min.Y); zs0=min(zs0,b.min.Z)
        xs1=max(xs1,b.max.X); ys1=max(ys1,b.max.Y); zs1=max(zs1,b.max.Z)
    return (xs0,ys0,zs0,xs1,ys1,zs1)

def _fuse_ok(f, sols, vol_min):
    fs = f.solids()
    if len(fs) != 1 or not fs[0].is_valid:
        return None
    a = _bbox_tuple([fs[0]]); b = _bbox_tuple(sols)
    if max(abs(x - y) for x, y in zip(a, b)) > 0.05:
        return None
    if fs[0].volume < vol_min:
        return None
    return fs[0]

def _fuse_all(obj, merge=True):
    sols = list(obj.solids())
    if not merge or len(sols) < 2:
        return obj if len(sols) != 1 else sols[0]
    big = max(sols, key=lambda y: y.volume)
    others = [x for x in sols if x is not big]
    vol_min = big.volume + 0.5 * sum(x.volume for x in others)
    def attempt(fn):
        try:
            return _fuse_ok(fn().clean(), sols, vol_min)
        except Exception:
            return None
    r = attempt(lambda: big.fuse(*others))
    if r is None and len(others) > 1:
        r = attempt(lambda: big.fuse(others[0].fuse(*others[1:], glue=True)))
    if r is not None:
        return r
    # fallback: body + thread as two separate bodies (thread pieces glued into one)
    try:
        g = others[0].fuse(*others[1:], glue=True).clean() if len(others) > 1 else others[0]
        gs = g.solids()
        if len(gs) == 1 and gs[0].is_valid:
            return Compound(children=[big, gs[0]])
    except Exception:
        pass
    return Compound(children=sols)

def _tap(body, d, pitch, z0, length, hand, chamfer=True):
    """Cut an internal thread into `body` along Z from z0, by subtracting a bolt shape."""
    th = _iso_thread(major_diameter=d, pitch=pitch, length=length + 2.5 * pitch, external=True,
                     hand=hand, end_finishes=("raw", "raw"), simple=False)
    th = th.locate(Pos(0, 0, z0 - pitch))
    core = Solid.make_cylinder(th.min_radius + 0.01, length + 4 * pitch,
                               Plane.XY.offset(z0 - 2 * pitch))
    tools = [core, *th.solids()]
    if chamfer:
        c = 0.55 * d
        tools.append(Solid.make_cone(c, 0.01, c, Plane.XY.offset(z0 - 0.5 * c + 0.0)))
        tools.append(Solid.make_cone(c, 0.01, c, Plane(origin=(0, 0, z0 + length + 0.5 * c),
                                                         z_dir=(0, 0, -1))))
    r = body.cut(*tools).clean()
    fs = r.solids()
    return fs[0] if len(fs) == 1 else r

def _iso_thread(**kw):
    """IsoThread with retries: OCC sometimes fails on an almost-whole number of turns."""
    L, p = kw["length"], kw["pitch"]
    last = None
    for dl in (0, 0.07, -0.07, 0.15):
        try:
            kw["length"] = L + dl * p
            return IsoThread(**kw)
        except Exception as e:
            last = e
    raise last

def _thread_ext(d, pitch, length, hand, ends):
    return _iso_thread(major_diameter=d, pitch=pitch, length=length, external=True,
                       hand=hand, end_finishes=ends, interference=0.05, simple=False)

def _thread_int(d, pitch, length, hand, ends=("fade", "fade")):
    return IsoThread(major_diameter=d, pitch=pitch, length=length, external=False,
                     hand=hand, end_finishes=ends, simple=False)

def _hex_prism(s, h, z0=0.0, chamfer_bottom=True, chamfer_top=True):
    """Hex prism with 30deg corner chamfers (like nuts / hex heads)."""
    prism = extrude(Plane.XY.offset(z0) * RegularPolygon(s / 2, 6, major_radius=False), h)
    e = s / math.cos(math.radians(30))
    R = e / 2 + 0.01
    dw = 0.95 * s
    c = (R - dw / 2) * math.tan(math.radians(30))
    pts = [(0, z0)]
    pts += [(dw / 2, z0), (R, z0 + c)] if chamfer_bottom else [(R, z0)]
    pts += [(R, z0 + h - c), (dw / 2, z0 + h)] if chamfer_top else [(R, z0 + h)]
    pts += [(0, z0 + h)]
    prof = make_face(Polyline(*[(x, 0, z) for x, z in pts], close=True))
    cham = revolve(Plane.XZ * prof if False else prof, Axis.Z)
    return prism & cham

def _revolve_profile(pts):
    """pts: list of (r, z) closed polygon in XZ plane, revolved about Z."""
    face = make_face(Polyline(*[(r, 0, z) for r, z in pts], close=True))
    return revolve(face, Axis.Z)

# ---------------------------------------------------------------- drive recesses
def _drive_sketch(drive, size):
    """2D recess outline at origin. size = characteristic key size (mm)."""
    if drive.startswith("Hex socket"):
        return RegularPolygon(size / 2, 6, major_radius=False)
    if drive.startswith("Torx"):
        A = size
        B = 0.72 * A
        rl = 0.13 * A
        sk = Circle(B / 2)
        for k in range(6):
            a = math.radians(60 * k)
            rr = A / 2 - rl
            sk += Pos(rr * math.cos(a), rr * math.sin(a)) * Circle(rl)
        f = 0.07 * A
        try:
            sk = offset(offset(sk, f), -f)
        except Exception:
            pass
        return sk
    if drive.startswith("Triangle"):
        return RegularPolygon(size * 0.62, 3)
    if drive.startswith("Square"):
        return Rectangle(size * 0.75, size * 0.75)
    if drive.startswith("Pentagon"):
        return RegularPolygon(size * 0.6, 5)
    return None

def _cut_drive(head_top_z, solid, drive, d, dk, k, kind):
    """Cut recess into head top. kind: 'cyl','button','csk','pan','hex','none'."""
    if drive == "None":
        return solid
    big = kind == "cyl"
    ks = key_s(d) if big else max(key_s(d) * 0.8, 0.6)
    depth = {"cyl": 0.55 * k, "button": 0.6 * k, "csk": 0.6 * k, "rcsk": 0.6 * k,
             "pan": 0.5 * k, "hex": 0.4 * k, "none": 0.5 * d}[kind]
    depth = max(depth, 0.3)
    top = Plane.XY.offset(head_top_z)
    if drive.startswith("Slot"):
        n = max(0.3, 0.2 * d)
        sk = Rectangle(dk * 1.2, n)
        return solid - extrude(top * sk, -min(depth, 0.5 * k + 0.2 * d if kind != "none" else depth))
    if drive.startswith("Cross"):
        w = max(0.25, 0.16 * d)
        L = min(0.55 * dk, 1.2 * d)
        down = Plane(origin=(0, 0, head_top_z), x_dir=(1, 0, 0), z_dir=(0, 0, -1))
        rec = extrude(down * Rectangle(L, w), depth) + extrude(down * Rectangle(w, L), depth)
        cone = Solid.make_cone(L * 0.3, 0.02, depth, Plane.XY.offset(head_top_z).reverse() if False else Plane(origin=(0, 0, head_top_z), z_dir=(0, 0, -1)))
        return solid - rec - cone
    size = torx_a(d) * (1.0 if big else 0.85) if drive.startswith("Torx") else ks
    # keep the recess inside the head
    size = min(size, 0.62 * dk) if dk else size
    sk = _drive_sketch(drive, size)
    if sk is None:
        return solid
    rec = extrude(top * sk, -depth)
    # conical bottom like a drilled socket
    r_in = size * 0.45
    cone = Solid.make_cone(r_in, 0.01, r_in * 0.58,
                           Plane(origin=(0, 0, head_top_z - depth), z_dir=(0, 0, -1)))
    return solid - rec - cone

# ---------------------------------------------------------------- custom screw
def custom_head_dims(head, d):
    if head == "Socket cap (cylindrical)":
        dk = _interp(SOCKET_DK, d) if d <= 36 else 1.5 * d
        return dict(dk=dk, k=d)
    if head.startswith("Button"):
        dk = _interp(BUTTON_DK, d) if d <= 16 else 1.75 * d
        return dict(dk=dk, k=0.55 * d)
    if head.startswith("Countersunk") or head.startswith("Raised countersunk"):
        dk = _interp(CSK_DK, d) if d <= 24 else 1.7 * d
        return dict(dk=dk, k=(dk - d) / 2)
    if head == "Pan head":
        return dict(dk=1.9 * d, k=0.75 * d)
    if head == "Hex head":
        return dict(dk=hex_s(d), k=0.67 * d)
    if head == "Hex head with flange":
        return dict(dk=hex_s(d), k=0.67 * d, dc=2.2 * d, c=max(0.6, 0.12 * d))
    return dict(dk=0, k=0)

def make_custom_screw(d, pitch, length, head, drive, hand="right",
                      thread_length=0.0, dk=None, k=None, merge=True):
    """Custom screw. length: under-head length (countersunk: overall)."""
    dims = custom_head_dims(head, d)
    if dk: dims["dk"] = dk
    if k:  dims["k"] = k
    dk, k = dims["dk"], dims["k"]
    csk = head.startswith("Countersunk") or head.startswith("Raised countersunk")
    headless = head.startswith("Headless")
    # shank geometry (along -Z from z=0); countersunk head lives in [-k, 0]
    z_shank_top = -k if csk else 0.0
    L_shank = length - (k if csk else 0)
    if L_shank <= pitch * 2:
        raise ValueError(f"Length {length} mm is too short for this head")
    tl = L_shank if (thread_length <= 0 or thread_length >= L_shank) else thread_length
    z_tip = z_shank_top - L_shank
    plain = L_shank - tl

    parts = []
    # head
    if head == "Socket cap (cylindrical)":
        r = dk / 2; ch = min(0.08 * d, 0.5)
        h = _revolve_profile([(0, 0), (r, 0), (r, k - ch), (r - ch, k), (0, k)])
        kind = "cyl"; top = k
    elif head.startswith("Button"):
        r = dk / 2
        # dome: spherical cap through (r,0.15k) and apex (0,k)
        h0 = 0.12 * k
        a = r; b = k - h0
        R = (a * a + b * b) / (2 * b)
        n = 24
        pts = [(0, 0), (r, 0), (r, h0)]
        for i in range(1, n):
            x = r * (1 - i / n)
            z = h0 + (math.sqrt(max(R * R - x * x, 0)) - (R - b))
            pts.append((x, z))
        pts.append((0, k))
        h = _revolve_profile(pts)
        kind = "button"; top = k
    elif csk:
        raised = head.startswith("Raised")
        rr = dk / 2
        body = [(0, -k), (d / 2, -k), (rr, -0.02 * d), (rr, 0)]
        if raised:
            f = 0.2 * d
            body += [(rr * 0.7, f * 0.75), (rr * 0.35, f * 0.95), (0, f)]
        else:
            body += [(0, 0)]
        h = _revolve_profile(body)
        kind = "rcsk" if raised else "csk"; top = 0.2 * d if raised else 0.0
    elif head == "Pan head":
        r = dk / 2; f = 0.3 * k
        pts = [(0, 0), (r, 0), (r, k - f)]
        for i in range(1, 8):
            a = math.radians(90 * i / 8)
            pts.append((r - f + f * math.cos(a), k - f + f * math.sin(a)))
        pts.append((0, k))
        h = _revolve_profile(pts)
        kind = "pan"; top = k
    elif head.startswith("Hex head"):
        flange = "flange" in head
        z0 = dims.get("c", 0) if flange else 0
        h = _hex_prism(dk, k - z0, z0=z0, chamfer_bottom=not flange)
        if flange:
            rc = dims["dc"] / 2; c = dims["c"]
            h = h + _revolve_profile([(0, 0), (rc, 0), (rc, c * 0.6), (rc * 0.8, c * 1.3), (0, c * 1.3)])
        kind = "hex"; top = k
    else:  # headless set screw
        h = None
        kind = "none"; top = 0.0

    if h is not None:
        h = _cut_drive(top, h, drive, d, dk, k, kind)
        parts.append(h)

    # unthreaded shank
    if plain > 0:
        parts.append(Solid.make_cylinder(d / 2, plain + (0.01 if h is not None else 0),
                                         Plane.XY.offset(z_shank_top - plain)))
    # thread
    ends = ("chamfer", "fade" if plain > 0 else ("raw" if h is not None else "chamfer"))
    th = _thread_ext(d, pitch, tl, hand, ends)
    th = th.locate(Pos(0, 0, z_tip))
    core = Solid.make_cylinder(th.min_radius - CORE_GAP, tl, Plane.XY.offset(z_tip))
    # chamfer the core tip slightly
    parts.append(core)
    # 1) shaft = core + thread (hardest boolean, done alone)
    shaft = _fuse_all(Compound(children=[*parts[-1].solids(), *th.solids()]), merge)
    rest = parts[:-1]
    if headless:
        rest = []
    # 2) head + plain shank (simple solids)
    hb = None
    if rest:
        hb = rest[0]
        if len(rest) > 1:
            hb = hb.fuse(*rest[1:]).clean()
    shaft_sols = list(shaft.solids())
    if hb is not None and len(shaft_sols) == 1 and merge:
        res = _fuse_all(Compound(children=[*hb.solids(), shaft_sols[0]]), merge)
    elif hb is not None:
        res = Compound(children=[*hb.solids(), *shaft_sols])
    else:
        res = shaft
    if headless and drive != "None":
        if isinstance(res, Solid):
            res = _cut_drive(z_shank_top, res, drive, d, d, d, "none")
    return res

# ---------------------------------------------------------------- custom nuts
def make_custom_nut(d, pitch, kind, hand="right", length=None, drive="Hex socket (Allen)",
                    merge=True):
    s = hex_s(d)
    if kind.startswith("Hex nut"):
        m = nut_m(d)
        return _tap(_hex_prism(s, m).solids()[0], d, pitch, 0, m, hand)
    if kind.startswith("Thin"):
        m = round(max(0.5 * d, 0.6), 2)
        return _tap(_hex_prism(s, m).solids()[0], d, pitch, 0, m, hand)
    if kind.startswith("Coupling"):
        m = length or 3 * d
        return _tap(_hex_prism(s, m).solids()[0], d, pitch, 0, m, hand)
    if kind.startswith("Nylon"):
        mh = nut_m(d) * 0.9                       # hex (threaded) part
        htot = max(1.3 * d, mh + 1.0)             # overall height
        ch = htot - mh                            # collar height
        rc = 0.92 * s / 2                         # collar radius
        f = min(0.35 * ch, 0.25 * s)
        collar_pts = [(d / 2 + 0.05, mh - 0.05), (rc, mh - 0.05), (rc, htot - f)]
        for i in range(1, 7):
            a = math.radians(90 * i / 6)
            collar_pts.append((rc - f + f * math.cos(a), htot - f + f * math.sin(a)))
        lip_r = d / 2 + 0.06 * s
        collar_pts += [(lip_r, htot), (lip_r, htot - 0.25 * ch)]
        ring_ro = 0.40 * s
        collar_pts += [(ring_ro, htot - 0.25 * ch), (ring_ro, mh + 0.15 * ch), (d / 2 + 0.05, mh + 0.15 * ch)]
        collar = _revolve_profile(collar_pts)
        hexp = _hex_prism(s, mh, chamfer_top=False).solids()[0]
        hexp = _tap(hexp, d, pitch, 0, mh, hand, chamfer=False)
        steel = _fuse_all(Compound(children=[*hexp.solids(), *collar.solids()]), merge)
        # nylon ring: inner dia slightly under the minor diameter -> visible locking ring
        minor = d - 1.0825 * pitch
        nylon = _revolve_profile([(minor / 2 * 0.98, mh + 0.15 * ch), (ring_ro - 0.01, mh + 0.15 * ch),
                                  (ring_ro - 0.01, htot - 0.25 * ch), (minor / 2 * 0.98, htot - 0.25 * ch)])
        nylon.label = "nylon_insert"
        out = Compound(children=[*steel.solids(), *nylon.solids()])
        return out
    if kind.startswith("Sleeve"):
        csk = "countersunk" in kind
        od = max(d + 2.0, 1.25 * d)
        dk = 1.7 * od
        hk = (dk - od) / 2 if csk else max(1.0, 0.25 * d)
        L = length or max(3 * d, 10)
        # sleeve down from z=0 (head bearing face), head above (flat) or cone (csk)
        if csk:
            head = _revolve_profile([(0, -hk), (od / 2, -hk), (dk / 2, -0.02), (dk / 2, 0), (0, 0)])
            top = 0.0; z_sleeve_top = -hk; Ls = L - hk
        else:
            r = dk / 2; f = min(0.3 * hk, 0.6)
            head = _revolve_profile([(0, 0), (r, 0), (r, hk - f), (r - f, hk), (0, hk)])
            top = hk; z_sleeve_top = 0.0; Ls = L
        head = _cut_drive(top, head, drive, d * 0.8, dk, hk if not csk else hk, "csk" if csk else "pan")
        sleeve = Solid.make_cylinder(od / 2, Ls + 0.01, Plane.XY.offset(z_sleeve_top - Ls))
        body = head.fuse(sleeve).clean().solids()[0]
        thl = Ls * 0.85
        body = _tap(body, d, pitch, z_sleeve_top - Ls, thl, hand)
        # relief bore above the thread (to the drive recess)
        return body - Solid.make_cylinder(d / 2, Ls - thl + 0.01, Plane.XY.offset(z_sleeve_top - Ls + thl))
    raise ValueError(kind)

# ---------------------------------------------------------------- rod, washers
def make_threaded_rod(d, pitch, length, hand="right", merge=True):
    th = _thread_ext(d, pitch, length, hand, ("chamfer", "chamfer"))
    core = Solid.make_cylinder(th.min_radius - CORE_GAP, length)
    return _fuse_all(Compound(children=[core, *th.solids()]), merge)

def washer_dims(d):
    d1 = d + (0.2 if d <= 2 else 0.4 if d <= 10 else 1.0 if d <= 24 else 2.0)
    d2 = 2.0 * d if d <= 12 else 1.85 * d
    h = min(max(0.3, round(0.17 * d, 1)), 0.12 * d + 1)
    return d1, d2, h

def make_custom_washer(d, kind):
    if kind.startswith("Flat"):
        d1, d2, h = washer_dims(d)
        return Solid.make_cylinder(d2 / 2, h) - Solid.make_cylinder(d1 / 2, h)
    # DIN 127 split lock washer, real helical twist (one turn, pitch = thickness)
    d1 = d + (0.1 if d <= 10 else 0.2 if d <= 24 else 0.5)
    b = 0.27 * d + 1.2
    t = max(0.4, 0.2 * d + 0.3)
    rm = d1 / 2 + b / 2
    gap_deg = 12
    turn = 360 - gap_deg
    rise = t * 0.9
    path = Helix(pitch=rise * 360 / turn, height=rise, radius=rm)
    # take only 'turn' degrees of the helix: build from height=rise (=turn deg)
    prof = Plane(origin=path @ 0, x_dir=(1, 0, 0), z_dir=path % 0) * Rectangle(b, t)
    try:
        w = sweep(prof, path, is_frenet=True)
        sol = w.solids()[0] if hasattr(w, "solids") else w
        if sol.is_valid:
            return sol.locate(Pos(0, 0, t / 2))
    except Exception:
        pass
    ring = Solid.make_cylinder(d1 / 2 + b, t) - Solid.make_cylinder(d1 / 2, t)
    return ring - extrude(Plane.XY * Pos(rm, 0) * Rectangle(b * 2, rm * math.radians(gap_deg)), t)

# ---------------------------------------------------------------- standard
def _thread_min_r(solids):
    import math as _m
    return min(_m.hypot(v.X, v.Y) for sh in solids for v in sh.vertices())

def make_std_screw(cls, ftype, size, length, hand="right", merge=True):
    obj = cls(size, length, ftype, hand=hand, simple=False)
    body = [c for c in obj.children if c.label == "body"]
    thr = [c for c in obj.children if c.label == "thread"]
    if not merge or not body or not thr:
        return _fuse_all(obj, merge)
    body = body[0].solids()[0]
    # rebuild the thread ourselves (lower interference -> robust booleans)
    lo = obj.length_offset()
    base = -lo - obj.grip_length - obj.thread_offset
    tl = obj.thread_length
    tip = base - tl
    ends = ("fade", "fade" if obj.thread_offset > 0 else "raw")
    th = _thread_ext(obj.thread_diameter, obj.thread_pitch, tl, hand, ends).locate(Pos(0, 0, tip))
    tsol = list(th.solids())
    rmin = th.min_radius
    z0, z1 = tip, base
    for gap in (CORE_GAP,):
        try:
            nb = body.cut(Solid.make_cylinder(rmin + 0.25, z1 - z0, Plane.XY.offset(z0)))
            nb = nb.fuse(Solid.make_cylinder(rmin - gap, z1 - z0 + 0.01, Plane.XY.offset(z0))).clean()
            if len(nb.solids()) != 1:
                continue
            r = _fuse_all(Compound(children=[nb.solids()[0], *tsol]), merge)
            if isinstance(r, Solid):
                return r
        except Exception:
            pass
    return _fuse_all(Compound(children=[body, *tsol]), True)

def make_std_nut(cls, ftype, size, hand="right", merge=True):
    obj = cls(size, ftype, hand=hand, simple=True)
    d, p = obj.thread_diameter, obj.thread_pitch
    m = float(obj.nut_data.get("m", obj.nut_thickness))
    body = obj.solids()[0] if len(obj.solids()) == 1 else obj.solids()[0].fuse(*obj.solids()[1:])
    body = body.fuse(Solid.make_cylinder(d / 2 + 0.001, m)).clean().solids()[0]
    blind = cls in (F.DomedCapNut,)
    return _tap(body, d, p, 0, m, hand, chamfer=not blind and cls is not F.HeatSetNut)

def make_std_washer(cls, ftype, size):
    return _to_solid_or_compound(cls(size, ftype))

# ---------------------------------------------------------------- kit
def make_kit(screw_shape, nut_shape, washer_shape, grip, washer_under_head, washer_under_nut):
    """Screw head bearing face at Z=0; clamped stack of thickness `grip` below."""
    items = [("bolt", screw_shape)]
    z = 0.0
    wt = 0.0
    if washer_shape is not None:
        bb = washer_shape.bounding_box(); wt = bb.max.Z - bb.min.Z
    if washer_under_head and washer_shape is not None:
        items.append(("washer_head", washer_shape.moved(Location((0, 0, -wt)))))
        z -= wt
    z -= grip
    if washer_under_nut and washer_shape is not None:
        items.append(("washer_nut", washer_shape.moved(Location((0, 0, z - wt)))))
        z -= wt
    if nut_shape is not None:
        nb = nut_shape.bounding_box()
        flipped = nut_shape.moved(Location((0, 0, 0), (1, 0, 0), 180))
        fb = flipped.bounding_box()
        items.append(("nut", flipped.moved(Location((0, 0, z - fb.max.Z)))))
    return items

# ---------------------------------------------------------------- export
def export(shape_or_items, path_step, also_stl=False):
    if isinstance(shape_or_items, list):
        children = []
        for name, shp in shape_or_items:
            for i, s in enumerate(shp.solids()):
                s.label = name if len(shp.solids()) == 1 else f"{name}_{i+1}"
                children.append(s)
        shape = Compound(children=children)
    else:
        shape = shape_or_items
    export_step(shape, path_step)
    if also_stl:
        export_stl(shape, os.path.splitext(path_step)[0] + ".stl", tolerance=0.01,
                   angular_tolerance=0.2)
    return path_step

def parse_size(size):
    m = re.match(r"M([\d.]+)-([\d.]+)", size)
    return (float(m.group(1)), float(m.group(2))) if m else (None, None)
