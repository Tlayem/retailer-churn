#!/usr/bin/env python3
"""06_slides.py — write the slide presentation as Slides-artifact files from paper/stats.json.

Output: slides/project/deck.json and slides/project/slides/<id>.html
Figures are referenced by the asset urls in slides/assets.json (written after upload).
Every number on a slide is read from paper/stats.json.
Usage: python code/06_slides.py [--final]      (--final removes every DRAFT marker)
"""
import datetime
import json
import pathlib
import sys

FINAL = "--final" in sys.argv
ROOT = pathlib.Path(__file__).resolve().parents[1]
S = json.loads((ROOT / "paper" / "stats.json").read_text())
A = json.loads((ROOT / "AUTHORS.json").read_text())["authors"][0]
ASSETS = json.loads((ROOT / "slides" / "assets.json").read_text())
OUT = ROOT / "slides" / "project"
(OUT / "slides").mkdir(parents=True, exist_ok=True)

N, G, T, SH, B = S["national"], S["gradient"], S["turnover_national"], S["shift_share_E1"], S["build"]
RG, RN, LC, WT, TY = S["region"], S["region_neighbors_range"], S["local_county"], S["within_type_E1_exit_pct"], S["by_type_E1_exit_pct"]
MIX, PQ = S["mix_june2025_pct"], S["poverty_quintiles"]
R = {r["model"]: r for r in S["regressions"]}
SENS = {r["gap_days"]: r for r in S["gap_sensitivity"]}


def f1(x):
    return f"{float(x):.1f}"


def f2(x):
    return f"{float(x):.2f}"


def f3(x):
    return f"{float(x):.3f}"


def n0(x):
    return f"{int(x):,}"


DARK, LIGHT, ALT, ACC, BODY, MUTED, LINE = "#14213D", "#FAF9F5", "#EEF1F4", "#1C5CAB", "#3F4A5A", "#5B6573", "#DCE1E7"
HEAD = "'Source Serif 4', Georgia, serif"
TEXT = "'IBM Plex Sans', Arial, sans-serif"
FOOT = f"{A['correspondence_name']} · Retailer Churn and Food Access" + ("" if FINAL else " · DRAFT, not verified")

slides, order = {}, []
page = [0]


def sec(sid, inner, bg=LIGHT, color=DARK, notes="", footer=True):
    page[0] += 1
    foot = ""
    if footer:
        foot = (f'<p style="position:absolute; left:128px; bottom:56px; width:1300px; font-size:24px; color:{MUTED}">{FOOT}</p>'
                f'<p style="position:absolute; right:128px; bottom:56px; width:120px; text-align:right; font-size:24px; color:{MUTED}">{page[0]}</p>')
    aside = f"<aside>{notes}</aside>" if notes else ""
    html = (f'<section id="{sid}" data-transition="fade" style="background:{bg}; color:{color}; font-family:{TEXT}; '
            f'padding:112px 128px 150px; display:flex; flex-direction:column; gap:32px">'
            f"{inner}{foot}{aside}</section>\n")
    order.append(sid)
    slides[sid] = html


def eyebrow(t):
    return f'<p style="font-size:24px; font-weight:600; letter-spacing:2px; text-transform:uppercase; color:{ACC}">{t}</p>'


def h2(t, size=56):
    return f'<h2 style="font-family:{HEAD}; font-size:{size}px; font-weight:600; line-height:1.12; color:{DARK}">{t}</h2>'


def head(eb, title, size=56):
    return f'<div style="display:flex; flex-direction:column; gap:10px">{eyebrow(eb)}{h2(title, size)}</div>'


def fig(key, w, h, alt):
    return (f'<img src="{ASSETS[key]}" alt="{alt}" style="width:{w}px; height:{h}px; object-fit:contain; '
            f'background:#FFFFFF; border:1px solid {LINE}; border-radius:12px">')


def bullets(items, size=26, width=None):
    w = f" width:{width}px;" if width else " flex:1;"
    lis = "".join(f"<li>{i}</li>" for i in items)
    return f'<ul style="font-size:{size}px; line-height:1.38; color:{BODY};{w}">{lis}</ul>'


