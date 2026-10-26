"""Independent re-implementation of R/dniester_regressions.R in numpy/scipy, used to check the
R script's logic and give reference numbers for its output. Run from the repository root:
python python/check_regressions.py"""
import numpy as np, pandas as pd
from scipy import optimize, special, stats

D = "data/"
P = pd.read_csv(D + "persons.csv")
T = pd.read_csv(D + "dubasari_daily_temperature_1928_1933.csv", parse_dates=["date"])

A = P[(P.direction == "left_to_right") & P.outcome.isin(["crossed", "caught", "killed", "drowned", "fled_back"])].copy()
A["success"] = (A.outcome == "crossed").astype(int)
print(f"Attempts {len(A)}  crossed {A.success.sum()}  rate {A.success.mean():.3f}")

def design(df, terms, factors=(), ref=None):
    X = pd.DataFrame({"(Intercept)": 1.0}, index=df.index)
    for t in terms:
        X[t] = df[t].astype(float)
    for f in factors:
        lv = sorted(df[f].unique())
        base = ref.get(f, lv[0]) if ref else lv[0]
        for l in lv:
            if l != base:
                X[f"{f}{l}"] = (df[f] == l).astype(float)
    return X

def logit(df, X, cluster="incident_id"):
    Xv, y = X.values, df.success.values.astype(float)
    b = np.zeros(Xv.shape[1])
    for _ in range(100):
        mu = special.expit(Xv @ b); W = mu * (1 - mu)
        H = Xv.T @ (Xv * W[:, None])
        step = np.linalg.lstsq(H, Xv.T @ (y - mu), rcond=None)[0]
        b += step
        if np.max(np.abs(step)) < 1e-10:
            break
    mu = special.expit(Xv @ b); W = mu * (1 - mu)
    bread = np.linalg.pinv(Xv.T @ (Xv * W[:, None]))
    sc = Xv * (y - mu)[:, None]
    g = df[cluster].values
    meat = sum(np.outer(s, s) for s in pd.DataFrame(sc).groupby(g).sum().values)
    G = len(np.unique(g)); meat *= G / (G - 1)
    V = bread @ meat @ bread
    se = np.sqrt(np.diag(V))
    return pd.DataFrame({"coef": b, "se": se, "OR": np.exp(b), "lo": np.exp(b - 1.96 * se),
                         "hi": np.exp(b + 1.96 * se), "p": 2 * stats.norm.sf(np.abs(b / se))}, index=X.columns), V, b

def negbin(y, X):
    Xv = X.values
    def nll(par):
        b, lt = par[:-1], par[-1]; th = np.exp(lt); mu = np.exp(Xv @ b)
        return -np.sum(special.gammaln(y + th) - special.gammaln(th) - special.gammaln(y + 1)
                       + th * np.log(th / (th + mu)) + y * np.log(mu / (th + mu)))
    start = np.r_[np.zeros(Xv.shape[1]), 0.0]; start[0] = np.log(y.mean())
    r = optimize.minimize(nll, start, method="BFGS", options={"gtol": 1e-8, "maxiter": 5000})
    b, th = r.x[:-1], np.exp(r.x[-1]); mu = np.exp(Xv @ b)
    W = mu / (1 + mu / th)
    se = np.sqrt(np.diag(np.linalg.inv(Xv.T @ (Xv * W[:, None]))))
    return pd.DataFrame({"coef": b, "se": se, "RR": np.exp(b), "lo": np.exp(b - 1.96 * se),
                         "hi": np.exp(b + 1.96 * se), "p": 2 * stats.norm.sf(np.abs(b / se))}, index=X.columns), th

show = lambda t, rows: print(t.loc[[r for r in t.index if any(k in r for k in rows)]].round(4).to_string())

# ---------------- Analysis 1
stations = ["Camenca", "Dubasari", "Krasni Mayak", "Tiraspol"]
days = pd.date_range("1932-02-28", "1932-06-26")
panel = pd.MultiIndex.from_product([days, stations], names=["date", "ice_station"]).to_frame(index=False)
dd = A[A.date.notna() & A.ice_station.isin(stations)].copy(); dd["date"] = pd.to_datetime(dd.date)
panel = panel.merge(dd.groupby(["date", "ice_station"]).size().rename("people").reset_index(), how="left") \
             .merge(dd.groupby(["date", "ice_station"]).incident_id.nunique().rename("incidents").reset_index(), how="left")
