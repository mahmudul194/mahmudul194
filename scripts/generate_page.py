#!/usr/bin/env python3
"""Render the whole profile page as one continuous SVG (desktop + mobile).

Usage:
  GH_TOKEN=... python scripts/generate_page.py <github-username>     # live data
  python scripts/generate_page.py --seed seed.json                   # offline, from a JSON file

Outputs: page-top, page-mobile-top and the connect-* slices in assets/
"""
import json, math, os, random, sys, textwrap, urllib.request
from datetime import datetime, timezone
from html import escape as esc

SANS = "'Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"
PAL = ["#22d3ee", "#818cf8", "#c084fc", "#f472b6", "#fbbf24", "#34d399"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
NB = "&#160;"

# ------------------------------------------------------------------ content
ABOUT = ("I'm a Software Engineer specializing in the MERN stack. I build clean, maintainable web "
         "applications end-to-end, from database design and REST APIs to responsive user interfaces, "
         "and I work full-time on production projects.")
FACTS = [("CURRENTLY", "Software Engineer, full-time"),
         ("LEARNING", "System design and scalable architecture"),
         ("OPEN TO", "Collaboration on well-scoped projects"),
         ("ASK ME ABOUT", "JavaScript, API design, React, Node.js")]
STACK = [("LANGUAGES", ["JavaScript", "TypeScript", "Java", "C"]),
         ("FRONTEND", ["HTML", "CSS", "Tailwind CSS", "React", "Next.js"]),
         ("BACKEND & DATA", ["Node.js", "Express", "MongoDB"]),
         ("TOOLS", ["Git", "GitHub", "VS Code", "Postman", "Vercel"])]
FOCUS = ["Full Stack Development", "REST APIs", "System Design"]
CONNECT = "For work inquiries or collaboration, reach out through any of the links below."

# ------------------------------------------------------------------ data
QUERY = """
query($login:String!){ user(login:$login){
  contributionsCollection{ totalCommitContributions restrictedContributionsCount
    totalPullRequestContributions totalIssueContributions totalRepositoryContributions }
  repositories(first:100, ownerAffiliations:OWNER, isFork:false, orderBy:{field:PUSHED_AT, direction:DESC}){
    nodes{ stargazerCount languages(first:10, orderBy:{field:SIZE, direction:DESC}){ edges{ size node{ name } } } } }
}}"""

def fetch(login, token):
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        u = json.load(r)["data"]["user"]
    cc, langs, stars = u["contributionsCollection"], {}, 0
    for repo in u["repositories"]["nodes"]:
        stars += repo["stargazerCount"]
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]
    tot = sum(v for _, v in top) or 1
    return {"commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"], "stars": stars,
            "prs": cc["totalPullRequestContributions"], "issues": cc["totalIssueContributions"],
            "contributed": cc["totalRepositoryContributions"], "languages": [[n, v / tot * 100] for n, v in top]}

# ------------------------------------------------------------------ svg helpers
def fmt(n): return (f"{n/1000:.1f}k".replace(".0k", "k")) if n >= 1000 else str(n)

def T(x, y, s, size, fill="#e2e8f0", weight=400, anchor="start", ls=0, extra=""):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    l = f' letter-spacing="{ls}"' if ls else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-family="{SANS}" font-size="{size}" font-weight="{weight}" fill="{fill}"{a}{l} {extra}>{s}</text>'

def hr(x1, x2, y, op=0.12): return f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" stroke="#ffffff" stroke-opacity="{op}"/>'