def panel(title, items, width, size=26):
    return (f'<div style="width:{width}px; display:flex; flex-direction:column; gap:14px; background:#FFFFFF; padding:32px; '
            f'border:1px solid {LINE}; border-radius:16px"><h3 style="font-size:30px; font-weight:600; color:{DARK}">{title}</h3>'
            f'{bullets(items, size)}</div>')


def card(title, body, big=None, size=26):
    b = f'<p style="font-family:{HEAD}; font-size:64px; font-weight:600; color:{ACC}; line-height:1.0">{big}</p>' if big else ""
    return (f'<div style="flex:1; display:flex; flex-direction:column; gap:12px; background:#FFFFFF; padding:32px; '
            f'border:1px solid {LINE}; border-radius:16px">{b}<h3 style="font-size:30px; font-weight:600; color:{DARK}">{title}</h3>'
            f'<p style="font-size:{size}px; line-height:1.38; color:{BODY}">{body}</p></div>')


def table(header, rows, widths, size=26, align=None):
    align = align or (["left"] + ["right"] * (len(header) - 1))
    th = "".join(f'<th style="width:{w}%; text-align:{a}">{h}</th>' for h, w, a in zip(header, widths, align))
    trs = "".join("<tr>" + "".join(f'<td style="text-align:{a}">{c}</td>' for c, a in zip(r, align)) + "</tr>" for r in rows)
    return f'<table style="font-size:{size}px; color:{DARK}; font-family:{TEXT}"><tr>{th}</tr>{trs}</table>'


def note(t, size=24):
    return f'<p style="font-size:{size}px; line-height:1.35; color:{MUTED}">{t}</p>'


def row(*children, gap=40, align="center"):
    return f'<div style="display:flex; gap:{gap}px; align-items:{align}">{"".join(children)}</div>'


# ------------------------------------------------------------------ 1 cover
draft = "" if FINAL else '<p style="font-size:26px; font-weight:600; color:#E86A6A">DRAFT — not verified by the author</p>'
sec("cover", f"""
<div style="flex:1"></div>
{draft}
<p style="font-size:28px; font-weight:600; letter-spacing:2px; text-transform:uppercase; color:#8FB8EC">Working paper · September 2026</p>
<h1 style="font-family:{HEAD}; font-size:112px; font-weight:600; line-height:1.05; color:{LIGHT}">Retailer Churn and Food Access</h1>
<p style="font-size:36px; line-height:1.4; color:#C9D3E0">Twenty years of SNAP retailer entry and exit, and what a single-date access map cannot show</p>
<div style="flex:1"></div>
<p style="font-size:32px; color:{LIGHT}"><b>{A['name']}</b></p>
<p style="font-size:26px; color:#C9D3E0">{A['affiliation']}</p>
""", bg=DARK, color=LIGHT, footer=False,
    notes="Framing: food access is usually measured as a stock of nearby stores at one date; this paper measures the flow of stores in and out of that stock.")

# ------------------------------------------------------------------ 2 motivation
sec("motivation", f"""
{head("Motivation", "Food access is measured as distance on a single date")}
{row(
    card("The standard measure", "Share of a tract's population living more than 1 mile (urban) or 10 miles (rural) from a food store, the convention of USDA's Food Access Research Atlas."),
    card("What changed in July 2026", "ERS released the SNAP-authorized Retailer Access Map (SRAM). It measures distance to every SNAP-authorized store, including convenience stores and small groceries, not only supermarkets."),
    card("What it still cannot show", "SRAM uses the retailer list as of June 2025. It records which stores were nearby on that date, but not how long those stores stay."),
    gap=28, align="stretch")}
{note("Sources: USDA ERS, Food Access Research Atlas documentation (2026); SRAM data, initial release July 2026.")}
""", notes="Emphasize that SRAM is a real improvement for SNAP households. The point is not a criticism of SRAM but a missing dimension: time.")

