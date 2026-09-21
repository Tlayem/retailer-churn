#!/usr/bin/env python3
"""02_build.py — authorization records -> store spells -> location spells -> panels.

Three definitions of a retailer "exit", from most to least literal:
  E0  record exit    every authorization End Date in the file
  E1  store exit     a Record ID's authorization ends and the same Record ID is
                     not re-authorized within GAP_DAYS (gaps <= GAP_DAYS are
                     treated as continuous; spells are merged)
  E2  location loss  an address stops hosting ANY SNAP-authorized store and no
                     store (any Record ID) is authorized there within GAP_DAYS

GAP_DAYS is the author's ruling V1 (default 365). Because a GAP_DAYS window
must be observable after an exit, E1/E2 exits are counted through the end of
LAST_EXIT_YEAR only.

Writes data/processed/: records_clean.csv.gz, store_spells.csv.gz,
location_spells.csv.gz, national_year.csv, county_year.csv, county_period.csv,
sram_county.csv, county_crosswalk_unmatched.csv, build_log.json
"""
import json
import pathlib
import re
import unicodedata
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXT = ROOT / "data" / "raw" / "extracted"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

GAP_DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 365   # V1
FIRST_YEAR, LAST_EXIT_YEAR = 2006, 2024
SRAM_DATE = pd.Timestamp("2025-06-30")      # SRAM retailer list: "as of June 2025"
LOOKBACK_DATE = pd.Timestamp("2020-06-30")  # five years earlier
BATCH_MIN = 1000                            # an End Date shared by >= this many records nationally
FAR = pd.Timestamp("2099-12-31")
EXCLUDE_TYPES = {"Farmers' Market", "Delivery Route"}  # excluded by SRAM too
KEEP_STATES = None  # set after reading SRAM (50 states + DC)

GROUP = {
    "Supermarket": "Large store", "Super Store": "Large store", "Large Grocery Store": "Large store",
    "Medium Grocery Store": "Grocery", "Small Grocery Store": "Grocery",
    "Combination Grocery/Other": "Grocery", "Food Buying Co-op": "Grocery",
    "Convenience Store": "Convenience",
    "Meat/Poultry Specialty": "Specialty", "Bakery Specialty": "Specialty",
    "Seafood Specialty": "Specialty", "Fruits/Veg Specialty": "Specialty",
    "Military Commissary": "Other", "Wholesaler": "Other", "Unknown": "Other",
}
log = {"GAP_DAYS": GAP_DAYS, "FIRST_YEAR": FIRST_YEAR, "LAST_EXIT_YEAR": LAST_EXIT_YEAR}

STATE_ABBR = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado",
    "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts",
    "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", "MT": "Montana",
    "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}
NAME_TO_ABBR = {v: k for k, v in STATE_ABBR.items()}


# ---------------------------------------------------------------- helpers
def merge_intervals(df, key, gap_days):
    """Merge [start, end] intervals within `key` when the next start is within gap_days
    of the running max end. Open intervals (end NaT) run to FAR. Returns one row per merged spell."""
    d = df[[key, "start", "end"]].copy()
    d["end_f"] = d["end"].fillna(FAR)
    d = d.sort_values([key, "start", "end_f"]).reset_index(drop=True)
    runmax = d.groupby(key)["end_f"].cummax()
    prev = runmax.groupby(d[key]).shift()
    new = prev.isna() | (d["start"] > prev + pd.Timedelta(days=gap_days))
    d["spell"] = new.cumsum()
    g = d.groupby("spell").agg(**{key: (key, "first"), "start": ("start", "min"), "end_f": ("end_f", "max"),
                                  "n_records": ("start", "size")})
    g["end"] = g["end_f"].where(g["end_f"] < FAR)
    return g.drop(columns="end_f").reset_index(drop=True)


