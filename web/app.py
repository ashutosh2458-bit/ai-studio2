"""Site Designer engine (Python in the browser via Pyodide/WebAssembly).
The editor (index.html) owns the canvas; this module turns a design `doc` into clean HTML/CSS/JS,
inserts ready-made sections, and runs the small rule-based assistant."""
import html as H, json, random, re

FONTS = {"sans": "system-ui,-apple-system,'Segoe UI',sans-serif", "serif": "Georgia,'Times New Roman',serif",
         "rounded": "'Trebuchet MS','Segoe UI',sans-serif", "mono": "ui-monospace,Menlo,monospace"}
BASE = dict(type="rect", name="", x=0, y=0, w=200, h=100, fill="", color="#18202b", stroke="#000000", sw=0, r=0,
            op=100, fs=16, fw=400, ta="left", text="", href="", src="", shadow=False)
COLORS = {"red": "#e5383b", "orange": "#f77f00", "yellow": "#e9b800", "green": "#2b9348", "teal": "#0f9d94",
          "blue": "#2a6fdb", "indigo": "#4a3fd1", "purple": "#8a3ffc", "pink": "#e0408f", "black": "#1b1f24",
          "gray": "#5b6b7a", "white": "#ffffff"}


def E(type, x, y, w, h, name, **kw):
    return {**BASE, "type": type, "x": x, "y": y, "w": w, "h": h, "name": name, "id": "e" + format(random.getrandbits(30), "x"), **kw}


def tint(c, a=.9):
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(round(v + (255 - v) * a) for v in (r, g, b))


# ------------------------------------------------------------ ready-made sections (designed on a 1280px grid)
def build(name, ac):
    T = lambda x, y, w, h, n, t, **k: E("text", x, y, w, h, n, text=t, **k)
    if name == "navbar":
        return [E("rect", 0, 0, 1280, 72, "Navbar", fill="#ffffff", shadow=True), T(64, 20, 200, 32, "Brand", "Brandname", fs=22, fw=800),
                *[T(560 + i * 110, 24, 100, 28, f"Link {i + 1}", t) for i, t in enumerate(("Product", "Pricing", "About"))],
                E("button", 1056, 12, 160, 48, "Sign up", text="Sign up", fill=ac, color="#ffffff", r=10, fw=600, ta="center")]
    if name == "hero":
        return [E("rect", 0, 0, 1280, 560, "Hero background", fill=tint(ac)),
                T(64, 120, 560, 150, "Hero title", "Build something people remember", fs=56, fw=800),
                T(64, 290, 520, 80, "Hero text", "A short line that explains what you do and who it is for.", fs=18, color="#5b6b7a"),
                E("button", 64, 390, 180, 52, "Primary button", text="Get started", fill=ac, color="#ffffff", r=10, fw=600, ta="center"),
                E("button", 260, 390, 180, 52, "Secondary button", text="Learn more", stroke=ac, sw=2, color=ac, r=10, fw=600, ta="center"),
                E("image", 700, 90, 520, 380, "Hero image", r=20)]
    if name in ("features", "pricing"):
        o = [T(64, 60, 600, 50, "Section title", "What you get" if name == "features" else "Pricing", fs=36, fw=800)]
        for i in range(3):
            x = 64 + i * 400
            if name == "features":
                o += [E("rect", x, 150, 368, 240, f"Card {i + 1}", fill="#f5f7f8", stroke="#e1e7ec", sw=1, r=16),
                      E("ellipse", x + 28, 178, 48, 48, f"Icon {i + 1}", fill=ac), T(x + 28, 250, 300, 32, f"Title {i + 1}", f"Feature {i + 1}", fs=22, fw=700),
                      T(x + 28, 294, 310, 60, f"Text {i + 1}", "One or two sentences about the benefit.", color="#5b6b7a")]
            else:
                o += [E("rect", x, 150, 368, 330, f"Plan {i + 1}", fill="#ffffff", stroke=ac if i == 1 else "#e1e7ec", sw=2 if i == 1 else 1, r=16, shadow=i == 1),
                      T(x + 28, 178, 300, 28, f"Plan name {i + 1}", ("Starter", "Pro", "Team")[i], fs=20, fw=700),
                      T(x + 28, 216, 300, 56, f"Price {i + 1}", ("$9", "$29", "$79")[i], fs=44, fw=800),
                      T(x + 28, 290, 300, 80, f"Perks {i + 1}", "Feature one\nFeature two\nFeature three", color="#5b6b7a"),
                      E("button", x + 28, 400, 312, 48, f"Choose {i + 1}", text="Choose plan", fill=ac, color="#ffffff", r=10, fw=600, ta="center")]
        return o
    if name == "cta":
        return [E("rect", 64, 40, 1152, 200, "CTA panel", fill=ac, r=24),
                T(112, 80, 700, 50, "CTA title", "Ready to start?", fs=34, fw=800, color="#ffffff"),
                E("button", 112, 150, 200, 52, "CTA button", text="Create your account", fill="#ffffff", color=ac, r=10, fw=600, ta="center")]
    return [E("rect", 0, 0, 1280, 120, "Footer", fill="#18202b"), T(64, 46, 600, 28, "Footer text", "© Brandname. All rights reserved.", fs=15, color="#eef1f6")]