def defs(W, H):
    g = lambda i, c, o: f'<radialGradient id="{i}"><stop offset="0" stop-color="{c}" stop-opacity="{o}"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>'
    return f'''<defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0.4" y2="1"><stop offset="0" stop-color="#060814"/><stop offset="0.5" stop-color="#0a1030"/><stop offset="1" stop-color="#070a1c"/></linearGradient>
    {g("b1","#6366f1",0.5)}{g("b2","#a855f7",0.42)}{g("b3","#06b6d4",0.34)}{g("b4","#3b82f6",0.3)}
    {g("gc","#22d3ee",0.9)}{g("gv","#c084fc",0.9)}{g("gp","#f472b6",0.9)}
    <linearGradient id="acc" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22d3ee"/><stop offset="0.5" stop-color="#818cf8"/><stop offset="1" stop-color="#c084fc"/></linearGradient>
    <linearGradient id="name" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffffff"/><stop offset="0.6" stop-color="#e0e7ff"/><stop offset="1" stop-color="#a5f3fc"/></linearGradient>
    <linearGradient id="core" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#22d3ee"/><stop offset="1" stop-color="#8b5cf6"/></linearGradient>
    <style>
      @keyframes d1{{from{{transform:translate(0,0)}}to{{transform:translate(70px,46px)}}}}
      @keyframes d2{{from{{transform:translate(0,0)}}to{{transform:translate(-60px,70px)}}}}
      @keyframes d3{{from{{transform:translate(0,0)}}to{{transform:translate(48px,-64px)}}}}
      @keyframes tw{{0%,100%{{opacity:.08}}50%{{opacity:.75}}}}
      .bl{{animation-timing-function:ease-in-out;animation-iteration-count:infinite;animation-direction:alternate}}
      .st{{animation:tw 6s ease-in-out infinite}}
      @media (prefers-reduced-motion: reduce){{.bl,.st{{animation:none}}}}
    </style>
    <clipPath id="clip"><rect width="{W}" height="{H}" rx="26"/></clipPath>
    <clipPath id="barclip"><rect x="0" y="0" width="1" height="1"/></clipPath>
  </defs>'''

def mesh(W, H, mobile):
    s = 0.62 if mobile else 1
    blobs = [(W - 150, 80, 520, "b1"), (W + 30, H * 0.36, 430, "b2"), (-70, H * 0.58, 470, "b3"),
             (W * 0.78, H * 0.86, 480, "b2"), (W * 0.28, -90, 380, "b4"), (W * 0.2, H * 0.97, 430, "b3")]
    out = f'<rect width="{W}" height="{H}" fill="url(#bg)"/>'
    for i, (x, y, r, g) in enumerate(blobs):
        dur = 24 + i * 5
        out += (f'<circle class="bl" cx="{x:.0f}" cy="{y:.0f}" r="{r*s:.0f}" fill="url(#{g})" '
                f'style="animation-name:d{i%3+1};animation-duration:{dur}s;animation-delay:-{i*3}s"/>')
    rng = random.Random(11)
    for _ in range(int(W * H / 30000)):
        out += (f'<circle class="st" cx="{rng.uniform(8, W-8):.0f}" cy="{rng.uniform(8, H-8):.0f}" r="{rng.uniform(0.7, 1.5):.1f}" '
                f'fill="#cbd5e1" opacity="0.3" style="animation-duration:{rng.uniform(4, 9):.1f}s;animation-delay:-{rng.uniform(0, 9):.1f}s"/>')
    return out

def dot(x, y, r, g, c):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r*5}" fill="url(#{g})" opacity="0.55"/><circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{c}"/>'

def spin(cx, cy, dur, sign=1):
    return (f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="{360*sign} {cx} {cy}" '
            f'dur="{dur}s" repeatCount="indefinite"/>')

def orbits(cx, cy, radii, ops, dots, core):
    o = "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#acc)" stroke-width="1.3" stroke-opacity="{op}"/>' for r, op in zip(radii, ops))
    o += (f'<circle cx="{cx}" cy="{cy}" r="{max(radii)+46}" fill="none" stroke="url(#acc)" stroke-width="1.4" stroke-opacity="0.3" stroke-dasharray="2 16" stroke-linecap="round">'
          + spin(cx, cy, 140) + '</circle>')
    for i, (r, a, g, c, sz) in enumerate(dots):
        x, y = cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))
        o += f'<g>{dot(x, y, sz, g, c)}{spin(cx, cy, 46 + r * 0.35, 1 if i % 2 == 0 else -1)}</g>'
    return o + (f'<circle cx="{cx}" cy="{cy}" r="{core*2.2:.0f}" fill="url(#gv)" opacity="0.25"><animate attributeName="opacity" values="0.18;0.36;0.18" dur="6s" repeatCount="indefinite"/></circle>'
                f'<circle cx="{cx}" cy="{cy}" r="{core}" fill="url(#core)"/>'
                f'<circle cx="{cx}" cy="{cy}" r="{core}" fill="none" stroke="#fff" stroke-opacity="0.4" stroke-width="1.5"/>'
                f'<circle cx="{cx}" cy="{cy}" r="{core*0.62:.1f}" fill="none" stroke="#fff" stroke-opacity="0.35" stroke-width="1.2"/>'
                f'<circle cx="{cx}" cy="{cy}" r="{core*0.22:.1f}" fill="#fff" fill-opacity="0.9"/>')