def norm_county(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = s.upper().replace("&", "AND")
    s = re.sub(r"[.'`,-]", " ", s)
    s = re.sub(r"\bSAINT\b", "ST", s)
    s = re.sub(r"\bSTE\b", "ST", s)
    s = re.sub(r"\b(COUNTY|PARISH|BOROUGH|CENSUS AREA|CITY AND BOROUGH|MUNICIPALITY|PLANNING REGION)\b", " ", s)
    return re.sub(r"\s+", "", s)


def rates_by_year(spells, group_col=None, years=range(FIRST_YEAR, LAST_EXIT_YEAR + 1)):
    """Stock on 1 Jan, entries and exits during each year, optionally by group."""
    rows = []
    cols = [group_col] if group_col else []
    for y in years:
        jan1, dec31 = pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y}-12-31")
        endf = spells["end"].fillna(FAR)
        active = (spells["start"] < jan1) & (endf >= jan1)
        entry = spells["start"].between(jan1, dec31)
        exit_ = spells["end"].between(jan1, dec31)
        t = pd.DataFrame({"active": active, "entry": entry, "exit": exit_})
        for c in cols:
            t[c] = spells[c].values
        agg = t.groupby(cols).sum() if cols else t.sum().to_frame().T
        agg = agg.reset_index() if cols else agg
        agg["year"] = y
        rows.append(agg)
    r = pd.concat(rows, ignore_index=True).rename(columns={"active": "stock_jan1", "entry": "entries", "exit": "exits"})
    r["entry_rate"] = r["entries"] / r["stock_jan1"]
    r["exit_rate"] = r["exits"] / r["stock_jan1"]
    return r


# ---------------------------------------------------------------- SRAM (tract -> county)
gen = pd.read_csv(EXT / "SRAM General Tract Characteristics Data.csv", encoding="latin-1")
sd = pd.read_csv(EXT / "SRAM Straight Line Distance Data.csv", encoding="latin-1")
dd = pd.read_csv(EXT / "SRAM Driving Distance Data.csv", encoding="latin-1", nrows=0)
drv_cols = [c for c in dd.columns if c in ("DD_SRAM_LILATracts_1And10", "DD_SRAM_LA1and10", "DD_SRAM_lapop1", "DD_SRAM_lapop10")]
dd = pd.read_csv(EXT / "SRAM Driving Distance Data.csv", encoding="latin-1", usecols=["CensusTract20"] + drv_cols)
tr = gen.merge(sd[["CensusTract20", "SD_SRAM_LILATracts_1And10", "SD_SRAM_LA1and10", "SD_SRAM_lapop1", "SD_SRAM_lapop10",
                   "SD_SRAM_lalowi1", "SD_SRAM_lalowi10"]], on="CensusTract20", how="left")
tr = tr.merge(dd, on="CensusTract20", how="left")
tr["tract"] = tr["CensusTract20"].astype(str).str.zfill(11)
tr["fips"] = tr["tract"].str[:5]
log["sram_tracts"] = len(tr)
log["sram_pop2020"] = int(tr["POP2020"].sum())
KEEP_STATES = {NAME_TO_ABBR[s] for s in tr["State"].unique()}
log["sram_states"] = len(KEEP_STATES)

w = tr["POP2020"]
tr["pop_lila"] = w * tr["SD_SRAM_LILATracts_1And10"].fillna(0)
tr["pop_lowinc"] = w * tr["LowIncomeTracts"].fillna(0)
tr["pop_urban"] = w * tr["Urban"].fillna(0)
tr["pov_x_pop"] = w * tr["PovertyRate"].fillna(0)
tr["pop_pov_ok"] = w * tr["PovertyRate"].notna()
tr["la_pop"] = np.where(tr["Urban"] == 1, tr["SD_SRAM_lapop1"], tr["SD_SRAM_lapop10"])
if "DD_SRAM_LILATracts_1And10" in tr:
    tr["pop_lila_drive"] = w * tr["DD_SRAM_LILATracts_1And10"].fillna(0)