def place(name, doc):
    p = doc["page"]; f = p["w"] / 1280
    y0 = max([e["y"] + e["h"] for e in doc["els"]], default=0)
    new = build(name, p.get("accent", "#2a44e8"))
    for e in new:
        e["x"], e["w"], e["y"] = round(e["x"] * f), round(e["w"] * f), e["y"] + y0
        if f < 1: e["fs"] = max(13, round(e["fs"] * max(f, .55)))
    doc["els"] += new
    return new


# ------------------------------------------------------------ export
def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "el"
    return "e-" + s if s[0].isdigit() else s


def contains(a, b):
    return (a is not b and a["x"] <= b["x"] + 1 and a["y"] <= b["y"] + 1 and
            a["x"] + a["w"] >= b["x"] + b["w"] - 1 and a["y"] + a["h"] >= b["y"] + b["h"] - 1)


def style(e, kids=False):
    t, s = e["type"], []
    if t == "image":
        s.append("object-fit:cover;display:block" if e["src"] and not kids else
                 "background:url('%s') center/cover" % e["src"].replace("'", "%27") if e["src"] else
                 "background:linear-gradient(135deg,#cfd8e0,#aab8c4)")
    elif e["fill"]:
        s.append("background:" + e["fill"])
    if t == "ellipse": s.append("border-radius:50%")
    elif e["r"]: s.append(f"border-radius:{e['r']}px")
    if e["sw"]: s.append(f"border:{e['sw']}px solid {e['stroke']}")
    if e["op"] < 100: s.append("opacity:%g" % (e["op"] / 100))
    if e["shadow"]: s.append("box-shadow:0 8px 24px rgba(0,0,0,.18)")
    if t in ("text", "button", "input"):
        s.append(f"color:{e['color']};font-size:{e['fs']}px;font-weight:{e['fw']};text-align:{e['ta']};white-space:pre-wrap")
    if t == "text": s.append("display:block")
    if t == "input": s.append("padding:0 14px")
    if t == "button":
        s.append("display:flex;align-items:center;justify-content:" + {"left": "flex-start", "center": "center", "right": "flex-end"}[e["ta"]] + ";text-decoration:none;cursor:pointer")
    return ";".join(s)


