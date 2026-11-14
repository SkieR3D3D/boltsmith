# -*- coding: utf-8 -*-
"""Spec -> shape builder shared by the Boltsmith GUI-less tools (no tkinter)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
C = None


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


