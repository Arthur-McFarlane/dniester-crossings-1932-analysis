"""Maps of the 1932 Dniester crossings (Figures 3-5):
3. Failure flows        4. Successful origin clusters        5. Successful crossing points

Run from the repository root:  python python/make_maps.py
Reads data/persons.csv, data/gazetteer.csv and data/naturalearth/; writes PNG and PDF files to figures/."""
import json, math, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Polygon, FancyArrowPatch
from matplotlib.lines import Line2D

NE = "data/naturalearth/"
OUT = "figures/"
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.serif": ["DejaVu Serif"], "font.size": 9})

SEA, USSR, ROM, INK = "#dfe4e8", "#eba29e", "#ecd59f", "#2b2b2b"
RIVER = "#5b7fa6"
BINS = [(1, 1, "1"), (2, 4, "2–4"), (5, 9, "5–9"), (10, 24, "10–24"), (25, 999, "25 or more")]
PURPLES = ["#e3d7ee", "#b79ccf", "#8a5fae", "#5e2d82", "#300a45"]
def binc(n):
    for (lo, hi, _), c in zip(BINS, PURPLES):
        if lo <= n <= hi: return c
def bins(n):
    for i, (lo, hi, _) in enumerate(BINS):
        if lo <= n <= hi: return i

# ---------------------------------------------------------------- data
P = pd.read_csv("data/persons.csv")
G = pd.read_csv("data/gazetteer.csv").set_index("place_modern")
OK = set(G.index[G.latitude.notna()])
A = P[(P.direction == "left_to_right") & P.outcome.isin(["crossed", "caught", "killed", "drowned", "fled_back"])].copy()
FAIL, SUCC = A[A.outcome != "crossed"], A[A.outcome == "crossed"]

# ---------------------------------------------------------------- geography
def rings(fname):
    out = []
    for f in json.load(open(NE + fname))["features"]:
        g = f["geometry"]
        for poly in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]):
            out.append(np.array(poly[0]))
    return out
LAND = rings("land.geojson")
LAKES = rings("lakes.geojson")
d = json.load(open(NE + "dniester.geojson"))
RIV = []
for f in d["features"]:
    if f["properties"].get("name") == "Dniester":
        g = f["geometry"]
        RIV += [np.array(p) for p in (g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]])]
MAIN = max(RIV, key=len)
if MAIN[0, 1] < MAIN[-1, 1]: MAIN = MAIN[::-1]

def land_path(ext):
    x0, x1, y0, y1 = ext
    verts, codes = [], []
    for r in LAND:
        if r[:, 0].max() < x0 - 1 or r[:, 0].min() > x1 + 1 or r[:, 1].max() < y0 - 1 or r[:, 1].min() > y1 + 1: continue
        verts += list(r); codes += [Path.MOVETO] + [Path.LINETO] * (len(r) - 2) + [Path.CLOSEPOLY]
    return Path(verts, codes)

def base(ax, ext, sides=True, land=USSR):
    x0, x1, y0, y1 = ext
    k = math.cos(math.radians((y0 + y1) / 2))
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect(1 / k); ax.set_facecolor(SEA)
    lp = land_path(ext)
    ax.add_patch(PathPatch(lp, fc=land, ec="none", zorder=0))
    if sides:  # the Dniester was the border: right bank Romania, left bank USSR
        r = MAIN[(MAIN[:, 0] > x0 - 2)]
        mouth = np.array([[30.45, 46.05], [30.6, 45.6]])  # down the liman to the sea
        west = [[x0 - 3, r[0, 1]], [x0 - 3, y0 - 3]]
        poly = np.vstack([west[:1], r, mouth, [[30.6, y0 - 3]], west[1:]])
        pr = Polygon(poly, closed=True, fc=ROM, ec="none", zorder=1)
        ax.add_patch(pr); pr.set_clip_path(PathPatch(lp, transform=ax.transData))
    for lk in LAKES:
        if lk[:, 0].max() > x0 and lk[:, 0].min() < x1 and lk[:, 1].max() > y0 and lk[:, 1].min() < y1:
            ax.add_patch(Polygon(lk, closed=True, fc=SEA, ec="none", zorder=2))
    for p in RIV:
        ax.plot(p[:, 0], p[:, 1], color=RIVER, lw=1.6, zorder=3, solid_capstyle="round")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_color("#888888"); s.set_linewidth(0.6)
    return k