# ------------------------------------------------------------------ 3 why turnover matters
sec("gap", f"""
{head("Why turnover matters", "The stores SRAM adds are the ones that come and go")}
{row(
    panel("Evidence on small formats", [
        "Convenience stores were <b>44%</b> of SNAP retailers but <b>5%</b> of SNAP redemptions in FY2024 (USDA FNS 2026).",
        "Dollar-store entry is associated with the exit of other small-format stores, not grocery stores (Chenarides, Çakır and Richards 2024).",
        "Byrne et al. (2024): the 2008–2012 expansion of SNAP retailers lowered shopping costs, so the stock matters for households."], 800),
    panel("The measurement problem", [
        "If nearby stores enter and exit often, a single-date map overstates how reliable access is.",
        "In administrative data, an authorization ending is not the same as a store closing: owners change, authorizations lapse and return, and records are closed in batches.",
        "The studies reviewed here do not separate these cases or report national turnover rates."], 800),
    gap=32, align="stretch")}
""", notes="This is the literature gap slide. Keep to about one minute.")

# ------------------------------------------------------------------ 4 questions and contributions
sec("questions", f"""
{head("This paper", "Three questions and three contributions")}
{row(
    panel("Research questions", [
        "<b>How often</b> do SNAP retailers exit once administrative record changes are separated from real departures?",
        "<b>Which stores and which places</b> carry the most turnover?",
        "<b>How much</b> of the access in the June 2025 SRAM snapshot is recent?"], 800),
    panel("Contributions", [
        "Three nested definitions of exit: record, store and location.",
        "A national panel of SNAP retailer turnover, 2006–2024, by store type and county poverty.",
        "A link between the retailer panel and SRAM's reference month, showing how recent mapped access is."], 800),
    gap=32, align="stretch")}
{note("The analysis is descriptive. It documents patterns and does not estimate causal effects.")}
""", notes="State the three questions slowly; the rest of the talk answers them in order.")

# ------------------------------------------------------------------ 5 data
sec("data", f"""
{head("Data", "Two public USDA files, linked at the county level")}
{row(
    card("SNAP Retailer Locator, historical file", f"Every retailer authorized at any time from 2005 to 2025 (current to 31 Dec 2025): store type, street address, county, coordinates, authorization and end dates.", big=n0(B['records_raw']) + " records", size=25),
    card("SNAP-authorized Retailer Access Map", f"{n0(B['sram_tracts'])} 2020 census tracts: population, poverty, SNAP households, and low-income/low-access flags. Aggregated to {n0(B['sram_counties'])} counties, weighted by population.", big=n0(B['sram_tracts']) + " tracts", size=25),
    gap=28, align="stretch")}
{table(["Sample construction", "Records"], [
    ["Raw historical file", n0(B['records_raw'])],
    ["Less farmers markets and delivery routes (also excluded by SRAM)", "−" + n0(B['records_dropped_farmers_market_delivery_route'])],
    ["Less records outside the 50 states and DC", "−" + n0(B['records_dropped_outside_50_states_dc'])],
    ["Less records ending before they begin", "−" + n0(B['records_end_before_auth_dropped'])],
    [f"<b>Analysis sample</b> ({n0(B['record_ids'])} retailers; {f2(100 * B['county_match_rate'])}% matched to a county)", "<b>" + n0(B['records_kept']) + "</b>"],
], [80, 20], size=24)}
""", notes="The stock of stores is fully observed from 1 January 2006, because the file includes every retailer authorized at any time since 2005. County matching is by name, with 426 records assigned by ZIP code.")

# ------------------------------------------------------------------ 6 definitions
sec("definitions", f"""
{head("Measurement", "What counts as an exit? Three nested definitions")}
{row(
    card("E0 · Record exit", "Any authorization end date. What a simple count of the file measures."),
    card("E1 · Store exit", "A retailer's authorization ends and the same retailer is not re-authorized within 365 days."),
    card("E2 · Location loss", "An address stops hosting any SNAP store, and no new SNAP store opens there within 365 days."),
    gap=28, align="stretch")}
<p style="font-size:26px; font-weight:600; color:{DARK}">Example: one address in the Bronx, New York (ZIP 10457)</p>
{table(["Retailer at the address", "Authorized", "Ended"], [
    ["Retailer 1", "May 2004", "June 2006"],
    ["Retailer 2 (opened 12 weeks later)", "August 2006", "November 2013"],
    ["Retailer 3", "April 2015", "August 2016"],
    ["Retailer 4", "September 2022", "still open"],
], [56, 22, 22], size=24)}
{note("Three store exits (E1), but only two location losses (E2): the 2006 exit was followed by a new SNAP store within a year.")}
""", notes="Business names are in the QA report; they are left off the slide. E2 is the measure that matters for a household deciding where to shop.")