def label(x, y, idx, text, color, size=13):
    return (f'<text x="{x}" y="{y}" font-family="{SANS}" font-size="{size}" font-weight="700" letter-spacing="4">'
            f'<tspan fill="{color}">{idx}</tspan><tspan fill="#94a3b8">{NB}{NB}{esc(text)}</tspan></text>')

def lines(x, y, txts, size, lh, fill="#cbd5e1", weight=400):
    return "".join(T(x, y + i * lh, esc(t), size, fill, weight) for i, t in enumerate(txts))

def items_text(items, accent):
    sep = f'<tspan fill="{accent}">{NB}{NB}·{NB}{NB}</tspan>'
    return sep.join(f"<tspan>{esc(i)}</tspan>" for i in items)

def wrap_items(items, maxc):
    rows, cur = [], []
    for it in items:
        if cur and len(" · ".join(cur + [it])) + 4 > maxc: rows.append(cur); cur = []
        cur.append(it)
    return rows + [cur]

def stats_items(d):
    return [("Commits", fmt(d["commits"])), ("Stars Earned", fmt(d["stars"])), ("Pull Requests", fmt(d["prs"])),
            ("Issues", fmt(d["issues"])), ("Contributed To", fmt(d["contributed"])), ("Languages", str(len(d["languages"])))]

def lang_bar(d, x, y, w, h):
    tot = sum(p for _, p in d["languages"]) or 1
    segs, cx = "", x
    for i, (n, p) in enumerate(d["languages"]):
        sw = w * p / tot
        segs += f'<rect x="{cx:.1f}" y="{y}" width="{sw:.1f}" height="{h}" fill="{PAL[i%6]}"/>'
        cx += sw
    cid = f"bar{int(x)}{int(y)}"
    return (f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}"/></clipPath>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="#ffffff" fill-opacity="0.07"/>'
            f'<g clip-path="url(#{cid})">{segs}</g>')

def svg(W, Htot, crop, body, mobile, label="Mahmudul Hoque Rifat, Software Engineer"):
    x, y, w, h = crop
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x:g} {y:g} {w:g} {h:g}" width="{w:g}" height="{h:g}" role="img" aria-label="{label}">
  {defs(W, Htot)}
  <g clip-path="url(#clip)">
    {mesh(W, Htot, mobile)}
    {body}
  </g>
  <rect x="0.5" y="0.5" width="{W-1}" height="{Htot-1}" rx="26" fill="none" stroke="#ffffff" stroke-opacity="0.12"/>
