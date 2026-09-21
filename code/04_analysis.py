#!/usr/bin/env python3
"""04_analysis.py — analysis, figures, tables, and paper/stats.json.

Every number quoted in the paper, abstract, slides, or README is written to
paper/stats.json here and read from there. Figures carry a DRAFT stamp unless
run with --final (only after the author's verification gate).

Usage:  python code/04_analysis.py [--final]
"""
import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import statsmodels.formula.api as smf  # noqa: E402

FINAL = "--final" in sys.argv
ROOT = pathlib.Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
FIG = ROOT / "paper" / "figures"
TAB = ROOT / "paper" / "tables"
FIG.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

HOME = "TN"                             # V6: regional illustration = Tennessee (author's home state)
NEIGHBORS = ["AL", "AR", "GA", "KY", "MS", "MO", "NC", "VA"]  # the eight states bordering Tennessee
LOCAL_FIPS = "47149"                     # Rutherford County, TN (Murfreesboro)
SRAM_DATE, LOOKBACK = pd.Timestamp("2025-06-30"), pd.Timestamp("2020-06-30")

# palette (dataviz reference instance, light mode; validated slots 1-3 all-pairs)
COL = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "yellow": "#eda100",
     "ink": "#0b0b0b", "ink2": "#52514e", "grid": "#e4e3df", "surface": "#fcfcfb"}
SEQ = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]  # ordinal blue, 250->650
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": COL["ink2"],
                     "axes.labelcolor": COL["ink"], "xtick.color": COL["ink2"], "ytick.color": COL["ink2"],
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": COL["grid"], "grid.linewidth": 0.8, "axes.axisbelow": True,
                     "figure.facecolor": "white", "axes.facecolor": "white", "savefig.dpi": 200})

log = json.loads((P / "build_log.json").read_text())
S = {"build": log}

rec = pd.read_csv(P / "records_clean.csv.gz", dtype={"rid": str, "fips": str}, parse_dates=["start", "end"])
ss = pd.read_csv(P / "store_spells.csv.gz", dtype={"rid": str, "fips": str}, parse_dates=["start", "end"])
ls = pd.read_csv(P / "location_spells.csv.gz", dtype={"fips": str}, parse_dates=["start", "end"])
nat = pd.read_csv(P / "national_year.csv")
cp = pd.read_csv(P / "county_period.csv", dtype={"fips": str})
cp = cp[cp["stock_jan1_E1"] > 0].copy()
lv = pd.read_csv(P / "location_turnover_2020_2025.csv.gz", dtype={"fips": str})


def stamp(fig):
    if not FINAL:
        fig.text(0.995, 0.995, "DRAFT — not verified", ha="right", va="top", fontsize=8, color="#e34948")


def pct(x, d=1):
    return round(100 * float(x), d)


# ------------------------------------------------------------ 1. national, three definitions
a = nat[nat["group"] == "All"]
tot = a.groupby("definition")[["stock_jan1", "entries", "exits"]].sum()
tot["exit"] = tot.exits / tot.stock_jan1
tot["entry"] = tot.entries / tot.stock_jan1
S["national"] = {
    "stock_2006": int(a[(a.definition == "E1 store") & (a.year == 2006)].stock_jan1.iloc[0]),
    "stock_2024": int(a[(a.definition == "E1 store") & (a.year == 2024)].stock_jan1.iloc[0]),
    "exit_E0_pct": pct(tot.loc["E0 record", "exit"]), "exit_E1_pct": pct(tot.loc["E1 store", "exit"]),
    "exit_E2_pct": pct(tot.loc["E2 location", "exit"]),
    "entry_E1_pct": pct(tot.loc["E1 store", "entry"]), "entry_E2_pct": pct(tot.loc["E2 location", "entry"]),
    "exit_E1_2024_pct": pct(a[(a.definition == "E1 store") & (a.year == 2024)].exit_rate.iloc[0]),
    "exit_E2_2024_pct": pct(a[(a.definition == "E2 location") & (a.year == 2024)].exit_rate.iloc[0]),
    "store_exits_total": int(tot.loc["E1 store", "exits"]), "location_losses_total": int(tot.loc["E2 location", "exits"]),
}
S["national"]["share_store_exits_replaced_in_place_pct"] = pct(1 - tot.loc["E2 location", "exits"] / tot.loc["E1 store", "exits"])
S["national"]["peak_entry_year"] = int(a[a.definition == "E1 store"].set_index("year").entry_rate.idxmax())
S["national"]["peak_entry_E1_pct"] = pct(a[a.definition == "E1 store"].entry_rate.max())