def export(doc, mode="auto", js=False, linked=False):
    p = doc["page"]; W = p["w"]
    els = [dict(e) for e in doc["els"] if not e.get("hidden")]
    used = {}
    for e in els:
        b = slug(e["name"] or e["type"]); n = used.get(b, 0); used[b] = n + 1
        e["_c"] = b if n == 0 else f"{b}-{n + 1}"
    kids, top = {e["id"]: [] for e in els}, []
    for i, e in enumerate(els):
        cands = [q for q in els[:i] if q["type"] in ("rect", "ellipse", "image") and contains(q, e)]
        (kids[min(cands, key=lambda q: q["w"] * q["h"])["id"]] if cands else top).append(e)
    bottom = max([e["y"] + e["h"] for e in els], default=0) + 40
    anim = bool(js and p.get("anim"))
    rules, st = [], {"h1": False}

    def tag(e, c, inner, is_top):
        t, esc = e["type"], H.escape
        a = f'class="{c}" id="{c}"' + (" data-reveal" if anim and is_top else "")
        if t == "text":
            tg = "p"
            if e["fs"] >= 36: tg, st["h1"] = ("h2" if st["h1"] else "h1"), True
            elif e["fs"] >= 26: tg = "h2"
            elif e["fs"] >= 20: tg = "h3"
            return f'<a {a} href="{esc(e["href"])}">{esc(e["text"])}</a>' if e["href"] else f"<{tg} {a}>{esc(e['text'])}</{tg}>"
        if t == "button":
            return f'<a {a} href="{esc(e["href"])}">{esc(e["text"])}</a>' if e["href"] else f'<button {a} type="button">{esc(e["text"])}</button>'
        if t == "input": return f'<input {a} type="text" placeholder="{esc(e["text"])}" aria-label="{esc(e["text"])}">'
        if t == "image" and e["src"] and not inner: return f'<img {a} src="{esc(e["src"])}" alt="{esc(e["name"])}">'
        return f"<div {a}>{inner}</div>"

    def node(e, par, extra=""):
        ks = kids[e["id"]]
        if par:
            pos = "position:absolute;left:%.3f%%;top:%gpx;width:%.3f%%;height:%gpx" % ((e["x"] - par["x"]) / par["w"] * 100, e["y"] - par["y"], e["w"] / par["w"] * 100, e["h"])
        elif mode == "abs":
            pos = "position:absolute;left:%.3f%%;top:%gpx;width:%.3f%%;height:%gpx" % (e["x"] / W * 100, e["y"], e["w"] / W * 100, e["h"])
        else:
            pos = "width:%gpx;max-width:100%%;%s:%gpx;flex:0 1 auto%s%s" % (e["w"], "height" if ks else "min-height", e["h"], ";position:relative" if ks else "", extra)
        rules.append(f".{e['_c']}{{{pos};{style(e, bool(ks))}}}")
        return tag(e, e["_c"], "".join(node(k, e) for k in ks), par is None)

    if mode == "abs":
        body, wrap = "".join(node(e, None) for e in sorted(top, key=lambda z: (z["y"], z["x"]))), f"height:{bottom:g}px;"
    else:
        rows = []
        for e in sorted(top, key=lambda z: (z["y"], z["x"])):
            r = rows[-1] if rows else None
            if r and min(e["y"] + e["h"], r["bot"]) - max(e["y"], r["top"]) >= .4 * min(e["h"], r["bot"] - r["top"]):
                r["els"].append(e); r["bot"] = max(r["bot"], e["y"] + e["h"])
            else:
                rows.append(dict(els=[e], top=e["y"], bot=e["y"] + e["h"]))
        body, prev, wrap = "", 0, ""
        for i, r in enumerate(rows, 1):
            rules.append(f".r{i}{{margin-top:{max(0, r['top'] - prev):g}px}}")
            items, right = "", 0
            for e in sorted(r["els"], key=lambda z: z["x"]):
                items += node(e, None, f";margin-left:{max(0, e['x'] - right):g}px;margin-top:{max(0, e['y'] - r['top']):g}px")
                right = e["x"] + e["w"]
            body += f'<div class="row r{i}">{items}</div>\n'; prev = r["bot"]

    css = (f"*{{box-sizing:border-box}}\nhtml{{scroll-behavior:smooth}}\n"
           f"body{{margin:0;background:{p['bg']};color:#18202b;font-family:{FONTS[p['font']]};line-height:1.3}}\n"
           "h1,h2,h3,p{margin:0;font-weight:inherit}\nbutton,input{font-family:inherit;border:0;margin:0}\n"
           f".page{{max-width:{W}px;margin:0 auto;position:relative;{wrap}}}\n")
    if mode != "abs":
        css += ".row{display:flex;align-items:flex-start}\n"
    css += "\n".join(rules) + "\n"
    if mode != "abs":
        css += "@media(max-width:720px){.row{flex-direction:column;align-items:stretch}.row>*{width:100%!important;margin:0 0 12px!important}}\n"
    if anim:
        css += ".hide{opacity:0;transform:translateY(16px);transition:opacity .5s,transform .5s}.hide.in{opacity:1;transform:none}\n"
    script = JS if anim else "// Nothing to run yet. Turn on \"Animate on scroll\" in Page settings to add scroll animations.\n"
    head = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{H.escape(p["title"])}</title>\n' + ('<link rel="stylesheet" href="style.css">\n' if linked else f"<style>\n{css}</style>\n") + "</head>\n<body>\n")
    tail = ('<script src="script.js"></script>\n' if linked else f"<script>\n{script}</script>\n") if anim else ""
    return {"html": head + f'<main class="page">\n{body}</main>\n' + tail + "</body>\n</html>\n", "css": css, "js": script}


