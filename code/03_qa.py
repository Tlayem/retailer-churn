#!/usr/bin/env python3
"""03_qa.py — QA report for the build. Writes data/processed/qa_report.txt.

Read this before trusting any number downstream. Stops with a non-zero exit
if a hard check fails.
"""
import json
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
log = json.loads((P / "build_log.json").read_text())
rec = pd.read_csv(P / "records_clean.csv.gz", dtype={"rid": str, "fips": str}, parse_dates=["start", "end"])
ss = pd.read_csv(P / "store_spells.csv.gz", dtype={"rid": str, "fips": str}, parse_dates=["start", "end"])
ls = pd.read_csv(P / "location_spells.csv.gz", dtype={"fips": str}, parse_dates=["start", "end"])
nat = pd.read_csv(P / "national_year.csv")
cp = pd.read_csv(P / "county_period.csv", dtype={"fips": str})

out, fails = [], []


def say(s=""):
    out.append(s)


def check(ok, msg):
    say(("PASS  " if ok else "FAIL  ") + msg)
    if not ok:
        fails.append(msg)


say("QA REPORT — Retailer Churn and Food Access")
say(f"gap rule (V1): {log['GAP_DAYS']} days; exit years {log['FIRST_YEAR']}-{log['LAST_EXIT_YEAR']}")
say()
say("1. ROW COUNTS")
for k in ["records_raw", "records_end_before_auth_dropped", "records_dropped_farmers_market_delivery_route",
          "records_dropped_outside_50_states_dc", "records_kept", "record_ids", "store_spells", "locations",
          "location_spells"]:
    say(f"   {k:<48}{log[k]:>10,}")
lost = log["records_raw"] - log["records_end_before_auth_dropped"] - log["records_dropped_farmers_market_delivery_route"] \
    - log["records_dropped_outside_50_states_dc"]
check(lost == log["records_kept"], "records reconcile: raw - drops = kept")
check(len(rec) == log["records_kept"], "records_clean.csv.gz row count = kept")
check(ss["rid"].nunique() == log["record_ids"], "every Record ID has at least one store spell")
check(ss["n_records"].sum() == log["records_kept"], "store spells account for every record")
check(ls["n_records"].sum() == log["records_kept"], "location spells account for every record")

say()
say("2. MATCH RATES")
say(f"   county by name            {log['records_county_matched_by_name']:>10,}")
say(f"   county imputed by ZIP     {log['records_county_imputed_by_zip']:>10,}")
say(f"   county unmatched          {log['records_county_unmatched']:>10,}  (see county_crosswalk_unmatched.csv)")
check(log["county_match_rate"] > 0.999, f"county match rate {log['county_match_rate']:.4%} > 99.9%")
say(f"   records keyed by record ID (no street address): {log['records_without_street_address_keyed_by_record']:,}")
say(f"   SRAM: {log['sram_tracts']:,} tracts, {log['sram_counties']:,} counties, "
    f"{log['sram_states']} states+DC, population {log['sram_pop2020']:,}")
check(log["sram_pop2020"] == 331449281, "SRAM population equals 2020 Census resident population (331,449,281)")
say(f"   counties with a SNAP stock in the panel: {log['counties_in_panel']:,} of {log['sram_counties']:,}")

say()
say("3. DATA FEATURES THAT SHAPE INTERPRETATION")
say(f"   authorization date 1 Jan 1930 (placeholder, pre-period): {log['records_auth_placeholder_1930']:,} records")
say(f"   end dates shared by >= 1,000 records nationally (administrative batch dates): {len(log['batch_end_dates'])}")
say(f"   records ending on a batch date: {log['records_ending_on_batch_dates']:,} of "
    f"{log['records_with_end_date']:,} ended records ({log['records_ending_on_batch_dates']/log['records_with_end_date']:.1%})")
multi = rec.groupby("rid").size()
say(f"   Record IDs with more than one authorization spell: {(multi > 1).sum():,}")
check(rec.groupby("rid")["store_type"].nunique().max() == 1, "store type constant within Record ID")