fig, ax = plt.subplots(figsize=(7.2, 4.0))
for d, col, lab in [("E0 record", COL["blue"], "Authorization records end (E0)"),
                    ("E1 store", COL["orange"], "Stores exit (E1)"),
                    ("E2 location", COL["aqua"], "Addresses lose all SNAP retail (E2)")]:
    x = a[a.definition == d]
    ax.plot(x.year, 100 * x.exit_rate, color=col, lw=2, marker="o", ms=4, label=lab)
    ax.annotate(f"{100 * x.exit_rate.iloc[-1]:.1f}%", (x.year.iloc[-1], 100 * x.exit_rate.iloc[-1]),
                xytext=(6, 0), textcoords="offset points", va="center", fontsize=9, color=COL["ink"])
ax.set_ylabel("Annual exit rate (% of 1 Jan stock)")
ax.set_ylim(0, 14)
ax.set_xlim(2005.5, 2025.2)
ax.set_xticks(range(2006, 2025, 2))
ax.legend(frameon=False, fontsize=8.5, loc="upper right")
ax.set_title(f"{S['national']['share_store_exits_replaced_in_place_pct']:.0f}% of SNAP store exits are followed by a new SNAP store\n"
             "at the same address within a year", loc="left", fontsize=10.5)
fig.text(0.01, 0.01, "Source: USDA FNS SNAP Retailer Locator historical data 2005–2025. 50 states + DC; farmers markets "
         "and delivery routes excluded.", fontsize=7, color=COL["ink2"])
stamp(fig)
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(FIG / "fig1_exit_definitions.png")
plt.close(fig)

# ------------------------------------------------------------ 2. store type
g = nat[(nat.definition == "E1 store") & (nat.group.isin(["Large store", "Grocery", "Convenience", "Specialty"]))]
gt = g.groupby("group")[["stock_jan1", "entries", "exits"]].sum()
gt["exit"] = gt.exits / gt.stock_jan1
S["by_type_E1_exit_pct"] = {k: pct(v) for k, v in gt["exit"].items()}
S["by_type_stock_share_pct"] = {k: pct(v) for k, v in (gt.stock_jan1 / gt.stock_jan1.sum()).items()}
order = ["Large store", "Grocery", "Convenience", "Specialty"]
fig, ax = plt.subplots(figsize=(6.2, 3.3))
vals = [100 * gt.loc[k, "exit"] for k in order]
ax.barh(order[::-1], vals[::-1], color=COL["blue"], height=0.55)
for i, v in enumerate(vals[::-1]):
    ax.text(v + 0.2, i, f"{v:.1f}%", va="center", fontsize=9, color=COL["ink"])
ax.set_xlabel("Average annual store exit rate, 2006–2024 (E1)")
ax.grid(axis="y", visible=False)
ax.set_title("Convenience and specialty stores exit three to four\ntimes as often as large stores",
             loc="left", fontsize=10.5)
fig.text(0.01, 0.01, "Large store = supermarket, super store, large grocery. Grocery = small/medium grocery, "
         "combination grocery/other, co-op.", fontsize=7, color=COL["ink2"])
stamp(fig)
fig.tight_layout(rect=(0, 0.05, 1, 1))
fig.savefig(FIG / "fig2_store_type.png")
plt.close(fig)

# ------------------------------------------------------------ 3. poverty gradient
cp["pov_q"] = pd.qcut(cp["poverty_rate"], 5, labels=[1, 2, 3, 4, 5]).astype(int)
lv = lv.merge(cp[["fips", "pov_q"]], on="fips", how="left")