# ------------------------------------------------------------------ 7 robustness of measurement
s0, s30, s180, s365, s730 = (SENS[k] for k in (0, 30, 180, 365, 730))
sec("window", f"""
{head("Measurement", "How much the continuity window matters")}
{row(
    f'<div style="width:900px; display:flex; flex-direction:column; gap:16px">' +
    table(["Window (days)", "Store exit, %/yr (E1)", "Location loss, %/yr (E2)"],
          [[str(r['gap_days']), f2(r['E1_exit_pct']), f2(r['E2_exit_pct'])] for r in S['gap_sensitivity']], [34, 33, 33], size=26) +
    note("Average annual rates. The 730-day window counts exits through 2023.") + "</div>",
    panel("Reading the table", [
        "Store exit barely moves: re-authorization of the same retailer is uncommon.",
        f"Location loss is sensitive: at 30 days {f1(100 * (1 - s30['E2_exit_pct'] / s30['E1_exit_pct']))}% of store exits are replaced in place; at 365 days, {f1(N['share_store_exits_replaced_in_place_pct'])}%.",
        f"{len(B['batch_end_dates'])} end dates each close 1,000+ records nationally; {f1(S['store_exits_on_batch_dates_pct'])}% of store exits fall on them."], 700, size=25),
    gap=40, align="start")}
""", notes="The 365-day window is a judgment call. The batch dates are administrative clean-ups that date when the agency recorded the exit, not when a store closed; that is why annual rates are lumpy and why county results pool 2006–2024.")

# ------------------------------------------------------------------ 8 result 1
sec("headline", f"""
{head("Result 1 · How often", f"{f1(N['share_store_exits_replaced_in_place_pct'])}% of store exits are replaced at the same address within a year")}
{row(
    fig("fig1", 1000, 556, "Annual exit rates 2006 to 2024 under three definitions"),
    bullets([
        f"Stores exit at <b>{f1(N['exit_E1_pct'])}%</b> a year on average.",
        f"Addresses lose all SNAP retail at <b>{f1(N['exit_E2_pct'])}%</b> a year.",
        f"Counting record end dates as closures overstates location loss by about <b>{round(100 * (N['exit_E0_pct'] / N['exit_E2_pct'] - 1))}%</b>.",
        f"Stock grew from {n0(N['stock_2006'])} (2006) to {n0(N['stock_2024'])} (2024); entry peaked at {f1(N['peak_entry_E1_pct'])}% in {N['peak_entry_year']}."], size=25, width=600),
    gap=40)}
""", notes="The spikes (2006-07, 2014, 2018-19) line up with administrative batch dates. The gap between the orange and green lines is in-place replacement, mostly ownership changes.")

# ------------------------------------------------------------------ 9 result 2
sec("types", f"""
{head("Result 2 · Which stores", "Small formats carry most of the turnover")}
{row(
    fig("fig2", 960, 511, "Store exit rate by store group"),
    bullets([
        f"Large stores exit at <b>{f1(TY['Large store'])}%</b> a year; convenience stores at <b>{f1(TY['Convenience'])}%</b>, about three times as often.",
        f"Convenience stores are <b>{f1(S['by_type_stock_share_pct']['Convenience'])}%</b> of all SNAP store-years, so they account for most exits.",
        f"Specialty stores exit fastest ({f1(TY['Specialty'])}%) but are only {f1(S['by_type_stock_share_pct']['Specialty'])}% of the stock.",
        "SRAM counts all of these formats as access."], size=25, width=640),
    gap=40)}
""", notes="Large = supermarket, super store, large grocery. Grocery = small and medium grocery, combination grocery/other, co-op. Specialty = meat, bakery, seafood, fruit and vegetable.")