JS = """// Fade elements in as they scroll into view. (Smooth scrolling for #links is done in CSS.)
const items = document.querySelectorAll('[data-reveal]');
if ('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  }), { threshold: 0.1 });
  items.forEach(el => { el.classList.add('hide'); io.observe(el); });
}
"""


# ------------------------------------------------------------ assistant
ALIAS = {"navbar": r"nav|navbar|navigation|menu", "hero": r"hero|banner", "features": r"features?|benefits",
         "pricing": r"pricing|plans|prices?", "cta": r"cta|call to action|signup", "footer": r"footer"}
SINGLE = {r"button": ("button", dict(text="Button", fill="#2a44e8", color="#ffffff", r=10, fw=600, ta="center", w=160, h=48)),
          r"heading|text|paragraph": ("text", dict(text="Heading", fs=28, fw=700, w=300, h=44)),
          r"image|photo|picture": ("image", dict(r=8, w=300, h=200)), r"input|field|email": ("input", dict(text="Email address", fill="#ffffff", stroke="#b9c5ce", sw=1, r=8, color="#5b6b7a", w=280, h=44)),
          r"card|box|rectangle": ("rect", dict(fill="#e6ebef", r=12, w=240, h=140)), r"circle|ellipse": ("ellipse", dict(fill="#f0a92e", w=140, h=140))}
HELP = ("I can edit the design from plain English. Try:\n• add a navbar / hero / features / pricing / cta / footer\n• add a button\n"
        "• make it blue (recolors your accent, or the selected element)\n• make it dark / light\n• center it, make it bigger, rounded, add shadow\n"
        "• mobile / tablet / desktop\n• delete it, clear everything")