def place(ax, name, dx=0.04, dy=0.0, ha="left", style="italic", size=8.5, weight="normal"):
    la, lo = G.loc[name, "latitude"], G.loc[name, "longitude"]
    ax.text(lo + dx, la + dy, name, fontsize=size, style=style, ha=ha, va="center", color=INK, zorder=9, fontweight=weight)

def region_labels(ax, sea=True):
    ax.text(0.97, 0.96, "SOVIET UNION\n(Moldavian ASSR)", transform=ax.transAxes, ha="right", va="top", fontsize=10,
            color="#7d2e2a", fontweight="bold", linespacing=1.3, zorder=9)
    ax.text(0.03, 0.30, "ROMANIA\n(Bessarabia)", transform=ax.transAxes, ha="left", va="top", fontsize=10,
            color="#7a5f1d", fontweight="bold", linespacing=1.3, zorder=9)
    if sea: ax.text(0.86, 0.06, "Black Sea", transform=ax.transAxes, ha="center", fontsize=9, style="italic", color="#5a6a78", zorder=9)

def towns(ax, skip=()):
    for n in ("Chisinau", "Tiraspol", "Bender", "Rybnitsa", "Dubasari", "Camenca"):
        la, lo = G.loc[n, "latitude"], G.loc[n, "longitude"]
        ax.plot(lo, la, marker="s", ms=3.4, mfc="white", mec=INK, mew=0.8, zorder=8)
    for n, a in {"Chisinau": (-0.04, 0.0, "right"), "Tiraspol": (0.05, 0.03, "left"), "Bender": (-0.04, -0.03, "right"),
                 "Rybnitsa": (0.05, 0.0, "left"), "Dubasari": (0.05, -0.02, "left"), "Camenca": (0.05, 0.02, "left")}.items():
        if n not in skip: place(ax, n, *a)

def scalebar(ax, x, y, k, km=50, nlen=0.2):
    dl = km / (111.32 * k)
    ax.plot([x, x + dl], [y, y], color=INK, lw=1.6, solid_capstyle="butt", zorder=9)
    for xx in (x, x + dl / 2, x + dl): ax.plot([xx, xx], [y - 0.015, y + 0.015], color=INK, lw=1, zorder=9)
    ax.text(x + dl / 2, y + 0.035, f"{km} km", ha="center", va="bottom", fontsize=8.5, zorder=9)
    ax.annotate("N", xy=(x + dl + 0.25 * nlen / 0.2, y + nlen), xytext=(x + dl + 0.25 * nlen / 0.2, y), ha="center", va="center",
                fontsize=9, fontweight="bold", arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.2), zorder=9)

def dots(ax, counts, s_base=38, s_step=16, zorder=7):
    t = counts.to_frame("n").join(G[["latitude", "longitude"]]).sort_values("n")
    for name, r in t.iterrows():
        ax.scatter(r.longitude, r.latitude, s=s_base + s_step * bins(r.n), c=binc(r.n), edgecolors="white",
                   linewidths=0.8, zorder=zorder)
    return t

def bin_legend(fig, x, y, title):
    hs = [Line2D([], [], ls="", marker="o", ms=math.sqrt(38 + 16 * i), mfc=c, mec="white", mew=0.8)
          for i, c in enumerate(PURPLES)]
    fig.legend(hs, [b[2] for b in BINS], title=title, ncol=5, loc="upper left", bbox_to_anchor=(x, y),
               bbox_transform=fig.transFigure, frameon=False, fontsize=10, title_fontsize=10.5,
               handletextpad=0.5, columnspacing=1.8, alignment="left")

def caption(fig, y, text):
    fig.text(0.5, y, text, ha="center", va="top", fontsize=11, style="italic", wrap=True)

EXT = (27.6, 31.0, 46.15, 48.55)
SOURCE = "Source: ANA, f. A-49, inv. 1, d. 2084. Coastline, lakes and river: Natural Earth. The 1932 border followed the Dniester."