def qsum(d):
    return pd.Series({
        "counties": len(d), "poverty_median": d.poverty_rate.median(),
        "poverty_min": d.poverty_rate.min(), "poverty_max": d.poverty_rate.max(),
        "E1_exit": d.exits_E1.sum() / d.stock_jan1_E1.sum(), "E2_exit": d.exits_E2.sum() / d.stock_jan1_E2.sum(),
        "lost_2020_2025": d.lost_since_2020.sum() / d.locs_2020.sum(),
        "new_2020_2025": d.new_since_2020.sum() / d.locs_2025.sum(),
        "lila_pop_share": d.pop_lila.sum() / d.pop2020.sum(), "pop": d.pop2020.sum(),
    })


pq = cp.groupby("pov_q").apply(qsum)
pq.to_csv(TAB / "table_poverty_quintiles.csv")
S["poverty_quintiles"] = {int(k): {c: (round(float(v), 4) if isinstance(v, float) else int(v)) for c, v in row.items()}
                          for k, row in pq.iterrows()}
q1, q5 = pq.loc[1], pq.loc[5]
S["gradient"] = {
    "E2_q1_pct": pct(q1.E2_exit), "E2_q5_pct": pct(q5.E2_exit), "E2_ratio": round(q5.E2_exit / q1.E2_exit, 2),
    "E1_q1_pct": pct(q1.E1_exit), "E1_q5_pct": pct(q5.E1_exit),
    "lost_q1_pct": pct(q1.lost_2020_2025), "lost_q5_pct": pct(q5.lost_2020_2025),
    "new_q1_pct": pct(q1.new_2020_2025), "new_q5_pct": pct(q5.new_2020_2025),
    "pov_q1_median": round(q1.poverty_median, 1), "pov_q5_median": round(q5.poverty_median, 1),
    "pov_q5_min": round(q5.poverty_min, 1), "pov_q1_max": round(q1.poverty_max, 1),
}
tot_l = lv.dropna(subset=["fips"])
S["turnover_national"] = {
    "locs_2020": int(tot_l.then.sum()), "locs_2025": int(tot_l.now.sum()),
    "lost_pct": pct((tot_l.then & ~tot_l.now).sum() / tot_l.then.sum()),
    "new_pct": pct((tot_l.now & ~tot_l.then).sum() / tot_l.now.sum()),
}

fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.4), sharey=False)
lab = [f"Q{i}\n{pq.loc[i, 'poverty_median']:.0f}%" for i in range(1, 6)]
for ax, col, title in [(axes[0], "E2_exit", "Annual location-loss rate (E2), 2006–2024"),
                       (axes[1], "lost_2020_2025", "SNAP addresses of June 2020\ngone by June 2025")]:
    v = 100 * pq[col].values
    ax.bar(range(5), v, color=SEQ, width=0.62)
    for i, y in enumerate(v):
        ax.text(i, y + 0.15 * (v.max() / 5), f"{y:.1f}%", ha="center", fontsize=8.5, color=COL["ink"])
    ax.set_xticks(range(5), lab, fontsize=8)
    ax.set_title(title, loc="left", fontsize=9.5)
    ax.set_ylim(0, v.max() * 1.2)
    ax.grid(axis="x", visible=False)
axes[0].set_ylabel("%")
fig.supxlabel("County poverty quintile (median county poverty rate)", fontsize=9)
fig.suptitle("SNAP retail access turns over faster in higher-poverty counties", x=0.01, ha="left", fontsize=11)
stamp(fig)
fig.tight_layout(rect=(0, 0.02, 1, 0.97))
fig.savefig(FIG / "fig3_poverty_gradient.png")
plt.close(fig)

# ------------------------------------------------------------ 4. store mix and decomposition
act = ss[(ss.start <= SRAM_DATE) & (ss.end.isna() | (ss.end > SRAM_DATE))].merge(cp[["fips", "pov_q"]], on="fips")
mix = pd.crosstab(act.pov_q, act.group, normalize="index")
mix.to_csv(TAB / "table_store_mix_june2025.csv")
S["mix_june2025_pct"] = {int(k): {c: pct(v) for c, v in row.items()} for k, row in mix.iterrows()}
S["stores_active_june2025"] = int(len(act))

# type-specific E1 exit rates by quintile (2006-2024) -> shift-share
yrs = range(2006, 2025)
sq = ss.merge(cp[["fips", "pov_q"]], on="fips")
rows = []
for y in yrs:
    j1, d31 = pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y}-12-31")
    act_y = (sq.start < j1) & (sq.end.fillna(pd.Timestamp("2099-12-31")) >= j1)
    ex_y = sq.end.between(j1, d31)
    t = pd.DataFrame({"pov_q": sq.pov_q, "group": sq.group, "stock": act_y, "exits": ex_y}).groupby(["pov_q", "group"]).sum()
    rows.append(t)