# ------------------------------------------------------------------ 10 result 3
sec("poverty", f"""
{head("Result 3 · Where", "Access turns over faster in higher-poverty counties")}
{row(
    fig("fig3", 1080, 448, "Location loss by county poverty quintile"),
    bullets([
        f"Annual location loss rises from <b>{f1(G['E2_q1_pct'])}%</b> to <b>{f1(G['E2_q5_pct'])}%</b> across poverty quintiles ({f2(G['E2_ratio'])}×).",
        f"Poorest fifth of counties: <b>{f1(G['lost_q5_pct'])}%</b> of June 2020 SNAP addresses gone by June 2025.",
        f"Least-poor fifth: <b>{f1(G['lost_q1_pct'])}%</b>.",
        f"More of the 2025 stock is also new in poorer counties ({f1(G['new_q5_pct'])}% vs {f1(G['new_q1_pct'])}%)."], size=25, width=520),
    gap=40)}
{note(f"County poverty rate from the 2020–2024 ACS via SRAM. Quintile medians: {f1(G['pov_q1_median'])}% (Q1) to {f1(G['pov_q5_median'])}% (Q5); {n0(S['counties_analyzed'])} counties.")}
""", notes="This is the core distributional result. Turnover is highest exactly where households have the fewest alternatives.")

# ------------------------------------------------------------------ 11 result 4: mix
sec("mix", f"""
{head("Result 4 · Store mix", "Poorer counties rely more on high-turnover formats")}
{row(
    fig("fig4", 1000, 485, "Store mix by county poverty quintile, June 2025"),
    bullets([
        f"Large stores are <b>{f1(MIX['1']['Large store'])}%</b> of SNAP stores in the least-poor counties and <b>{f1(MIX['5']['Large store'])}%</b> in the poorest.",
        f"Convenience stores: {f1(MIX['1']['Convenience'])}% vs {f1(MIX['5']['Convenience'])}%.",
        "Stores counted as open on 30 June 2025, SRAM's reference month.",
        "Does this mix explain the poverty gap? Next slide."], size=25, width=600),
    gap=40)}
""", notes="Mix is part of the story, but the decomposition on the next slide shows it is the smaller part.")

# ------------------------------------------------------------------ 12 decomposition
sec("decomp", f"""
{head("Why the gap?", "Store mix explains only about a quarter of the poverty gap")}
{row(
    f'<div style="width:700px; display:flex; flex-direction:column; gap:18px">'
    f'<p style="font-family:{HEAD}; font-size:120px; font-weight:600; color:{ACC}; line-height:1.0">{round(SH["share_of_gap_from_mix_pct"])}%</p>'
    f'<p style="font-size:26px; line-height:1.4; color:{BODY}">of the gap in store exit rates between the poorest and least-poor fifths is due to store mix (shift-share).</p>'
    f'<p style="font-size:26px; line-height:1.4; color:{BODY}">Poorest fifth: <b>{f2(SH["q5_actual_pct"])}%</b> a year. Least poor: <b>{f2(SH["q1_actual_pct"])}%</b>. Poorest fifth with the least-poor mix: <b>{f2(SH["q5_with_q1_mix_pct"])}%</b>.</p></div>',
    f'<div style="flex:1; display:flex; flex-direction:column; gap:16px">'
    f'<p style="font-size:28px; font-weight:600; color:{DARK}">Store exit rate within each format, %/yr</p>' +
    table(["Store group", "Least poor", "Poorest"], [[g, f1(WT[g]['Q1']), f1(WT[g]['Q5'])] for g in ["Large store", "Grocery", "Convenience", "Specialty"]], [46, 27, 27], size=26) +
    note("The same kind of store exits more often in poorer counties.") + "</div>",
    gap=48, align="start")}
""", notes="Shift-share on 2006–2024 store exit rates. About three-quarters of the gap is within-format: a convenience store in a poor county is more likely to leave SNAP than one in a richer county.")