def chat(text, doc, sel):
    low, p, done, new = text.lower(), doc["page"], [], []
    chosen = [e for e in doc["els"] if e["id"] in sel]
    W = p["w"]
    if re.search(r"\b(clear|start over|delete everything|remove everything)\b", low):
        doc["els"] = []; chosen = []; done.append("Cleared the canvas.")
    elif re.search(r"\b(delete|remove)\b", low) and chosen:
        doc["els"] = [e for e in doc["els"] if e not in chosen]; done.append(f"Deleted {len(chosen)} element(s)."); chosen = []
    if re.search(r"\b(add|insert|create|build|put|need|want)\b", low):
        for name, pat in ALIAS.items():
            if re.search(r"\b(%s)\b" % pat, low): new += place(name, doc); done.append(f"Added a {name} section.")
        if not new:
            for pat, (t, kw) in SINGLE.items():
                if re.search(r"\b(%s)\b" % pat, low):
                    kw = dict(kw); w, h = kw.pop("w"), kw.pop("h"); e = E(t, 0, 0, w, h, t.title(), **kw)
                    e["x"], e["y"] = round((W - e["w"]) / 2), max([q["y"] + q["h"] for q in doc["els"]], default=0) + 24
                    doc["els"].append(e); new.append(e); done.append(f"Added a {t}."); break
    for w, hx in COLORS.items():
        if re.search(r"\b%s\b" % w, low):
            if chosen:
                for e in chosen: e["color" if e["type"] == "text" else "fill"] = hx
                done.append(f"Colored the selection {w}.")
            elif "background" in low: p["bg"] = hx; done.append(f"Set the page background to {w}.")
            else:
                old = p.get("accent")
                for e in doc["els"]:
                    for k in ("fill", "stroke", "color"):
                        if e[k] == old: e[k] = hx
                p["accent"] = hx; done.append(f"Changed the accent color to {w}.")
            break
    if re.search(r"\bdark\b", low) or re.search(r"\blight\b", low):
        d = "dark" in low
        sw = {"#ffffff": "#1b2430", "#f5f7f8": "#1b2430", "#18202b": "#eef1f6", "#5b6b7a": "#9fb0c0"} if d else {"#1b2430": "#ffffff", "#eef1f6": "#18202b", "#9fb0c0": "#5b6b7a"}
        for e in doc["els"]:
            for k in ("fill", "color", "stroke"): e[k] = sw.get(e[k], e[k])
        p["bg"] = "#10131a" if d else "#ffffff"; done.append("Switched to a dark theme." if d else "Switched to a light theme.")
    for e in chosen:
        if re.search(r"\bcenter", low): e["x"] = round((W - e["w"]) / 2)
        elif re.search(r"\balign left\b", low): e["x"] = 64
        elif re.search(r"\balign right\b", low): e["x"] = W - 64 - e["w"]
        if re.search(r"\b(bigger|larger|grow)\b", low): k = 1.2
        elif re.search(r"\b(smaller|shrink)\b", low): k = .8
        else: k = 1
        e["w"], e["h"], e["fs"] = round(e["w"] * k), round(e["h"] * k), round(e["fs"] * k)
        if re.search(r"\bround", low): e["r"] = 16
        if re.search(r"\b(sharp|square)\b", low): e["r"] = 0
        if "shadow" in low: e["shadow"] = True
    if chosen and re.search(r"\b(center|align|bigger|larger|grow|smaller|shrink|round|sharp|square|shadow)", low): done.append("Updated the selection.")
    m = re.search(r"\b(mobile|phone|tablet|desktop)\b", low)
    if m:
        nw = {"mobile": 390, "phone": 390, "tablet": 768, "desktop": 1280}[m.group(1)]
        for e in doc["els"]: e["x"], e["w"] = round(e["x"] * nw / W), round(e["w"] * nw / W)
        p["w"] = nw; done.append(f"Resized the page to {nw}px wide.")
    m = re.search(r"(?:title|brand|site name) (?:is|to) ([\w &'-]{1,30})", text, re.I)
    if m: p["title"] = m.group(1).strip(); done.append(f"Set the page title to {p['title']}.")
    reply = "Done:\n" + "\n".join("• " + d for d in done) if done else ("I couldn't find a change in that.\n" + HELP)
    return {"reply": reply, "doc": doc, "sel": [e["id"] for e in new] or sel}


# ------------------------------------------------------------ real AI (the browser calls the model with the visitor's own API key)
AI_SYSTEM = """You are a senior web designer editing a Figma-like canvas. Reply with ONE JSON object only (no markdown, no prose outside it):
{"reply": "one short sentence", "ops": [ ... ]}
Ops: {"op":"add","el":{...}} | {"op":"update","id":"<id>","set":{...}} | {"op":"delete","id":"<id>"} | {"op":"page","set":{"title","bg","accent","font"}} | {"op":"clear"}
Element types: rect, ellipse, text, button, image, input.
Fields: x,y,w,h (px; origin top-left of the page; page width is page.w), fill ('#rrggbb' or '' for none), color (text color), stroke, sw (border width),
r (corner radius), op (opacity 0-100), fs (font px), fw (400-800), ta (left|center|right), text, name, href (URL or '#layer-name'), src (https image URL, or '' for a placeholder), shadow (true/false).
Rules:
- Elements are drawn in array order (later = on top). Put text, buttons and icons fully INSIDE the rectangle they sit on so the exporter nests them as cards.
- Full-width sections use x=0 and w=page.w, stacked top to bottom with no gaps; inner content keeps about 64px side margins and stays within page.w.
- Text boxes must be tall enough for their text (line height 1.3, about 0.55 x font size per character of width).
- Use a consistent palette built from page.accent, strong text contrast, an 8px spacing grid, and real copy (no lorem ipsum).
- Give every element a unique, descriptive name.
- When editing, change as little as possible. 'it', 'this' and 'selected' mean the ids in "selected". To build a whole page, use many add ops in top-to-bottom order.
- Do not change the page width."""


def hexc(v, d):
    v = str(v or "").strip()
    if re.fullmatch(r"#[0-9a-fA-F]{3}", v): v = "#" + "".join(c * 2 for c in v[1:])
    return v.lower() if re.fullmatch(r"#[0-9a-fA-F]{6}", v) else d