qt = sum(rows)
qt["rate"] = qt.exits / qt.stock
qt["w"] = qt.stock / qt.groupby(level=0).stock.transform("sum")
actual5 = (qt.loc[5].rate * qt.loc[5].w).sum()
actual1 = (qt.loc[1].rate * qt.loc[1].w).sum()
cf5 = (qt.loc[5].rate * qt.loc[1].w).sum()   # Q5 rates, Q1 mix
S["shift_share_E1"] = {"q5_actual_pct": pct(actual5, 2), "q1_actual_pct": pct(actual1, 2),
                       "q5_with_q1_mix_pct": pct(cf5, 2),
                       "share_of_gap_from_mix_pct": pct((actual5 - cf5) / (actual5 - actual1))}
S["within_type_E1_exit_pct"] = {g_: {"Q1": pct(qt.loc[(1, g_), "rate"]), "Q5": pct(qt.loc[(5, g_), "rate"])}
                                for g_ in order}
qt.reset_index().to_csv(TAB / "table_type_by_quintile_E1.csv", index=False)

fig, ax = plt.subplots(figsize=(6.8, 3.3))
cols4 = [COL["blue"], COL["orange"], COL["aqua"], COL["yellow"]]
left = np.zeros(5)
for gname, col in zip(order, cols4):
    v = 100 * mix[gname].reindex(range(1, 6)).values
    ax.barh(range(5), v, left=left, color=col, height=0.6, label=gname, edgecolor="white", linewidth=2)
    for i in range(5):
        if v[i] > 6:
            ax.text(left[i] + v[i] / 2, i, f"{v[i]:.0f}%", ha="center", va="center", fontsize=8,
                    color="white" if gname in ("Large store",) else COL["ink"])
    left += v
ax.set_yticks(range(5), [f"Q{i} ({pq.loc[i, 'poverty_median']:.0f}%)" for i in range(1, 6)], fontsize=8.5)
ax.invert_yaxis()
ax.set_xlim(0, 100)
ax.set_xlabel("Share of SNAP-authorized stores open 30 June 2025 (the SRAM reference month)")
ax.grid(False)
ax.legend(ncol=4, frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(0, -0.2))
ax.set_title("Poorer counties' SNAP access leans on high-churn formats", loc="left", fontsize=10.5)
stamp(fig)
fig.tight_layout()
fig.savefig(FIG / "fig4_store_mix.png")
plt.close(fig)

# ------------------------------------------------------------ 5. county regressions (descriptive)
conv = act.groupby("fips").group.apply(lambda s: (s == "Convenience").mean()).rename("conv_share_2025")
large = act.groupby("fips").group.apply(lambda s: (s == "Large store").mean()).rename("large_share_2025")
cp = cp.merge(conv, on="fips", how="left").merge(large, on="fips", how="left")
cp["log_pop"] = np.log(cp["pop2020"])
cp["pov10"] = cp["poverty_rate"] / 10
cp["lila10"] = cp["lila_pop_share"] * 10
cp["urban10"] = cp["urban_pop_share"] * 10
cp["y_E2"] = 100 * cp["exit_rate_E2"]
cp["y_E1"] = 100 * cp["exit_rate_E1"]
cp["y_lost"] = 100 * cp["share_2020_lost"]
cp["conv10"] = cp["conv_share_2025"] * 10
models = {}
specs = [("E2 (1)", "y_E2 ~ pov10 + lila10 + urban10 + log_pop + C(st)", "stock_jan1_E2"),
         ("E2 (2)", "y_E2 ~ pov10 + lila10 + urban10 + log_pop + conv10 + C(st)", "stock_jan1_E2"),
         ("E1 (3)", "y_E1 ~ pov10 + lila10 + urban10 + log_pop + C(st)", "stock_jan1_E1"),
         ("Lost 2020-25 (4)", "y_lost ~ pov10 + lila10 + urban10 + log_pop + C(st)", "locs_2020")]