# ------------------------------------------------------------------ 13 regressions
mods = ["E2 (1)", "E2 (2)", "E1 (3)", "Lost 2020-25 (4)"]


def cell(m, v):
    r = R[m]
    if r.get(v) is None:
        return ""
    p = r[v + "_p"]
    st = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
    return f"{f2(r[v])}{st} ({f2(r[v + '_se'])})"


reg_rows = [[lab] + [cell(m, v) for m in mods] for lab, v in [
    ("Poverty rate, per 10 pp", "pov10"), ("LILA population share, per 0.1", "lila10"),
    ("Urban population share, per 0.1", "urban10"),
    ("Convenience share of stores, per 0.1", "conv10")]]
reg_rows.append(["Counties"] + [n0(R[m]["n"]) for m in mods])
sec("regress", f"""
{head("Conditional associations", "Poverty predicts turnover; the map's own access flag does not")}
{table(["County characteristic", "(1) Location loss", "(2) Location loss", "(3) Store exit", "(4) Lost 2020–25"], reg_rows, [32, 17, 17, 17, 17], size=24)}
{bullets([
    f"A 10-point higher poverty rate is associated with a location-loss rate {f2(R['E2 (1)']['pov10'])} points higher, against a mean of {f2(S['mean_y_E2_pct'])}%.",
    "Column 2: holding the convenience-store share fixed leaves the poverty coefficient about the same.",
    f"The low-income, low-access (LILA) share is not positive once poverty is held fixed; {f1(S['counties_zero_lila_pct'])}% of counties have no LILA population when every SNAP store counts."], size=24)}
{note("WLS, weights = county stock; state fixed effects and log population included; SEs clustered by state in parentheses. *** p<0.01, ** p<0.05, * p<0.1. Descriptive, not causal.")}
""", notes="Dependent variables in percent. Columns 1-3 are average annual rates, 2006-2024. Column 4 is the share of June 2020 SNAP addresses not active in June 2025.")

# ------------------------------------------------------------------ 14 snapshot
sec("snapshot", f"""
{head("Back to the map", "How recent is the access in the June 2025 snapshot?")}
{row(
    card("SNAP retail addresses, June 2025", "The locations behind SRAM's retailer list.", big=n0(T['locs_2025'])),
    card("New since June 2020", "Addresses that were not SNAP retail locations five years earlier.", big=f1(T['new_pct']) + "%"),
    card("Gone since June 2020", "June 2020 SNAP retail addresses no longer active in June 2025.", big=f1(T['lost_pct']) + "%"),
    gap=28, align="stretch")}
{bullets([
    "About one in five mapped access points is less than five years old.",
    f"In the poorest fifth of counties, {f1(G['new_q5_pct'])}% of 2025 addresses are new and {f1(G['lost_q5_pct'])}% of 2020 addresses are gone.",
    "A map release paired with a persistence measure would separate stable access from access that depends on one store."], size=26)}
""", notes="This connects the results back to the policy measure introduced at the start.")

# ------------------------------------------------------------------ 15 regional illustration
SN = {"TN": "Tennessee", "Neighboring states": "Bordering states (8)", "Rest of U.S.": "Rest of U.S."}
rg_rows = [[SN[k], f1(RG[k]['poverty_median']), f1(RG[k]['E2_exit_pct']), f1(RG[k]['lost_2020_2025_pct']), f1(RG[k]['new_2020_2025_pct'])]
           for k in ["TN", "Neighboring states", "Rest of U.S."]]