panel[["people", "incidents"]] = panel[["people", "incidents"]].fillna(0)
rd = P[P.date.notna() & P.ice_station.isin(stations) & P.ice_thickness_cm.notna()][["date", "ice_station", "ice_thickness_cm"]].drop_duplicates()
rd["date"] = pd.to_datetime(rd.date)
def nearest(d, s):
    r = rd[rd.ice_station == s]
    return r.ice_thickness_cm.values[np.argmin(np.abs((r.date - d).dt.days.values))]
panel["ice_cm"] = [nearest(d, s) for d, s in zip(panel.date, panel.ice_station)]
panel["frozen"] = (panel.ice_cm > 0).astype(int)
panel = panel.merge(T, on="date", how="left")
print(f"\nSector-days {len(panel)}; frozen {panel.frozen.sum()}; days with >=1 incident {(panel.incidents>0).sum()}")
print("mean incidents/day frozen vs open:", panel.groupby("frozen").incidents.mean().round(3).to_dict())
print("mean people/day frozen vs open:", panel.groupby("frozen").people.mean().round(3).to_dict())
for lab, yv, terms, df in [("1a people ~ ice", "people", ["ice_cm"], panel),
                           ("1b incidents ~ ice", "incidents", ["ice_cm"], panel),
                           ("1c incidents ~ frozen", "incidents", ["frozen"], panel),
                           ("1d incidents ~ ice + temp", "incidents", ["ice_cm", "temp_c"], panel.dropna(subset=["temp_c"]))]:
    t, th = negbin(df[yv].values, design(df, terms, ["ice_station"]))
    print(f"\n{lab}  (theta {th:.3f}, n {len(df)})"); show(t, terms)

# ---------------- Analysis 2
a2 = A[A.ice_thickness_cm.notna()].copy()
a2["tod"] = a2.time_of_day
a2["frozen"] = (a2.ice_thickness_cm > 0).astype(int)
print(f"\nAnalysis 2: n {len(a2)}")
for lab, terms, fac in [("2a ice", ["ice_thickness_cm"], []), ("2b frozen", ["frozen"], []),
                        ("2c ice+fog+time+sector", ["ice_thickness_cm", "fog"], ["ice_station", "tod"])]:
    t, _, _ = logit(a2, design(a2, terms, fac, ref={"tod": "night", "ice_station": "Camenca"})); print("\n" + lab); show(t, terms + (["tod"] if fac else []))
print(a2.groupby("ice_thickness_cm").success.agg(["size", "mean"]).round(3).to_string())

# ---------------- Analyses 3 and 4
def group_small(s, k=10):
    c = s.value_counts(); return s.where(s.isin(c[c >= k].index), "other")
for lab, col in [("3 origin", "origin_modern"), ("4 place", "location_modern")]:
    df = A.copy(); df["g"] = group_small(df[col])
    rates = df.groupby("g").success.agg(n="size", crossed="sum", rate="mean").sort_values("n", ascending=False)
    print(f"\nAnalysis {lab}: success by group"); print(rates.round(3).to_string())
    print("separated:", rates.index[(rates.crossed == 0) | (rates.crossed == rates.n)].tolist())
    sep = rates.index[(rates.crossed == 0) | (rates.crossed == rates.n)].tolist()
    df = df[~df.g.isin(sep)]
    X = design(df, [], ["g"], ref={"g": "Cioburciu"})
    t, V, b = logit(df, X)
    print(t.round(3).to_string())
    idx = [i for i, c in enumerate(X.columns) if c != "(Intercept)"]
    ok = idx
    w = b[ok] @ np.linalg.pinv(V[np.ix_(ok, ok)]) @ b[ok]
    print(f"joint Wald: chi2 {w:.2f} df {len(ok)} p {stats.chi2.sf(w, len(ok)):.4g}")
    if col == "origin_modern":
        k = df[(df.origin_modern != "unknown") & (df.location_modern != "unknown")].copy()
        k["local"] = (k.origin_modern == k.location_modern).astype(int)
        t, _, _ = logit(k, design(k, ["local"])); print("\n3c own village"); show(t, ["local"])
        print(k.groupby("local").success.agg(["size", "mean"]).round(3).to_string())
    else:
        c = df[df.ice_thickness_cm.notna()].copy()
        t, _, _ = logit(c, design(c, ["ice_thickness_cm"], ["g"], ref={"g": "Cioburciu"})); print("\n4c place + ice"); show(t, ["ice"])