</svg>
'''

CONTACTS = [("linkedin", "LinkedIn", "Let's connect", "#0ea5e9", "#6366f1"),
            ("email", "Email", "rifat.swe00@gmail.com", "#f472b6", "#a855f7"),
            ("facebook", "Facebook", "Send a message", "#3b82f6", "#22d3ee")]

def glyph(key, cx, cy, k=1.0):
    if key == "linkedin":
        return T(cx, cy + 10 * k, "in", 28 * k, "#fff", 800, "middle")
    if key == "email":
        return (f'<rect x="{cx-17*k:.1f}" y="{cy-12*k:.1f}" width="{34*k:.1f}" height="{24*k:.1f}" rx="5" fill="none" stroke="#fff" stroke-width="2.6"/>'
                f'<path d="M{cx-15*k:.1f} {cy-9*k:.1f} L{cx:.1f} {cy+4*k:.1f} L{cx+15*k:.1f} {cy-9*k:.1f}" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>')
    return T(cx + 2 * k, cy + 13 * k, "f", 36 * k, "#fff", 800, "middle")

def icon(key, cx, cy, r, c1, c2):
    gid = f"ic{key}"
    return (f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
            f'<circle cx="{cx}" cy="{cy}" r="{r*1.5:.0f}" fill="{c1}" fill-opacity="0.16"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{gid})"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#fff" stroke-opacity="0.35" stroke-width="1.5"/>'
            + glyph(key, cx, cy, r / 30))

def strip_desktop(i, W, ys, key, label_, sub, c1, c2):
    x0 = i * W / 3
    cx, cy = x0 + 96, ys + 82
    b = hr(max(x0, 72), min(x0 + W / 3, 1128), ys + 0.5)
    if i: b += f'<line x1="{x0+0.5:.1f}" y1="{ys+34}" x2="{x0+0.5:.1f}" y2="{ys+130}" stroke="#fff" stroke-opacity="0.1"/>'
    b += icon(key, cx, cy, 30, c1, c2)
    b += T(x0 + 150, ys + 76, label_, 26, "#f8fafc", 800) + T(x0 + 150, ys + 104, esc(sub), 17, "#94a3b8")
    ax, ay = x0 + W / 3 - 56, ys + 48
    b += f'<path d="M{ax-6} {ay-6} L{ax+6} {ay-6} L{ax+6} {ay+6} M{ax+6} {ay-6} L{ax-8} {ay+8}" fill="none" stroke="#cbd5e1" stroke-opacity="0.8" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'
    return b

def strip_mobile(i, W, ys, key, label_, c1, c2):
    x0 = i * W / 3
    b = hr(max(x0, 36), min(x0 + W / 3, 564), ys + 0.5)
    if i: b += f'<line x1="{x0+0.5:.1f}" y1="{ys+30}" x2="{x0+0.5:.1f}" y2="{ys+150}" stroke="#fff" stroke-opacity="0.1"/>'
    b += icon(key, x0 + W / 6, ys + 70, 34, c1, c2)
    b += T(x0 + W / 6, ys + 142, label_, 24, "#f8fafc", 800, "middle")
    return b

# ------------------------------------------------------------------ desktop
def desktop(d, stamp):
    W, L, R, C = 1200, 72, 1128, 440
    cw = (R - C) / 3
    b = orbits(1000, 200, [80, 130, 180, 230, 280], [.55, .45, .35, .26, .18],
               [(130, -35, "gc", "#67e8f9", 5), (180, 28, "gv", "#d8b4fe", 5), (80, 150, "gp", "#f9a8d4", 4),
                (230, 200, "gc", "#67e8f9", 4), (230, -60, "gv", "#d8b4fe", 4)], 44)
    b += (f'<rect x="{L}" y="64" width="266" height="38" rx="19" fill="#ffffff" fill-opacity="0.07" stroke="#ffffff" stroke-opacity="0.2"/>'
          f'<circle cx="{L+24}" cy="83" r="5" fill="url(#acc)"/>'
          + T(L + 42, 88, "SOFTWARE ENGINEER", 13, "#c7d2fe", 700, ls=3))
    b += T(L - 2, 190, "Mahmudul Hoque Rifat", 58, "url(#name)", 800)
    b += f'<rect x="{L}" y="212" width="96" height="4" rx="2" fill="url(#acc)"/>'
    b += T(L, 262, "Designing and building scalable web systems.", 22, "#94a3b8")
    b += T(L, 318, items_text(FOCUS, "#818cf8"), 17, "#cbd5e1", 600)
    y = 392
    b += hr(L, R, y)

    def head(y0, idx, name, title, color):
        s = label(L, y0, idx, name, color)
        for i, t in enumerate(title): s += T(L, y0 + 58 + i * 48, esc(t), 40, "url(#name)", 800)
        return s

    # 01 ABOUT
    y0 = y + 62
    b += head(y0, "01", "ABOUT", ["About", "Me"], PAL[0])
    para = textwrap.wrap(ABOUT, 58)
    b += lines(C, y0 + 6, para, 20, 33)
    fy = y0 + 6 + len(para) * 33 + 22
    ends = fy
    for i, (k, v) in enumerate(FACTS):
        fx = C + (i % 2) * (R - C) / 2 + (0 if i % 2 == 0 else 14)
        fyy = fy + (i // 2) * 112
        vl = textwrap.wrap(v, 28)
        b += hr(fx, fx + (R - C) / 2 - 28, fyy)
        b += T(fx, fyy + 30, k, 12, PAL[i], 700, ls=3)
        b += lines(fx, fyy + 60, vl, 19, 26, "#f1f5f9", 600)
        ends = max(ends, fyy + 60 + len(vl) * 26)
    y = max(ends, y0 + 58 + 48 + 20) + 40
    b += hr(L, R, y)

    # 02 STACK
    y0 = y + 62
    b += head(y0, "02", "TECH STACK", ["Tech", "Stack"], PAL[1])
    ry = y0 - 14
    for i, (cat, items) in enumerate(STACK):
        b += hr(C, R, ry)
        b += T(C, ry + 36, esc(cat), 13, PAL[i % 4], 700, ls=3)
        b += T(C + 178, ry + 38, items_text(items, PAL[i % 4]), 18, "#f1f5f9", 600)
        ry += 58
    b += hr(C, R, ry)
    y = max(ry, y0 + 58 + 48) + 40
    b += hr(L, R, y)

    # 03 ACTIVITY
    y0 = y + 62
    b += head(y0, "03", "GITHUB ACTIVITY", ["GitHub", "Activity"], PAL[2])
    sy = y0 - 14
    for i, (lab, val) in enumerate(stats_items(d)):
        x, yy = C + (i % 3) * cw, sy + (i // 3) * 108
        b += hr(x, x + cw - 30, yy)
        b += f'<rect x="{x:.1f}" y="{yy+18}" width="24" height="3" rx="1.5" fill="{PAL[i%6]}"/>'
        b += T(x, yy + 66, val, 44, "url(#name)", 800)
        b += T(x, yy + 92, lab, 14, "#94a3b8")
    ly = sy + 2 * 108 + 34
    b += T(C, ly, "MOST USED LANGUAGES", 12, "#94a3b8", 700, ls=3)
    b += lang_bar(d, C, ly + 18, R - C, 12)
    tot = sum(p for _, p in d["languages"]) or 1
    for i, (n, p) in enumerate(d["languages"]):
        x, yy = C + (i % 3) * cw, ly + 74 + (i // 3) * 36
        b += f'<circle cx="{x+6:.1f}" cy="{yy-6}" r="5.5" fill="{PAL[i%6]}"/>'
        b += T(x + 22, yy, esc(n), 17, "#f1f5f9", 600) + T(x + cw - 34, yy, f"{p/tot*100:.1f}%", 15, "#94a3b8", anchor="end")
    ey = ly + 74 + 36 + 34
    b += T(R, ey, f"Updated {stamp}", 12, "#64748b", anchor="end")
    y = ey + 40
    b += hr(L, R, y)

    # 04 CONNECT
    y0 = y + 62
    b += head(y0, "04", "CONNECT", ["Let's", "Connect"], PAL[3])
    cp = textwrap.wrap(CONNECT, 52)
    b += lines(C, y0 + 6, cp, 20, 33)
    Ht = int(max(y0 + 58 + 48, y0 + 6 + len(cp) * 33) + 48)
    Hs = 150
    Htot = Ht + Hs
    files = {"page-top.svg": svg(W, Htot, (0, 0, W, Ht), b, False)}
    for i, (key, lab, sub, c1, c2) in enumerate(CONTACTS):
        files[f"connect-{key}.svg"] = svg(W, Htot, (i * W / 3, Ht, W / 3, Hs), strip_desktop(i, W, Ht, key, lab, sub, c1, c2), False, lab)
    return files

# ------------------------------------------------------------------ mobile
def mobile(d, stamp):
    W, L, R = 600, 36, 564
    cw = (R - L) / 3
    b = orbits(520, 120, [55, 100, 145, 190, 235], [.55, .45, .35, .26, .18],
               [(100, -40, "gc", "#67e8f9", 5), (145, 40, "gv", "#d8b4fe", 5), (55, 160, "gp", "#f9a8d4", 4)], 30)
    b += (f'<rect x="{L}" y="56" width="304" height="42" rx="21" fill="#ffffff" fill-opacity="0.07" stroke="#ffffff" stroke-opacity="0.2"/>'
          f'<circle cx="{L+26}" cy="77" r="6" fill="url(#acc)"/>' + T(L + 46, 82, "SOFTWARE ENGINEER", 15, "#c7d2fe", 700, ls=3))
    b += T(L - 2, 200, "Mahmudul", 62, "url(#name)", 800) + T(L - 2, 268, "Hoque Rifat", 62, "url(#name)", 800)
    b += f'<rect x="{L}" y="292" width="110" height="5" rx="2.5" fill="url(#acc)"/>'
    b += lines(L, 344, ["Designing and building", "scalable web systems."], 25, 34, "#94a3b8")
    b += T(L, 426, items_text(FOCUS[:2], "#818cf8"), 19, "#cbd5e1", 600) + T(L, 456, esc(FOCUS[2]), 19, "#cbd5e1", 600)
    y = 506
    b += hr(L, R, y)

    def head(y0, idx, name, title, color):
        return label(L, y0, idx, name, color, 14) + T(L, y0 + 56, esc(title), 42, "url(#name)", 800)

    # about
    y0 = y + 60
    b += head(y0, "01", "ABOUT", "About Me", PAL[0])
    para = textwrap.wrap(ABOUT, 36)
    b += lines(L, y0 + 112, para, 22, 35)
    fy = y0 + 112 + len(para) * 35 + 10
    for k, v in FACTS:
        vl = textwrap.wrap(v, 34)
        b += hr(L, R, fy) + T(L, fy + 32, k, 13, PAL[FACTS.index((k, v))], 700, ls=3)
        b += lines(L, fy + 66, vl, 22, 30, "#f1f5f9", 600)
        fy += 66 + len(vl) * 30 + 14
    y = fy + 30
    b += hr(L, R, y)

    # stack
    y0 = y + 60
    b += head(y0, "02", "TECH STACK", "Tech Stack", PAL[1])
    ry = y0 + 84
    for i, (cat, items) in enumerate(STACK):
        rows = wrap_items(items, 33)
        b += hr(L, R, ry) + T(L, ry + 34, esc(cat), 14, PAL[i % 4], 700, ls=3)
        for j, row in enumerate(rows):
            b += T(L, ry + 72 + j * 34, items_text(row, PAL[i % 4]), 22, "#f1f5f9", 600)
        ry += 72 + len(rows) * 34 + 8
    y = ry + 22
    b += hr(L, R, y)

    # activity
    y0 = y + 60
    b += head(y0, "03", "GITHUB ACTIVITY", "GitHub Activity", PAL[2])
    sy = y0 + 84
    for i, (lab, val) in enumerate(stats_items(d)):
        x, yy = L + (i % 3) * cw, sy + (i // 3) * 124
        b += hr(x, x + cw - 20, yy) + f'<rect x="{x:.1f}" y="{yy+20}" width="26" height="3" rx="1.5" fill="{PAL[i%6]}"/>'
        b += T(x, yy + 74, val, 44, "url(#name)", 800) + T(x, yy + 104, lab, 16, "#94a3b8")
    ly = sy + 2 * 124 + 36
    b += T(L, ly, "MOST USED LANGUAGES", 13, "#94a3b8", 700, ls=3)
    b += lang_bar(d, L, ly + 22, R - L, 16)
    tot = sum(p for _, p in d["languages"]) or 1
    for i, (n, p) in enumerate(d["languages"]):
        x, yy = L + (i % 2) * (R - L) / 2, ly + 96 + (i // 2) * 46
        b += f'<circle cx="{x+7:.1f}" cy="{yy-7}" r="6.5" fill="{PAL[i%6]}"/>'
        b += T(x + 24, yy, esc(n), 20, "#f1f5f9", 600) + T(x + (R - L) / 2 - 24, yy, f"{p/tot*100:.1f}%", 17, "#94a3b8", anchor="end")
    ey = ly + 96 + 2 * 46 + 22
    b += T(R, ey, f"Updated {stamp}", 13, "#64748b", anchor="end")
    y = ey + 36
    b += hr(L, R, y)

    # connect
    y0 = y + 60
    b += head(y0, "04", "CONNECT", "Let's Connect", PAL[3])
    cp = textwrap.wrap(CONNECT, 36)
    b += lines(L, y0 + 112, cp, 22, 35)
    Ht = int(y0 + 112 + len(cp) * 35 + 40)
    Hs = 200
    Htot = Ht + Hs
    files = {"page-mobile-top.svg": svg(W, Htot, (0, 0, W, Ht), b, True)}
    for i, (key, lab, sub, c1, c2) in enumerate(CONTACTS):
        files[f"connect-{key}-m.svg"] = svg(W, Htot, (i * W / 3, Ht, W / 3, Hs), strip_mobile(i, W, Ht, key, lab, c1, c2), True, lab)
    return files

# ------------------------------------------------------------------ main
def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--seed" in sys.argv:
        data = json.load(open(sys.argv[sys.argv.index("--seed") + 1]))
    else:
        login = args[0] if args else os.environ.get("GITHUB_USER", "")
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not login or not token: sys.exit("Need a username and GH_TOKEN/GITHUB_TOKEN")
        data = fetch(login, token)
    stamp = datetime.now(timezone.utc).strftime("%b %d, %Y").replace(" 0", " ")
    os.makedirs(OUT, exist_ok=True)
    files = {**desktop(data, stamp), **mobile(data, stamp)}
    for name, content in files.items():
        open(os.path.join(OUT, name), "w").write(content)
    print("wrote", ", ".join(files))

if __name__ == "__main__":
    main()