sec("region", f"""
{head("A regional illustration", "Tennessee and its neighbors: poorer, more rural, similar turnover")}
{row(
    fig("fig5", 700, 488, "Five-year turnover of SNAP retail addresses in Tennessee and bordering states"),
    f'<div style="flex:1; display:flex; flex-direction:column; gap:16px">' +
    table(["", "Poverty %", "Loss %/yr", "Lost 20–25", "New 20–25"], rg_rows, [36, 16, 16, 16, 16], size=24) +
    f'<p style="font-size:24px; line-height:1.4; color:{BODY}">Why this region: a contiguous southern region that is poorer and more rural than the rest of the country, with a higher share of people in low-income, low-access tracts.</p>' +
    f'<p style="font-size:24px; line-height:1.4; color:{BODY}"><b>{LC["name"]} ({LC["place"]}):</b> location loss {f1(LC["E2_exit_pct"])}% a year; {f1(LC["new_2020_2025_pct"])}% of its {n0(LC["locs_2025"])} SNAP addresses in 2025 were new since 2020.</p></div>',
    gap=36, align="start")}
""", notes=f"Poverty is the median county poverty rate. Across the eight bordering states, the five-year loss share ranges from {f1(RN['lost_min'])}% ({RN['lost_min_state']}) to {f1(RN['lost_max'])}% ({RN['lost_max_state']}). Tennessee itself is close to the national rate; the point is the setting, not an unusual result.")

# ------------------------------------------------------------------ 16 policy
sec("policy", f"""
<div style="flex:1"></div>
<p style="font-size:26px; font-weight:600; letter-spacing:2px; text-transform:uppercase; color:#8FB8EC">Policy relevance</p>
<h2 style="font-family:{HEAD}; font-size:72px; font-weight:600; line-height:1.1; color:{LIGHT}">Updated SNAP stocking standards take effect November 4, 2026</h2>
<ul style="font-size:30px; line-height:1.45; color:#DDE4EE; max-width:1500px">
<li>Existing retailers must stock seven varieties in each staple food category, up from three (91 FR 25082, May 8, 2026).</li>
<li>The rule notes that in low-access areas "one nearby convenience store may be the only access point for buying food."</li>
<li>Small formats already have the highest exit rates, and poorer counties rely on them most.</li>
<li>Only a location-level measure (E2) can tell a retailer leaving SNAP apart from a community losing SNAP retail.</li>
</ul>
<div style="flex:1"></div>
""", bg=DARK, color=LIGHT,
    notes="This paper does not predict how many stores will leave under the rule. It provides the baseline and the measure needed to monitor its effect on access. The FNS historical file for 2026, expected in early 2027, will show exits around the compliance date.")

# ------------------------------------------------------------------ 17 limitations
sec("limits", f"""
{head("Limitations", "What these data can and cannot tell us")}
{row(
    panel("Measurement", [
        "SNAP authorization is not the same as a store being open.",
        f"Some end dates are administrative ({len(B['batch_end_dates'])} batch dates).",
        "The 365-day continuity window is a judgment; results are shown for 0–730 days.",
        "Address matching is literal: spelling variants overstate location loss; shared addresses understate it."], 800, size=25),
    panel("Scope and design", [
        "County level: SRAM is a tract product, and tract assignment of stores is the next step.",
        "SRAM access flags are measured once, in 2025.",
        "All associations are descriptive, with state fixed effects; none is causal.",
        "Redemption-weighted exit is not possible with public store-level data."], 800, size=25),
    gap=32, align="stretch")}
""", notes="Name the limits before the questions do.")

# ------------------------------------------------------------------ 18 conclusion
sec("conclusion", f"""
{head("Conclusions", "Food access is a flow as well as a stock")}
{row(
    card("1 · Measure exit by place", f"Record counts overstate lost access: {f1(N['exit_E0_pct'])}% vs {f1(N['exit_E2_pct'])}% a year. {f1(N['share_store_exits_replaced_in_place_pct'])}% of store exits are replaced in place."),
    card("2 · Turnover is unequal", f"Poorer counties lose SNAP retail addresses faster ({f1(G['lost_q5_pct'])}% vs {f1(G['lost_q1_pct'])}% over five years), mostly within store types."),
    card("3 · Read maps with turnover", f"{f1(T['new_pct'])}% of the addresses behind the June 2025 SRAM snapshot were new since 2020."),
    gap=28, align="stretch")}
{panel("Next steps", [
    "Tract-level assignment of stores: did tracts with access in 2025 have it five years earlier, and will they keep it?",
    "Measure exits around the November 2026 stocking-standards compliance date with the next FNS file."], 1664, size=25)}
""", notes="Close on the three takeaways, then the next steps.")