# ================================================================ Figure 3: failure flows
o_f = FAIL[FAIL.origin_modern.isin(OK)]
counts = o_f.origin_modern.value_counts()
flows = o_f[o_f.location_modern.isin(OK) & (o_f.origin_modern != o_f.location_modern)] \
    .groupby(["origin_modern", "location_modern"]).size().rename("n").reset_index()

fig = plt.figure(figsize=(11, 8.4))
ax = fig.add_axes([0.04, 0.2, 0.62, 0.74]); k = base(ax, EXT)
ov = fig.add_axes([0.68, 0.38, 0.30, 0.56]); ov.set_anchor("NW")
inside = lambda n: EXT[0] < G.loc[n, "longitude"] < EXT[1] and EXT[2] < G.loc[n, "latitude"] < EXT[3]

def flow_lines(ax, fl, rad=0.2):
    for _, r in fl.sort_values("n").iterrows():
        o, d_ = G.loc[r.origin_modern], G.loc[r.location_modern]
        ax.add_patch(FancyArrowPatch((o.longitude, o.latitude), (d_.longitude, d_.latitude),
                                     connectionstyle=f"arc3,rad={rad}", arrowstyle="-|>,head_length=3.5,head_width=2",
                                     lw=1.0 + 0.6 * r.n, color=binc(max(r.n, 2)), alpha=0.95, shrinkA=4, shrinkB=4, zorder=6))
flow_lines(ax, flows[flows.origin_modern.map(inside)])
# long-distance flows leave the main map: draw them to the frame edge
for _, r in flows[~flows.origin_modern.map(inside)].iterrows():
    o, d_ = G.loc[r.origin_modern], G.loc[r.location_modern]
    t = 0.0
    xs = np.linspace(d_.longitude, o.longitude, 400); ys = np.linspace(d_.latitude, o.latitude, 400)
    m = (xs > EXT[0]) & (xs < EXT[1]) & (ys > EXT[2]) & (ys < EXT[3])
    ax.plot(xs[m], ys[m], color=PURPLES[2], lw=1.0 + 0.6 * r.n, alpha=0.9, zorder=6, solid_capstyle="round")
towns(ax)
dots(ax, counts[[n for n in counts.index if inside(n)]])
region_labels(ax); scalebar(ax, 27.75, 46.3, k)

# overview: the long-distance origins
OVX = (26.0, 62.0, 43.0, 58.5)
kk = base(ov, OVX, sides=False, land="#ece6dc")
far = counts[[n for n in counts.index if not inside(n)]]
for _, r in flows[~flows.origin_modern.map(inside)].iterrows():
    o, d_ = G.loc[r.origin_modern], G.loc[r.location_modern]
    ov.plot([o.longitude, d_.longitude], [o.latitude, d_.latitude], color=PURPLES[2], lw=1.0 + 0.6 * r.n, zorder=6)
for n, v in far.items():
    la, lo = G.loc[n, "latitude"], G.loc[n, "longitude"]
    ov.scatter(lo, la, s=38 + 16 * bins(v), c=binc(v), edgecolors="white", linewidths=0.8, zorder=7)
    lab = {"Marx, Saratov": "Marx (Saratov)", "Sverdlovsk okrug": "Sverdlovsk", "Umans'kyi": "Uman",
           "Khmelnytskyi": "Proskurov", "Hradenytsi": "Hradenytsi"}.get(n, n)
    right = lo > 55
    ov.text(lo + (-0.8 if right else 0.6), la + 0.45, lab, fontsize=8, color=INK, zorder=9, ha="right" if right else "left")
ov.add_patch(plt.Rectangle((EXT[0], EXT[2]), EXT[1] - EXT[0], EXT[3] - EXT[2], fill=False, ec=INK, lw=0.9, zorder=8))

bin_legend(fig, 0.05, 0.175, "Failed crossers from each place (dots) and along each route (lines)")
fig.savefig(OUT + "figure3_failure_flows.png", dpi=300, bbox_inches="tight", pad_inches=0.15); fig.savefig(OUT + "figure3_failure_flows.pdf", bbox_inches="tight", pad_inches=0.15); plt.close(fig)

