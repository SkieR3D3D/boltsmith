# -*- coding: utf-8 -*-
"""Boltsmith CLI bridge (used by the Blender add-on).
Usage: python boltsmith_cli.py spec.json out_dir
Prints one JSON line: {"ok": true, "name": ..., "parts": [{"name":..., "stl":...}], "step": ...}
"""
import json, os, re, sys, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    import fastener_build as B
    from build123d import export_stl
    C = B.load_core()
    shp, name = B.build(spec)
    name = re.sub(r"[^\w.\-]+", "_", name)
    tol = float(spec.get("tol", 0.02))
    ang = float(spec.get("ang", 0.2))
    parts = []
    items = shp if isinstance(shp, list) else [(name, shp)]
    for pname, s in items:
        path = os.path.join(out, f"{name}__{pname}.stl" if len(items) > 1 else f"{name}.stl")
        export_stl(s, path, tolerance=tol, angular_tolerance=ang)
        parts.append({"name": pname if len(items) > 1 else name, "stl": path,
                      "bodies": len(s.solids())})
    step = None
    if spec.get("step_dir"):
        os.makedirs(spec["step_dir"], exist_ok=True)
        step = os.path.join(spec["step_dir"], name + ".step")
        C.export(shp, step)
    print("BOLTSMITH_RESULT " + json.dumps({"ok": True, "name": name, "parts": parts, "step": step}))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        print("BOLTSMITH_RESULT " + json.dumps({"ok": False, "error": str(e) or e.__class__.__name__}))
        sys.exit(1)