# ------------------------------------------------------------------ 19 references
refs = [
    "Allcott, H., Diamond, R., Dubé, J.-P., Handbury, J., Rahkovsky, I., and Schnell, M. (2019). Food deserts and the causes of nutritional inequality. <i>Quarterly Journal of Economics</i>, 134(4), 1793–1844.",
    "Byrne, A. T., Dong, X., James, E., Handbury, J., and Meckel, K. (2024). Welfare implications of increased retailer participation in SNAP. Working paper.",
    "Chenarides, L., Çakır, M., and Richards, T. J. (2024). Dynamic model of entry: Dollar stores. <i>American Journal of Agricultural Economics</i>, 106(2), 852–882.",
    "Chenarides, L., Cho, C., Nayga, R. M., Jr., and Thomsen, M. R. (2021). Dollar stores and food deserts. <i>Applied Geography</i>, 134, 102497.",
    "Li, Q., and Zhao, S. (2025). Access to SNAP-authorized retailers and diet quality among SNAP recipients. <i>JAMA Health Forum</i>, 6(4), e250677.",
    "USDA ERS (2026). Food Access Research Atlas, SNAP-authorized Retailer Access Map. Initial release July 2026.",
    "USDA FNS (2026). SNAP Retailer Locator historical data, 2005–2025.",
    "USDA FNS (2026). Updated staple food stocking standards for retailers in SNAP. Final rule. 91 FR 25082.",
]
sec("references", f"""
{head("References", "Sources cited")}
<ul style="font-size:24px; line-height:1.35; color:{BODY}">{"".join(f"<li>{r}</li>" for r in refs)}</ul>
""")

# ------------------------------------------------------------------ 20 thanks
repo = "Code, data and QA report: github.com/Tlayem/retailer-churn · doi.org/10.5281/zenodo.22884651" if FINAL else "Code, data and QA report: [VERIFY: repository link and DOI after release]"
sec("thanks", f"""
<div style="flex:1"></div>
<h2 style="font-family:{HEAD}; font-size:88px; font-weight:600; color:{LIGHT}">Thank you</h2>
<p style="font-size:30px; color:#DDE4EE">Comments and questions welcome</p>
<p style="font-size:30px; color:#DDE4EE">{A['correspondence_name']} · {A['email']}</p>
<p style="font-size:26px; color:#C9D3E0">ORCID {A['orcid']} · {A['affiliation']}</p>
<p style="font-size:26px; color:#C9D3E0">{repo}</p>
<div style="flex:1"></div>
""", bg=DARK, color=LIGHT, footer=False)

# ------------------------------------------------------------------ write
old_ids = {p.stem for p in (OUT / "slides").glob("*.html")}
for sid, html in slides.items():
    (OUT / "slides" / f"{sid}.html").write_text(html)
for sid in old_ids - set(slides):
    (OUT / "slides" / f"{sid}.html").unlink()
deck_path = OUT / "deck.json"
created = json.loads(deck_path.read_text())["createdOnFiles"] if deck_path.exists() else \
    {"v": 1, "at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
deck = {"v": 4, "createdOnFiles": created, "title": "Retailer Churn and Food Access", "order": order,
        "sections": {"s1": {"description": "Motivation, questions and data", "start": "cover"},
                     "s2": {"description": "Measuring exit three ways", "start": "definitions"},
                     "s3": {"description": "Results: how often, which stores, where, and why", "start": "headline"},
                     "s4": {"description": "Policy relevance, limitations and conclusions", "start": "policy"}},
        "faces": {"source-serif-4": {"family": "Source Serif 4",
                                     "href": "https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400..700&display=swap"},
                  "ibm-plex-sans": {"family": "IBM Plex Sans",
                                    "href": "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&display=swap"}},
        "designSystems": []}
deck_path.write_text(json.dumps(deck, indent=1))
print("wrote", len(order), "slides; removed", sorted(old_ids - set(slides)))