tab = []
for name, f, wcol in specs:
    d = cp.dropna(subset=[wcol, "conv10", "y_lost"]).query(f"{wcol} > 0")
    m = smf.wls(f, data=d, weights=d[wcol]).fit(cov_type="cluster", cov_kwds={"groups": d["st"]})
    models[name] = m
    row = {"model": name, "n": int(m.nobs), "r2": round(m.rsquared, 3)}
    for v in ["pov10", "lila10", "urban10", "log_pop", "conv10"]:
        if v in m.params:
            row[v] = round(m.params[v], 3)
            row[v + "_se"] = round(m.bse[v], 3)
            row[v + "_p"] = round(m.pvalues[v], 4)
    tab.append(row)
tab = pd.DataFrame(tab)
tab.to_csv(TAB / "table_regressions.csv", index=False)
S["regressions"] = tab.astype(object).where(tab.notna(), None).to_dict(orient="records")
S["mean_y_E2_pct"] = round(float(np.average(cp.dropna(subset=["y_E2"]).y_E2,
                                            weights=cp.dropna(subset=["y_E2"]).stock_jan1_E2)), 2)

# ------------------------------------------------------------ 6. sensitivity to the gap rule (V1)
sens = []
FAR = pd.Timestamp("2099-12-31")


def merge_intervals(df, key, gap):
    d = df[[key, "start", "end"]].copy()
    d["end_f"] = d["end"].fillna(FAR)
    d = d.sort_values([key, "start", "end_f"]).reset_index(drop=True)
    runmax = d.groupby(key)["end_f"].cummax()
    prev = runmax.groupby(d[key]).shift()
    d["spell"] = (prev.isna() | (d["start"] > prev + pd.Timedelta(days=gap))).cumsum()
    g_ = d.groupby("spell").agg(start=("start", "min"), end_f=("end_f", "max"))
    g_["end"] = g_["end_f"].where(g_["end_f"] < FAR)
    return g_


def avg_exit(sp, last=2024):
    st_, ex_ = 0, 0
    for y in range(2006, last + 1):
        j1, d31 = pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y}-12-31")
        st_ += ((sp.start < j1) & (sp.end.fillna(FAR) >= j1)).sum()
        ex_ += sp.end.between(j1, d31).sum()
    return ex_ / st_


for gap in [0, 30, 180, 365, 730]:
    last = 2024 if gap <= 365 else 2023
    sens.append({"gap_days": gap, "exit_years": f"2006-{last}",
                 "E1_exit_pct": pct(avg_exit(merge_intervals(rec, "rid", gap), last), 2),
                 "E2_exit_pct": pct(avg_exit(merge_intervals(rec, "loc", gap), last), 2)})
sens = pd.DataFrame(sens)
sens.to_csv(TAB / "table_gap_sensitivity.csv", index=False)
S["gap_sensitivity"] = sens.to_dict(orient="records")

# batch dates among store exits
ex1 = ss[ss.end.between("2006-01-01", "2024-12-31")]
S["store_exits_on_batch_dates_pct"] = pct(ex1.end_on_batch_date.mean())

# ------------------------------------------------------------ 7. Regional illustration: Tennessee and neighbors
STATE_NAMES = {"TN": "Tennessee", "AL": "Alabama", "AR": "Arkansas", "GA": "Georgia", "KY": "Kentucky",
               "MS": "Mississippi", "MO": "Missouri", "NC": "North Carolina", "VA": "Virginia"}


def area_row(key, d):
    return {"area": key, "counties": len(d),
            "E1_exit_pct": pct(d.exits_E1.sum() / d.stock_jan1_E1.sum()),
            "E2_exit_pct": pct(d.exits_E2.sum() / d.stock_jan1_E2.sum()),
            "lost_2020_2025_pct": pct(d.lost_since_2020.sum() / d.locs_2020.sum()),
            "new_2020_2025_pct": pct(d.new_since_2020.sum() / d.locs_2025.sum()),
            "locs_2025": int(d.locs_2025.sum()),
            "poverty_median": round(float(d.poverty_rate.median()), 1),
            "urban_pop_share_pct": pct(d.pop_urban.sum() / d.pop2020.sum()),
            "lila_pop_share_pct": pct(d.pop_lila.sum() / d.pop2020.sum()),
            "addr_per_10k": round(float(d.locs_2025.sum() / d.pop2020.sum() * 1e4), 1)}