cty = tr.groupby("fips").agg(state=("State", "first"), county20=("County20", "first"), county24=("County24", "first"),
                             pop2020=("POP2020", "sum"), pop_lila=("pop_lila", "sum"), pop_lowinc=("pop_lowinc", "sum"),
                             pop_urban=("pop_urban", "sum"), pov_x_pop=("pov_x_pop", "sum"), pop_pov_ok=("pop_pov_ok", "sum"),
                             la_pop=("la_pop", "sum"), snap_hh=("TractSNAP", "sum"), ohu=("OHU2020", "sum"),
                             hunv=("TractHUNV", "sum"), n_tracts=("tract", "size"),
                             n_lila_tracts=("SD_SRAM_LILATracts_1And10", "sum"),
                             **({"pop_lila_drive": ("pop_lila_drive", "sum")} if "pop_lila_drive" in tr else {}))
cty["lila_pop_share"] = cty["pop_lila"] / cty["pop2020"]
cty["low_access_pop_share"] = cty["la_pop"] / cty["pop2020"]
cty["lowinc_pop_share"] = cty["pop_lowinc"] / cty["pop2020"]
cty["urban_pop_share"] = cty["pop_urban"] / cty["pop2020"]
cty["poverty_rate"] = cty["pov_x_pop"] / cty["pop_pov_ok"]
cty["snap_hh_share"] = cty["snap_hh"] / cty["ohu"]
cty["no_vehicle_hh_share"] = cty["hunv"] / cty["ohu"]
if "pop_lila_drive" in cty:
    cty["lila_pop_share_drive"] = cty["pop_lila_drive"] / cty["pop2020"]
cty = cty.reset_index()
cty["st"] = cty["state"].map(NAME_TO_ABBR)
cty.to_csv(OUT / "sram_county.csv", index=False)
log["sram_counties"] = len(cty)

# county name crosswalk on 2020 county names (the tract FIPS in SRAM are 2020 counties).
# Secondary keys: Virginia independent cities without the word CITY, used only where
# that does not collide with a county of the same name (Richmond, Fairfax, Roanoke...).
# 2024 names (Connecticut planning regions) are NOT used: a region spans several
# 2020 counties. Records that still fail are assigned by ZIP code below.
prim = cty.assign(key=cty["county20"].map(norm_county))[["st", "key", "fips"]]
sec = cty.assign(key=cty["county20"].map(norm_county).str.replace(r"CITY$", "", regex=True))[["st", "key", "fips"]]
sec = sec[~sec.set_index(["st", "key"]).index.isin(prim.set_index(["st", "key"]).index)]
sec = sec[~sec.duplicated(["st", "key"], keep=False)]
ALIAS = {("DC", "DISTOFCOLUMBIA"): "11001", ("LA", "STJOHNBAPTIST"): "22095", ("KY", "MUHLENBURG"): "21177",
         ("MS", "CHIKASAW"): "28017", ("AK", "FAIRBANKSNOSTAR"): "02090", ("MO", "SAINTEGENEVIEVE"): "29186",
         ("AK", "SEFAIRBANKS"): "02240", ("TX", "BRISCO"): "48045", ("VA", "BEDFORDCITY"): "51019"}
alias = pd.DataFrame([(k[0], k[1], v) for k, v in ALIAS.items()], columns=["st", "key", "fips"])
xw = pd.concat([prim, sec, alias]).drop_duplicates(["st", "key"])
# known spelling differences between FNS county field and Census names, resolved by the name
# the FNS file uses; each is listed in the QA report

# ---------------------------------------------------------------- SNAP records
raw = pd.read_csv(EXT / "Historical SNAP Retailer Locator Data 2005-2025.csv", dtype=str, encoding="utf-8-sig")
raw = raw.apply(lambda s: s.str.strip())
log["records_raw"] = len(raw)
r = raw.rename(columns={"Record ID": "rid", "Store Type": "store_type", "State": "st", "County": "county"})
r["start"] = pd.to_datetime(r["Authorization Date"], format="%m/%d/%Y")
r["end"] = pd.to_datetime(r["End Date"].replace("", None), format="%m/%d/%Y")
r["placeholder_1930"] = r["start"] == pd.Timestamp("1930-01-01")
log["records_auth_placeholder_1930"] = int(r["placeholder_1930"].sum())