say()
say("4. RANGE CHECKS")
a = nat[nat["group"] == "All"]
for d in ["E0 record", "E1 store", "E2 location"]:
    x = a[a["definition"] == d]
    say(f"   {d:<12} exit rate {x.exit_rate.min():.3f}-{x.exit_rate.max():.3f}; entry rate "
        f"{x.entry_rate.min():.3f}-{x.entry_rate.max():.3f}; stock {x.stock_jan1.min():,.0f}-{x.stock_jan1.max():,.0f}")
    check(x.exit_rate.between(0, 0.5).all() and x.entry_rate.between(0, 0.5).all(), f"{d}: annual rates in [0, 0.5]")
e0 = a[a.definition == "E0 record"].set_index("year").exit_rate
e1 = a[a.definition == "E1 store"].set_index("year").exit_rate
e2 = a[a.definition == "E2 location"].set_index("year").exit_rate
check(((e0 >= e1 - 1e-9) & (e1 >= e2 - 1e-9)).all(), "ordering holds every year: E0 >= E1 >= E2 exit rates")
check(cp["poverty_rate"].between(0, 100).all(), "county poverty rates in [0, 100]")
check(cp["lila_pop_share"].between(0, 1).all(), "county LILA population shares in [0, 1]")

say()
say("5. NAMED SPOT CHECKS — look each up by hand (V4)")
say("   In the historical CSV (Excel filter on Record ID) and, for open records, the live Retailer Locator")
say("   https://www.fns.usda.gov/snap/retailer-locator")


def show(title, rid):
    r = rec[rec.rid == rid].sort_values("start")
    say(f"   -- {title}: Record ID {rid}")
    for _, x in r.iterrows():
        say(f"      {x['Store Name'][:38]:<38} {x.store_type:<26} {x.st} FIPS {x.fips}  "
            f"{x.start.date()} -> {x.end.date() if pd.notna(x.end) else 'open'}")
    s = ss[ss.rid == rid]
    say(f"      store spells after gap rule: {len(s)}")


open_ = rec[rec.end.isna()]
cand = open_[(open_.st == "TN") & (open_.group == "Large store") & open_["Store Name"].str.contains("KROGER", case=False)]
if len(cand):
    show("easy: open large store, Tennessee", cand.sort_values("rid").iloc[0].rid)
cand = rec[(rec.st == "TN") & (rec.fips == "47149") & (rec.group == "Convenience") & rec.end.notna()]
if len(cand):
    show("closed convenience store, Rutherford County TN (Murfreesboro)", cand.sort_values("rid").iloc[0].rid)
m = multi[multi == 3].index
show("hard: three authorization spells, same Record ID", sorted(m)[0])
cand = rec[rec.placeholder_1930 & rec.end.notna()]
show("placeholder 1930 authorization date", cand.sort_values("rid").iloc[0].rid)
cand = rec[rec.end_on_batch_date]
show("record ending on an administrative batch date", cand.sort_values("rid").iloc[len(cand) // 2].rid)
# location succession example: address with 3+ record IDs
loc_n = rec.groupby("loc")["rid"].nunique()
succ = loc_n[(loc_n >= 3) & ~loc_n.index.str.startswith("RID|")].index
ex = sorted(succ)[len(succ) // 3]
say(f"   -- location succession: address key {ex}")
for _, x in rec[rec["loc"] == ex].sort_values("start").iterrows():
    say(f"      {x.rid:<9}{x['Store Name'][:34]:<34} {x.start.date()} -> {x.end.date() if pd.notna(x.end) else 'open'}")
say(f"      location spells: {len(ls[ls['loc'] == ex])}")

say()
say(f"RESULT: {'ALL HARD CHECKS PASS' if not fails else str(len(fails)) + ' FAILURE(S)'}")
(P / "qa_report.txt").write_text("\n".join(out) + "\n")
print("\n".join(out))
raise SystemExit(1 if fails else 0)