region = [area_row(HOME, cp[cp.st == HOME])]
region += [area_row(st, cp[cp.st == st]) for st in NEIGHBORS]
region.append(area_row("Neighboring states", cp[cp.st.isin(NEIGHBORS)]))
region.append(area_row("Rest of U.S.", cp[~cp.st.isin(NEIGHBORS + [HOME])]))
region.append(area_row("United States", cp))
reg = pd.DataFrame(region)
reg.to_csv(TAB / "table_tennessee_region.csv", index=False)
S["region"] = reg.set_index("area").to_dict(orient="index")
nb = reg[reg.area.isin(NEIGHBORS)]
S["region_neighbors_range"] = {
    "lost_min": float(nb.lost_2020_2025_pct.min()), "lost_min_state": STATE_NAMES[nb.loc[nb.lost_2020_2025_pct.idxmin(), "area"]],
    "lost_max": float(nb.lost_2020_2025_pct.max()), "lost_max_state": STATE_NAMES[nb.loc[nb.lost_2020_2025_pct.idxmax(), "area"]]}
S["tn_counties_top2_poverty_quintiles"] = int(cp[(cp.st == HOME) & (cp.pov_q >= 4)].shape[0])
S["tn_counties"] = int((cp.st == HOME).sum())

lc = cp[cp.fips == LOCAL_FIPS].iloc[0]
S["local_county"] = {"name": "Rutherford County, Tennessee", "place": "Murfreesboro",
                     "E2_exit_pct": pct(lc.exit_rate_E2), "lost_2020_2025_pct": pct(lc.share_2020_lost),
                     "new_2020_2025_pct": pct(lc.share_2025_new), "locs_2025": int(lc.locs_2025),
                     "poverty_rate": round(float(lc.poverty_rate), 1)}

order_ = [HOME] + sorted(NEIGHBORS, key=lambda k: STATE_NAMES[k]) + ["Rest of U.S."]
rp = reg.set_index("area").loc[order_]
fig, ax = plt.subplots(figsize=(6.6, 4.6))
y = np.arange(len(rp))
ax.barh(y - 0.19, rp.lost_2020_2025_pct, height=0.36, color=COL["blue"], edgecolor="white", linewidth=1.5, label="June 2020 addresses gone by June 2025")
ax.barh(y + 0.19, rp.new_2020_2025_pct, height=0.36, color=COL["orange"], edgecolor="white", linewidth=1.5, label="June 2025 addresses new since June 2020")
for i, (l_, n_) in enumerate(zip(rp.lost_2020_2025_pct, rp.new_2020_2025_pct)):
    ax.text(l_ + 0.3, i - 0.19, f"{l_:.1f}%", va="center", fontsize=7.5)
    ax.text(n_ + 0.3, i + 0.19, f"{n_:.1f}%", va="center", fontsize=7.5)
ax.set_yticks(y, [STATE_NAMES.get(k, k) for k in rp.index], fontsize=8.5)
ax.get_yticklabels()[0].set_fontweight("bold")
ax.invert_yaxis()
ax.grid(axis="y", visible=False)
ax.set_xlim(0, rp[["lost_2020_2025_pct", "new_2020_2025_pct"]].max().max() * 1.15)
ax.set_xlabel("% of SNAP-authorized retail addresses")
ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(0, -0.13), ncol=1)
ax.set_title("Five-year turnover of SNAP retail addresses, Tennessee and bordering states", loc="left", fontsize=10)
stamp(fig)
fig.tight_layout()
fig.savefig(FIG / "fig5_tennessee_region.png")
plt.close(fig)

S["counties_zero_lila_pct"] = pct((cp["lila_pop_share"] == 0).mean())
S["counties_analyzed"] = int(len(cp))
S["lila_pop_share_national_pct"] = pct(cp.pop_lila.sum() / cp.pop2020.sum())
cp.to_csv(P / "county_analysis.csv", index=False)
S["final"] = FINAL
(ROOT / "paper" / "stats.json").write_text(json.dumps(S, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
print(json.dumps({k: v for k, v in S.items() if k != "build"}, indent=1, default=str))