bad = r["end"].notna() & (r["end"] < r["start"])
log["records_end_before_auth_dropped"] = int(bad.sum())
r = r[~bad]
excl_type = r["store_type"].isin(EXCLUDE_TYPES)
log["records_dropped_farmers_market_delivery_route"] = int(excl_type.sum())
r = r[~excl_type]
excl_st = ~r["st"].isin(KEEP_STATES)
log["records_dropped_outside_50_states_dc"] = int(excl_st.sum())
r = r[~excl_st]
log["records_kept"] = len(r)
r["group"] = r["store_type"].map(GROUP)

# batch end dates
end_counts = r["end"].value_counts()
batch_dates = set(end_counts[end_counts >= BATCH_MIN].index)
r["end_on_batch_date"] = r["end"].isin(batch_dates)
log["batch_end_dates"] = sorted(d.strftime("%Y-%m-%d") for d in batch_dates)
log["records_ending_on_batch_dates"] = int(r["end_on_batch_date"].sum())
log["records_with_end_date"] = int(r["end"].notna().sum())

# address key
street_no = r["Street Number"].fillna("").str.upper()
street = r["Street Name"].fillna("").str.upper().str.replace(r"[^A-Z0-9 ]", " ", regex=True)
street = street.str.replace(r"\b(STREET)\b", "ST", regex=True).str.replace(r"\b(AVENUE)\b", "AVE", regex=True) \
               .str.replace(r"\b(ROAD)\b", "RD", regex=True).str.replace(r"\b(HIGHWAY)\b", "HWY", regex=True) \
               .str.replace(r"\b(DRIVE)\b", "DR", regex=True).str.replace(r"\b(BOULEVARD)\b", "BLVD", regex=True) \
               .str.replace(r"\s+", " ", regex=True).str.strip()
zip5 = r["Zip Code"].str[:5]
has_addr = (street_no != "") & (street != "")
r["loc"] = np.where(has_addr, street_no + "|" + street + "|" + zip5, "RID|" + r["rid"])
log["records_without_street_address_keyed_by_record"] = int((~has_addr).sum())

# county FIPS
r["ckey"] = r["county"].fillna("").map(norm_county)
r = r.merge(xw.rename(columns={"key": "ckey"}), on=["st", "ckey"], how="left")
r["fips_method"] = np.where(r["fips"].notna(), "name", None)
log["records_county_matched_by_name"] = int(r["fips"].notna().sum())
# ZIP imputation: modal FIPS among name-matched records sharing state + 5-digit ZIP
zmode = r[r["fips"].notna()].assign(z=r["Zip Code"].str[:5]).groupby(["st", "z"])["fips"] \
    .agg(lambda s: s.value_counts().index[0])
need = r["fips"].isna()
imp = pd.Series(list(zip(r.loc[need, "st"], r.loc[need, "Zip Code"].str[:5])), index=r.index[need]).map(zmode)
r.loc[need, "fips"] = imp
r.loc[need & r["fips"].notna(), "fips_method"] = "zip"
log["records_county_imputed_by_zip"] = int((r["fips_method"] == "zip").sum())
unm = r[r["fips"].isna()].groupby(["st", "county"], dropna=False).size().rename("records").reset_index() \
    .sort_values("records", ascending=False)
unm.to_csv(OUT / "county_crosswalk_unmatched.csv", index=False)
log["records_county_unmatched"] = int(r["fips"].isna().sum())
log["county_match_rate"] = float(r["fips"].notna().mean())

r[["rid", "Store Name", "store_type", "group", "st", "county", "fips", "loc", "Latitude", "Longitude",
   "start", "end", "placeholder_1930", "end_on_batch_date", "fips_method"]].to_csv(OUT / "records_clean.csv.gz", index=False)

# ---------------------------------------------------------------- E1: store spells
attrs = r.drop_duplicates("rid").set_index("rid")[["store_type", "group", "st", "fips", "loc"]]
ss = merge_intervals(r, "rid", GAP_DAYS).join(attrs, on="rid")
log["store_spells"] = len(ss)
log["record_ids"] = int(r["rid"].nunique())
# was the spell's final end on a batch date?
ss = ss.merge(r[["rid", "end", "end_on_batch_date"]].drop_duplicates(["rid", "end"]), on=["rid", "end"], how="left")
ss["end_on_batch_date"] = ss["end_on_batch_date"].fillna(False).astype(bool)
ss.to_csv(OUT / "store_spells.csv.gz", index=False)