def num(v, lo, hi, d):
    try: return max(lo, min(hi, round(float(v))))
    except (TypeError, ValueError): return d


def clean_el(d, W):
    """Never trust model output: coerce every field to a safe value."""
    e = dict(BASE)
    e["id"] = d.get("id") or "e" + format(random.getrandbits(30), "x")
    e["type"] = d.get("type") if d.get("type") in ("rect", "ellipse", "text", "button", "image", "input") else "rect"
    for k, lo, hi in (("x", -50, W), ("y", 0, 20000), ("w", 8, W), ("h", 8, 4000), ("r", 0, 999), ("sw", 0, 40), ("op", 0, 100), ("fs", 6, 200)):
        e[k] = num(d.get(k), lo, hi, BASE[k])
    e["fw"] = num(d.get("fw"), 400, 800, 400) // 100 * 100
    e["fill"], e["color"], e["stroke"] = hexc(d.get("fill"), ""), hexc(d.get("color"), BASE["color"]), hexc(d.get("stroke"), BASE["stroke"])
    e["ta"] = d.get("ta") if d.get("ta") in ("left", "center", "right") else "left"
    for k in ("text", "name", "href"): e[k] = str(d.get(k) or "")[:600]
    src = str(d.get("src") or "")
    e["src"] = src if re.match(r"(https?://|data:image/)", src) else ""
    e["shadow"] = bool(d.get("shadow"))
    return e


def apply_ops(doc, ops):
    W, els, p, new = doc["page"]["w"], doc["els"], doc["page"], []
    for o in ops if isinstance(ops, list) else []:
        if not isinstance(o, dict): continue
        k = o.get("op")
        if k == "clear": els.clear()
        elif k == "add" and isinstance(o.get("el"), dict):
            e = clean_el({**o["el"], "id": None}, W); els.append(e); new.append(e["id"])
        elif k == "update" and isinstance(o.get("set"), dict):
            for i, e in enumerate(els):
                if e["id"] == o.get("id"):
                    n = clean_el({**e, **o["set"]}, W); n["id"] = e["id"]; els[i] = n
        elif k == "delete": els[:] = [e for e in els if e["id"] != o.get("id")]
        elif k == "page" and isinstance(o.get("set"), dict):
            s = o["set"]
            if "title" in s: p["title"] = str(s["title"])[:60]
            if "bg" in s: p["bg"] = hexc(s["bg"], p["bg"])
            if "accent" in s: p["accent"] = hexc(s["accent"], p["accent"])
            if s.get("font") in FONTS: p["font"] = s["font"]
    return new


def ai_request(doc, sel, text):
    keep = lambda e: {k: v for k, v in e.items() if k in ("id", "type", "name", "x", "y", "w", "h") or v != BASE.get(k)}
    ctx = {"page": doc["page"], "selected": sel, "elements": [keep(e) for e in doc["els"]]}
    return {"system": AI_SYSTEM, "user": "Current design:\n" + json.dumps(ctx, separators=(",", ":")) + "\n\nRequest: " + text}


def ai_apply(doc, sel, text):
    try:
        data = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
        assert isinstance(data, dict)
    except (AttributeError, ValueError, AssertionError):
        return {"reply": "I couldn't read the AI's answer. Try a shorter or clearer request.", "doc": doc, "sel": sel, "fit": False}
    new = apply_ops(doc, data.get("ops"))
    ids = {e["id"] for e in doc["els"]}
    return {"reply": str(data.get("reply") or "Done.")[:400], "doc": doc, "sel": [i for i in (new or sel) if i in ids], "fit": len(new) >= 5}


def api(raw):
    m = json.loads(raw); c = m["cmd"]
    if c == "export": return json.dumps(export(m["doc"], m.get("mode", "auto"), m.get("js", False), m.get("linked", False)))
    if c == "preset":
        new = place(m["name"], m["doc"]); return json.dumps({"doc": m["doc"], "sel": [e["id"] for e in new]})
    if c == "ai_request": return json.dumps(ai_request(m["doc"], m.get("sel", []), m["text"]))
    if c == "ai_apply": return json.dumps(ai_apply(m["doc"], m.get("sel", []), m["text"]))
    return json.dumps(chat(m["text"], m["doc"], m.get("sel", [])))