# ================================================================ Figures 4 and 5
EXT45 = (28.35, 30.45, 46.4, 48.25)
def cluster_map(counts, title, legend_title, cap, note, fname, labels):
    fig = plt.figure(figsize=(9.5, 10.6))
    ax = fig.add_axes([0.05, 0.19, 0.9, 0.76]); k = base(ax, EXT45)
    towns(ax, skip=set(labels) & set(counts.index))
    t = dots(ax, counts[[n for n in counts.index if inside(n)]], s_base=60, s_step=28)
    for n, (dx, dy, ha) in labels.items():
        if n in t.index:
            la, lo = G.loc[n, "latitude"], G.loc[n, "longitude"]
            ax.text(lo + dx, la + dy, f"{n} ({int(t.n[n])})", fontsize=8.5, ha=ha, va="center", color=INK, zorder=9)
    region_labels(ax, sea=False); scalebar(ax, 28.45, 46.48, k, km=25, nlen=0.08)
    hs = [Line2D([], [], ls="", marker="o", ms=math.sqrt(60 + 28 * i), mfc=c, mec="white", mew=0.8)
          for i, c in enumerate(PURPLES)]
    fig.legend(hs, [b[2] for b in BINS], title=legend_title, ncol=5, loc="upper left", bbox_to_anchor=(0.06, 0.175),
               bbox_transform=fig.transFigure, frameon=False, fontsize=10, title_fontsize=10.5, handletextpad=0.5,
               columnspacing=1.8, alignment="left")
    fig.savefig(OUT + fname + ".png", dpi=300, bbox_inches="tight", pad_inches=0.15); fig.savefig(OUT + fname + ".pdf", bbox_inches="tight", pad_inches=0.15); plt.close(fig)

c4 = SUCC[SUCC.origin_modern.isin(OK)].origin_modern.value_counts()
far4 = [n for n in c4.index if not inside(n)]
cluster_map(c4, "Successful origin clusters: where people who got across came from",
            "People from each place who reached the Romanian bank",
            "Figure 4: Successful Origin Clusters – all places of origin of successful crossers, with darker\n"
            "clusters representing more successful crossings from that location.",
            f"{c4.sum()} of {len(SUCC)} successful crossers have a known place of origin"
            + (f"; not shown: {', '.join(f'{n} ({c4[n]})' for n in far4).replace('Chaplyginsky', 'Ranenburg raion, Russia')}." if far4 else "."),
            "figure4_successful_origin_clusters",
            {"Speia": (-0.05, 0.0, "right"), "Cioburciu": (0.04, 0.03, "left"), "Molovata": (-0.05, 0.0, "right"),
             "Corotna": (0.06, -0.01, "left"), "Hlinaia": (-0.04, -0.045, "right"), "Rybnitsa": (0.05, -0.03, "left"),
             "Slobozia": (-0.06, 0.0, "right"), "Nezavertailovca": (0.05, -0.02, "left"), "Telita": (-0.05, -0.02, "right"),
             "Stroiesti": (-0.05, 0.0, "right"), "Cocieri": (0.05, -0.01, "left")})

c5 = SUCC[SUCC.location_modern.isin(OK)].location_modern.value_counts()
cluster_map(c5, "Successful crossing points: where people got across",
            "People who reached the Romanian bank at each place",
            "Figure 5: Successful Crossing Points – darker clusters mean more successful crossing\n"
            "attempts in that location.",
            f"{c5.sum()} of {len(SUCC)} successful crossings have a known crossing place.",
            "figure5_successful_crossing_points",
            {"Speia": (-0.05, 0.0, "right"), "Cioburciu": (0.04, 0.03, "left"), "Molovata": (-0.05, 0.0, "right"),
             "Corotna": (0.06, -0.01, "left"), "Hlinaia": (-0.04, -0.045, "right"), "Rybnitsa": (0.05, -0.03, "left"),
             "Slobozia": (-0.06, 0.0, "right"), "Nezavertailovca": (0.05, -0.02, "left"), "Telita": (-0.05, -0.02, "right"),
             "Stroiesti": (-0.05, 0.0, "right"), "Cocieri": (0.05, -0.01, "left")})
print("done")