# ---------------------------------------------------------------- E2: location spells
loc_attr = r.sort_values("start").groupby("loc").agg(st=("st", "last"), fips=("fips", "last"))
ls = merge_intervals(r.rename(columns={}), "loc", GAP_DAYS).join(loc_attr, on="loc")
# does the location ever host a large store?
large_locs = set(r.loc[r["group"] == "Large store", "loc"])
ls["ever_large"] = ls["loc"].isin(large_locs)
log["location_spells"] = len(ls)
log["locations"] = int(r["loc"].nunique())
ls.to_csv(OUT / "location_spells.csv.gz", index=False)

# ---------------------------------------------------------------- national year tables
rec = r[["start", "end", "group"]].copy()
nat = []
for label, sp in [("E0 record", rec), ("E1 store", ss), ("E2 location", ls)]:
    t = rates_by_year(sp)
    t["definition"] = label
    t["group"] = "All"
    nat.append(t)
    if "group" in sp:
        t = rates_by_year(sp, "group")
        t["definition"] = label
        nat.append(t)
nat = pd.concat(nat, ignore_index=True)
nat.to_csv(OUT / "national_year.csv", index=False)

# ---------------------------------------------------------------- county-year and county-period (E1, E2)
cy = []
for label, sp in [("E1 store", ss), ("E2 location", ls)]:
    sp = sp[sp["fips"].notna()]
    t = rates_by_year(sp, "fips")
    t["definition"] = label
    cy.append(t)
cy = pd.concat(cy, ignore_index=True)
cy.to_csv(OUT / "county_year.csv", index=False)

cp = cy.groupby(["definition", "fips"])[["stock_jan1", "entries", "exits"]].sum().reset_index()
cp["exit_rate"] = cp["exits"] / cp["stock_jan1"]
cp["entry_rate"] = cp["entries"] / cp["stock_jan1"]
cp = cp.pivot(index="fips", columns="definition", values=["stock_jan1", "exits", "entries", "exit_rate", "entry_rate"])
cp.columns = [f"{a}_{b.split()[0]}" for a, b in cp.columns]
cp = cp.reset_index()


# five-year turnover around the SRAM reference date (point-in-time, no gap rule needed)
def active_on(sp, d):
    return (sp["start"] <= d) & (sp["end"].fillna(FAR) > d)


a25, a20 = active_on(ls, SRAM_DATE), active_on(ls, LOOKBACK_DATE)
loc_now = set(ls.loc[a25, "loc"]); loc_then = set(ls.loc[a20, "loc"])
lv = pd.DataFrame({"loc": list(loc_now | loc_then)})
lv["now"] = lv["loc"].isin(loc_now); lv["then"] = lv["loc"].isin(loc_then)
lv = lv.join(loc_attr, on="loc")
lv["ever_large"] = lv["loc"].isin(large_locs)
tv = lv.groupby("fips").agg(locs_2025=("now", "sum"), locs_2020=("then", "sum"),
                            new_since_2020=("now", lambda s: int((s & ~lv.loc[s.index, "then"]).sum())),
                            lost_since_2020=("then", lambda s: int((s & ~lv.loc[s.index, "now"]).sum()))).reset_index()
tv["share_2025_new"] = tv["new_since_2020"] / tv["locs_2025"]
tv["share_2020_lost"] = tv["lost_since_2020"] / tv["locs_2020"]
lv.to_csv(OUT / "location_turnover_2020_2025.csv.gz", index=False)

panel = cty.merge(cp, on="fips", how="left").merge(tv, on="fips", how="left")
panel.to_csv(OUT / "county_period.csv", index=False)
log["counties_in_panel"] = int(panel["stock_jan1_E1"].notna().sum())

(OUT / "build_log.json").write_text(json.dumps(log, indent=2, default=str))
print(json.dumps(log, indent=2, default=str))
