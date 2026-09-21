#!/usr/bin/env node
/* 05_document.js — build the manuscript (paper/Adesiyan_Retailer_Churn_Food_Access.docx)
   from paper/stats.json and AUTHORS.json. No number in the paper is typed by hand.
   Usage: node code/05_document.js [--final]                                          */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, AlignmentType,
  HeadingLevel, BorderStyle, ShadingType, Footer, PageNumber, LevelFormat,
} = require("docx");

const FINAL = process.argv.includes("--final");
const ROOT = path.resolve(__dirname, "..");
const S = JSON.parse(fs.readFileSync(path.join(ROOT, "paper", "stats.json")));
const A = JSON.parse(fs.readFileSync(path.join(ROOT, "AUTHORS.json"))).authors[0];
const f1 = (x) => Number(x).toFixed(1);
const f2 = (x) => Number(x).toFixed(2);
const f3 = (x) => Number(x).toFixed(3);
const n0 = (x) => Number(x).toLocaleString("en-US");
const N = S.national, G = S.gradient, T = S.turnover_national, SH = S.shift_share_E1, B = S.build;
const R = Object.fromEntries(S.regressions.map((r) => [r.model, r]));
const RG = S.region, RN = S.region_neighbors_range, LC = S.local_county, WT = S.within_type_E1_exit_pct, TY = S.by_type_E1_exit_pct;
const SENS = Object.fromEntries(S.gap_sensitivity.map((r) => [r.gap_days, r]));
const MIX = S.mix_june2025_pct;
const replaced30 = 100 * (1 - SENS[30].E2_exit_pct / SENS[30].E1_exit_pct);

// ---------------------------------------------------------------- helpers
const FONT = "Times New Roman";
function runs(text, opts = {}) {
  // **bold** and *italic* markup
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), font: FONT, size: 24, ...opts }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, font: FONT, size: 24, ...opts }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, font: FONT, size: 24, ...opts }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), font: FONT, size: 24, ...opts }));
  return out;
}
const P = (text, o = {}) => new Paragraph({ children: runs(text, o.run || {}), spacing: { after: 160, line: 360 },
  alignment: o.align || AlignmentType.JUSTIFIED, indent: o.indent, ...(o.p || {}) });
const H1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 280, after: 140 },
  children: [new TextRun({ text, bold: true, font: FONT, size: 26 })] });
const H2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 100 },
  children: [new TextRun({ text, bold: true, italics: true, font: FONT, size: 24 })] });
const small = (text) => new Paragraph({ children: runs(text, { size: 20 }), spacing: { after: 200 },
  alignment: AlignmentType.LEFT });
function figure(file, caption, w = 600, h = 330) {
  const img = fs.readFileSync(path.join(ROOT, "paper", "figures", file));
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 },
      children: [new ImageRun({ type: "png", data: img, transformation: { width: w, height: h } })] }),
    small(caption),
  ];
}
const border = { style: BorderStyle.SINGLE, size: 4, color: "999999" };
const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
function table(header, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (t, i, head) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    borders: { top: head ? border : none, bottom: head ? border : none, left: none, right: none },
    shading: head ? { type: ShadingType.CLEAR, fill: "F2F2F2", color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({ alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT,
      children: [new TextRun({ text: String(t), font: FONT, size: 19, bold: !!head })] })],
  });
  const last = rows.length - 1;
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: header.map((t, i) => cell(t, i, true)) }),
      ...rows.map((r, ri) => new TableRow({ children: r.map((t, i) => {
        const c = cell(t, i, false);
        if (ri === last) c.options = c.options; // keep
        return c;
      }) }))],
  });
}
const star = (p) => (p < 0.01 ? "***" : p < 0.05 ? "**" : p < 0.1 ? "*" : "");
const coef = (r, v) => (r[v] === null || r[v] === undefined || Number.isNaN(r[v]) ? "" : `${f3(r[v])}${star(r[v + "_p"])}`);
const se = (r, v) => (r[v] === null || r[v] === undefined || Number.isNaN(r[v]) ? "" : `(${f3(r[v + "_se"])})`);

// ---------------------------------------------------------------- content
const body = [];
if (!FINAL) {
  body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
    children: [new TextRun({ text: "DRAFT — not verified by the author. Do not cite or circulate.", bold: true,
      color: "C00000", font: FONT, size: 22 })] }));
}
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
  children: [new TextRun({ text: "Retailer Churn and Food Access", bold: true, font: FONT, size: 34 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
  children: [new TextRun({ text: A.name, font: FONT, size: 24 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
  children: [new TextRun({ text: A.affiliation, font: FONT, size: 22 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
  children: [new TextRun({ text: `${A.email}  ·  ORCID ${A.orcid}`, font: FONT, size: 20 })] }));
body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [new TextRun({ text: "Working paper · September 2026", italics: true, font: FONT, size: 20 })] }));

const abstract = `Food-access maps record which stores are near people on one date. This paper asks how stable that access is. Using USDA's historical file of every SNAP-authorized retailer from 2005 to 2025 (${n0(B.records_kept)} authorization records in the 50 states and the District of Columbia), I build three measures of retailer exit: the end of an authorization record, the exit of a store, and the loss of all SNAP retail at an address. Stores left SNAP at an average annual rate of ${f1(N.exit_E1_pct)} percent between 2006 and 2024, but ${f1(N.share_store_exits_replaced_in_place_pct)} percent of those exits were followed by a new SNAP store at the same address within a year, and the rate at which addresses lost all SNAP retail was ${f1(N.exit_E2_pct)} percent. Turnover rises with county poverty: in the highest-poverty fifth of counties, ${f1(G.lost_q5_pct)} percent of June 2020 SNAP retail addresses were gone by June 2025, against ${f1(G.lost_q1_pct)} percent in the lowest-poverty fifth. Differences in store mix explain about ${Math.round(SH.share_of_gap_from_mix_pct)} percent of the poverty gap in store exit rates; the rest is higher exit within each store type. Linking the panel to USDA's new SNAP-authorized Retailer Access Map (July 2026) shows that ${f1(T.new_pct)} percent of the store addresses behind its June 2025 snapshot were not SNAP retail addresses five years earlier. Static access measures should be read alongside the turnover of the stores that produce them, especially as updated SNAP stocking standards take effect on November 4, 2026.`;
fs.writeFileSync(path.join(ROOT, "paper", "abstract.txt"), (FINAL ? "" : "DRAFT — not verified\n\n") + "Retailer Churn and Food Access\n" + A.name + ", " + A.affiliation + "\n\n" + abstract + "\n\nWords: " + abstract.split(/\s+/).length + "\n");
body.push(H1("Abstract"));
body.push(P(abstract));
body.push(P("**Keywords:** food access; SNAP; retail entry and exit; convenience stores; food deserts; administrative data", { align: AlignmentType.LEFT }));
body.push(P("**JEL codes:** I38, L81, Q18, R12", { align: AlignmentType.LEFT }));

// 1 Introduction
body.push(H1("1. Introduction"));
body.push(P(`Access to food retail is a central concern of U.S. nutrition policy. It is usually measured spatially, as the share of a population living beyond a fixed distance from a food store: one mile in urban areas and ten miles in rural areas, under the conventions of the U.S. Department of Agriculture's Food Access Research Atlas. For more than a decade the Atlas defined a food store as a supermarket, supercenter, or large grocery store. In July 2026 the Economic Research Service (ERS) released a companion measure, the SNAP-authorized Retailer Access Map (SRAM). SRAM calculates distance to every retailer authorized to accept Supplemental Nutrition Assistance Program (SNAP) benefits, from supercenters to convenience stores, using the population of authorized retailers as of June 2025 (USDA ERS 2026). By defining access in terms of the stores at which program benefits can be redeemed, SRAM aligns measurement more closely with where SNAP households shop.`));
body.push(P(`Like the measures that preceded it, however, SRAM is cross-sectional. It records which stores were within reach of each census tract at a single point in time and is silent on how long that configuration persists. This limitation matters most for the retail formats SRAM newly incorporates. Small-format retailers are numerous but economically marginal within the program: in fiscal year 2024 convenience stores made up 44 percent of SNAP-authorized retailers but accounted for only 5 percent of SNAP redemptions (USDA FNS 2026b). The small-format segment is also competitively unstable. Chenarides, Çakır, and Richards (2024) find that the expansion of dollar stores is associated with the exit of other small-format stores rather than of grocery stores. If the stores that bring a tract within the access threshold enter and exit frequently, a single-date measure will overstate the reliability of access, and the overstatement will be largest where access depends on small stores.`));
body.push(P(`The existing literature offers limited evidence on this dimension of food access. Most studies of the retail food environment treat store presence as a static characteristic of place, relating it to purchasing, diet, or the location decisions of particular formats (Allcott et al. 2019; Chenarides et al. 2021; Li and Zhao 2025). Research that exploits changes in the retailer stock, such as Byrne et al. (2024) on the 2008–2012 expansion of SNAP retail participation, shows that the stock moves enough to change household shopping costs, but it does not characterize the ongoing rate of retailer turnover or its distribution across places. Measuring turnover also raises a problem that has received little attention: in administrative data, the end of a retailer's authorization record need not coincide with the loss of a store. Records end when owners change, when authorizations lapse briefly and are restored, and, as the data suggest, when large numbers of records are closed on a single administrative date.`));
body.push(P(`This paper addresses both gaps using the historical extract of the Food and Nutrition Service's (FNS) Store Tracking and Redemption System, which records the authorization and end dates of every retailer that accepted SNAP benefits at any point between 2005 and 2025. I make three contributions. First, I propose and implement three nested definitions of retailer exit: the end of an authorization record; the exit of a store, which merges authorization spells of the same retailer interrupted by less than one year; and the loss of SNAP retail at a location, which treats the replacement of one store by another at the same address as continuity. Second, I document the level, composition, and geography of retailer turnover from 2006 to 2024 and relate it to county poverty and to the access classifications in SRAM. Third, I link the retailer panel to the SRAM reference date to measure how much of the access recorded in June 2025 was recently established.`));
body.push(P(`The findings indicate that the choice of exit definition is consequential. The average annual store exit rate over 2006–2024 is ${f1(N.exit_E1_pct)} percent, but ${f1(N.share_store_exits_replaced_in_place_pct)} percent of store exits are followed within a year by a new SNAP-authorized store at the same address, and the annual rate at which locations lose all SNAP retail is ${f1(N.exit_E2_pct)} percent. Turnover is concentrated in small formats and rises with county poverty. In the highest-poverty quintile of counties, ${f1(G.lost_q5_pct)} percent of SNAP retail locations active in June 2020 were no longer active in June 2025, compared with ${f1(G.lost_q1_pct)} percent in the lowest-poverty quintile. Differences in store mix account for only about ${Math.round(SH.share_of_gap_from_mix_pct)} percent of the corresponding gap in store exit rates; the remainder reflects higher exit rates within each store format. Nationally, ${f1(T.new_pct)} percent of the SNAP retail locations underlying the June 2025 SRAM snapshot had not been SNAP retail locations five years earlier.`));
body.push(P(`These results bear directly on current policy. Updated SNAP staple food stocking standards, which raise the required variety of staple foods, take effect for existing retailers on November 4, 2026 (USDA FNS 2026b). Assessing their consequences for food access will require distinguishing a retailer's departure from the program from a community's loss of SNAP retail, which is the distinction this paper formalizes. The remainder of the paper is organized as follows. Section 2 describes the data. Section 3 defines the exit measures. Section 4 presents the results, Section 5 discusses their implications, Section 6 sets out the limitations, and Section 7 concludes.`));

// 2 Data
body.push(H1("2. Data"));
body.push(P(`**SNAP retailers.** The USDA Food and Nutrition Service publishes a historical extract of its Store Tracking and Redemption System covering every retailer authorized at any point in the previous twenty calendar years (USDA FNS 2026a). The version used here is current as of December 31, 2025 and contains ${n0(B.records_raw)} records with a record identifier, store name and type, street address, county, coordinates, and authorization and end dates. A record with no end date was authorized at the end of 2025. I drop ${n0(B.records_dropped_farmers_market_delivery_route)} farmers market and delivery route records, which SRAM also excludes, ${n0(B.records_dropped_outside_50_states_dc)} records outside the 50 states and the District of Columbia, and ${n0(B.records_end_before_auth_dropped)} records whose end date precedes their authorization date, leaving ${n0(B.records_kept)} records for ${n0(B.record_ids)} record identifiers. Because the file covers every retailer authorized at any time since January 1, 2005, the stock of authorized stores, and entry and exit, are fully observed from 2006 onward, which sets the start of the analysis period.`));
body.push(P(`**Food access.** The 2025 SRAM data give, for each of ${n0(B.sram_tracts)} 2020 census tracts, population and housing counts from the 2020 Census, income and vehicle measures from the 2020–2024 American Community Survey, and low-access and low-income-low-access (LILA) flags computed with straight-line and driving distances to SNAP-authorized stores as of June 2025 (USDA ERS 2026). I aggregate tracts to ${n0(B.sram_counties)} counties, weighting by 2020 population. The tract populations sum to ${n0(B.sram_pop2020)}, the 2020 Census resident count.`));
body.push(P(`**Linking.** Retailers are assigned to 2020 counties by county name within state. ${f2(100 * B.county_match_rate)} percent of records match; ${n0(B.records_county_imputed_by_zip)} records, mostly in Connecticut, whose file uses its 2022 planning regions, are assigned the modal county of other records in the same ZIP code, and ${n0(B.records_county_unmatched)} records in pre-2019 Alaska census areas remain unassigned. The analysis sample has ${n0(S.counties_analyzed)} counties with at least one SNAP retailer.`));

// 3 Measurement
body.push(H1("3. Three definitions of exit"));
body.push(P(`The raw file overstates departures in two ways. First, the same record identifier can hold several authorization spells: ${n0(B.record_ids)} identifiers generate ${n0(B.records_kept)} records, and a store whose authorization lapses and is restored a few weeks later has not left. Second, when a store changes hands it usually receives a new record identifier, so the end of one store and the start of another at the same counter look like an exit and an entry. I therefore define exit three ways.`));
body.push(P(`**E0, record exit:** any authorization end date. **E1, store exit:** the end of a record identifier's authorization with no re-authorization of the same identifier within 365 days; spells separated by shorter gaps are merged. **E2, location loss:** the end of all SNAP retail at an address, defined by street number, standardized street name and five-digit ZIP code, with no SNAP store of any identifier authorized there within 365 days. Entry is defined symmetrically. For each definition, the annual exit rate is exits during the year divided by the stock on January 1. Because a 365-day window must be observable after each exit, exits are counted through 2024.`));
body.push(P(`The 365-day window is a judgment. Table 1 reports average exit rates for windows from zero to 730 days. Store exit is insensitive to the window, since re-authorization of the same identifier is uncommon. Location loss is sensitive, because much in-place replacement happens within a few months: with a 30-day window, ${f1(replaced30)} percent of store exits are replaced in place; with a 365-day window, ${f1(N.share_store_exits_replaced_in_place_pct)} percent are.`));
body.push(P(`One further feature of the file shapes interpretation. ${B.batch_end_dates.length} end dates are each shared by 1,000 or more records nationally, and ${f1(S.store_exits_on_batch_dates_pct)} percent of store exits fall on them. These are administrative batch actions. They date when FNS recorded an exit rather than when a store stopped trading, which makes annual rates lumpy, so the county analysis pools 2006–2024.`));
body.push(small("**Table 1.** Average annual exit rate (%), 2006–2024, by continuity window"));
body.push(table(["Window (days)", "Exit years", "Store exit (E1)", "Location loss (E2)"],
  S.gap_sensitivity.map((r) => [r.gap_days, r.exit_years, f2(r.E1_exit_pct), f2(r.E2_exit_pct)]), [2200, 2200, 2400, 2560]));
body.push(small("Note: the 730-day window counts exits through 2023, the last year with two years of follow-up."));

// 4 Results
body.push(H1("4. Results"));
body.push(H2("4.1 How often SNAP retailers exit"));
body.push(P(`The stock of SNAP-authorized stores grew from ${n0(N.stock_2006)} on January 1, 2006 to ${n0(N.stock_2024)} on January 1, 2024, with most of the growth during the 2008–2012 expansion; the store entry rate peaked at ${f1(N.peak_entry_E1_pct)} percent in ${N.peak_entry_year}. Against that stock, authorization records ended at an average annual rate of ${f1(N.exit_E0_pct)} percent, stores exited at ${f1(N.exit_E1_pct)} percent, and addresses lost all SNAP retail at ${f1(N.exit_E2_pct)} percent (Figure 1). In 2024 the rates were ${f1(N.exit_E1_2024_pct)} percent for stores and ${f1(N.exit_E2_2024_pct)} percent for addresses. Over 2006–2024 there were ${n0(N.store_exits_total)} store exits and ${n0(N.location_losses_total)} location losses: ${f1(N.share_store_exits_replaced_in_place_pct)} percent of store exits were followed by another SNAP store at the same address within a year.`));
body.push(...figure("fig1_exit_definitions.png", "**Figure 1.** Annual exit rates under three definitions, 2006–2024. Source: author's calculations from USDA FNS SNAP Retailer Locator historical data 2005–2025.", 600, 333));
body.push(P(`Measured by the definition that matters for access, the annual loss rate is ${Math.round(100 * N.exit_E2_pct / N.exit_E0_pct)} percent of the record-based rate. Counting record end dates as closures overstates the rate at which places lose SNAP retail by about ${Math.round(100 * (N.exit_E0_pct / N.exit_E2_pct - 1))} percent.`));

body.push(H2("4.2 Which stores exit"));
body.push(P(`Exit is concentrated in small formats (Figure 2). Large stores, meaning supermarkets, super stores and large grocery stores, exited at ${f1(TY["Large store"])} percent a year. Small, medium and combination grocery stores exited at ${f1(TY["Grocery"])} percent, convenience stores at ${f1(TY["Convenience"])} percent, and specialty stores at ${f1(TY["Specialty"])} percent. Convenience stores were ${f1(S.by_type_stock_share_pct["Convenience"])} percent of store-years, so they account for most exits.`));
body.push(...figure("fig2_store_type.png", "**Figure 2.** Average annual store exit rate (E1) by store group, 2006–2024.", 520, 276));

body.push(H2("4.3 Where access turns over"));
body.push(P(`I divide counties into quintiles of the 2020–2024 poverty rate. The median county poverty rate is ${f1(G.pov_q1_median)} percent in the lowest quintile and ${f1(G.pov_q5_median)} percent in the highest. The annual location-loss rate rises from ${f1(G.E2_q1_pct)} percent in the lowest-poverty quintile to ${f1(G.E2_q5_pct)} percent in the highest, a ratio of ${f2(G.E2_ratio)} (Figure 3). Over the five years before the SRAM snapshot the gap is wider in levels: ${f1(G.lost_q5_pct)} percent of the SNAP retail addresses active in the highest-poverty counties in June 2020 were not active in June 2025, compared with ${f1(G.lost_q1_pct)} percent in the lowest-poverty counties. More of the June 2025 stock was also new: ${f1(G.new_q5_pct)} percent against ${f1(G.new_q1_pct)} percent.`));
body.push(...figure("fig3_poverty_gradient.png", "**Figure 3.** Location loss by county poverty quintile. Left: average annual location-loss rate (E2), 2006–2024. Right: share of SNAP retail addresses active on June 30, 2020 that were not active on June 30, 2025. Quintile labels give the median county poverty rate.", 600, 249));
body.push(P(`Part of the gradient is composition. Large stores are ${f1(MIX["1"]["Large store"])} percent of SNAP stores open in June 2025 in the lowest-poverty quintile and ${f1(MIX["5"]["Large store"])} percent in the highest (Figure 4). A shift-share calculation shows how much this matters. The highest-poverty quintile's store exit rate is ${f2(SH.q5_actual_pct)} percent, against ${f2(SH.q1_actual_pct)} percent in the lowest. Giving the highest-poverty quintile the lowest quintile's store mix, while keeping its own type-specific exit rates, lowers its rate only to ${f2(SH.q5_with_q1_mix_pct)} percent. Composition therefore accounts for about ${Math.round(SH.share_of_gap_from_mix_pct)} percent of the gap. The remainder is higher exit within each format: convenience stores exit at ${f1(WT.Convenience.Q5)} percent a year in the highest-poverty counties against ${f1(WT.Convenience.Q1)} percent in the lowest, and small and medium grocery stores at ${f1(WT.Grocery.Q5)} against ${f1(WT.Grocery.Q1)} percent.`));
body.push(...figure("fig4_store_mix.png", "**Figure 4.** Composition of SNAP-authorized stores open on June 30, 2025, by county poverty quintile (median county poverty rate in parentheses).", 560, 272));

body.push(H2("4.4 Conditional associations"));
body.push(P(`Table 2 reports weighted least squares regressions of county turnover on the county poverty rate, the population share in SRAM low-income, low-access tracts, the urban population share, and log population, with state fixed effects and standard errors clustered by state. Weights are the county's stock of stores or addresses. Each ten-point increase in the poverty rate is associated with a location-loss rate ${f2(R["E2 (1)"].pov10)} percentage points higher (column 1), against a stock-weighted mean of ${f2(S.mean_y_E2_pct)} percent, and with ${f2(R["Lost 2020-25 (4)"].pov10)} points more of the June 2020 addresses gone by June 2025 (column 4). Column 2 adds the convenience-store share of each county's SNAP retailers in June 2025 as a control. The poverty coefficient remains positive, of similar size, and statistically significant, which indicates that the relationship between poverty and turnover is not explained by the greater prevalence of convenience stores in poorer counties. These estimates are conditional correlations.`));
body.push(P(`The LILA share itself is not associated with higher turnover once poverty is held fixed; its coefficients are small and negative. At county level this measure has little variation, since ${f1(S.counties_zero_lila_pct)} percent of counties have no population in a LILA tract when every SNAP retailer counts as a food store. Where access is scarce there are also fewer stores to lose. The places where access churns are poorer places with many small stores, not the places the static map flags.`));
body.push(small("**Table 2.** County turnover and county characteristics (WLS, state fixed effects)"));
const models = ["E2 (1)", "E2 (2)", "E1 (3)", "Lost 2020-25 (4)"];
const rowsT2 = [];
for (const [lab, v] of [["Poverty rate (per 10 pp)", "pov10"], ["LILA population share (per 0.1)", "lila10"],
  ["Urban population share (per 0.1)", "urban10"], ["Log population", "log_pop"], ["Convenience share of stores, 2025 (per 0.1)", "conv10"]]) {
  rowsT2.push([lab, ...models.map((m) => coef(R[m], v))]);
  rowsT2.push(["", ...models.map((m) => se(R[m], v))]);
}
rowsT2.push(["Counties", ...models.map((m) => n0(R[m].n))]);
rowsT2.push(["R²", ...models.map((m) => f3(R[m].r2))]);
body.push(table(["", "(1) Location loss", "(2) Location loss", "(3) Store exit", "(4) Lost 2020–25"], rowsT2, [3160, 1450, 1450, 1450, 1850]));
body.push(new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "Note: dependent variables in percent. Columns 1–3: average annual rates, 2006–2024. Column 4: share of June 2020 SNAP retail addresses not active in June 2025. Standard errors clustered by state in parentheses. *** p<0.01, ** p<0.05, * p<0.1.", font: FONT, size: 20 })] }));

body.push(H2("4.5 A regional illustration: Tennessee and its neighbors"));
const NBR = ["AL", "AR", "GA", "KY", "MS", "MO", "NC", "VA"];
const SN = { TN: "Tennessee", AL: "Alabama", AR: "Arkansas", GA: "Georgia", KY: "Kentucky", MS: "Mississippi", MO: "Missouri", NC: "North Carolina", VA: "Virginia" };
body.push(P(`As a regional illustration, this section examines a contiguous region of the southern United States: Tennessee and the eight states it borders (Alabama, Arkansas, Georgia, Kentucky, Mississippi, Missouri, North Carolina, and Virginia). The region is poorer and more rural than the rest of the country. The median county poverty rate is ${f1(RG.TN.poverty_median)} percent in Tennessee and ${f1(RG["Neighboring states"].poverty_median)} percent in the neighboring states, against ${f1(RG["Rest of U.S."].poverty_median)} percent elsewhere; ${f1(RG.TN.urban_pop_share_pct)} percent of Tennessee's population lives in urban tracts, against ${f1(RG["Rest of U.S."].urban_pop_share_pct)} percent outside the region; and ${f1(RG["Neighboring states"].lila_pop_share_pct)} percent of the neighboring states' population, and ${f1(RG.TN.lila_pop_share_pct)} percent of Tennessee's, lives in low-income, low-access tracts, against ${f1(RG["Rest of U.S."].lila_pop_share_pct)} percent elsewhere. ${S.tn_counties_top2_poverty_quintiles} of Tennessee's ${S.tn_counties} counties fall in the two highest national poverty quintiles. These are the conditions under which the national results suggest SNAP retail turnover matters most.`));
body.push(P(`Turnover in Tennessee itself is close to the national rate (Table 3, Figure 5). Its location-loss rate was ${f1(RG.TN.E2_exit_pct)} percent a year, against ${f1(RG["Rest of U.S."].E2_exit_pct)} percent outside the region, and ${f1(RG.TN.lost_2020_2025_pct)} percent of its June 2020 SNAP retail addresses were gone by June 2025. Turnover was higher across the neighboring states as a group (${f1(RG["Neighboring states"].lost_2020_2025_pct)} percent over five years), ranging from ${f1(RN.lost_min)} percent in ${RN.lost_min_state} to ${f1(RN.lost_max)} percent in ${RN.lost_max_state}. In ${LC.name}, which contains ${LC.place}, the location-loss rate was ${f1(LC.E2_exit_pct)} percent a year, and ${f1(LC.new_2020_2025_pct)} percent of its ${n0(LC.locs_2025)} SNAP retail addresses in June 2025 were new since June 2020, above the national share of ${f1(T.new_pct)} percent.`));
const rgRows = ["TN", ...NBR, "Neighboring states", "Rest of U.S.", "United States"].map((k) => {
  const r = RG[k];
  return [SN[k] || k, n0(r.counties), f1(r.poverty_median), f1(r.E2_exit_pct), f1(r.lost_2020_2025_pct), f1(r.new_2020_2025_pct), n0(r.locs_2025)];
});
body.push(small("**Table 3.** Turnover of SNAP retail in Tennessee and its bordering states"));
body.push(table(["", "Counties", "Median poverty %", "Location loss %/yr", "Lost 2020–25 %", "New 2020–25 %", "Addresses, June 2025"], rgRows,
  [1900, 950, 1200, 1300, 1200, 1200, 1410]));
body.push(small("Note: poverty is the median county poverty rate (ACS 2020–2024, via SRAM). Lost and new shares compare SNAP retail addresses active on June 30, 2020 and June 30, 2025."));
body.push(...figure("fig5_tennessee_region.png", "**Figure 5.** Five-year turnover of SNAP retail addresses in Tennessee and its bordering states, June 2020 to June 2025.", 520, 362));

// 5 Discussion
body.push(H1("5. Discussion"));
body.push(P(`Three implications follow. First, measures of retail exit built from SNAP authorization records should separate administrative and ownership changes from real departures. The difference is large: the record-based exit rate is ${f1(N.exit_E0_pct)} percent a year and the address-based rate ${f1(N.exit_E2_pct)} percent.`));
body.push(P(`Second, access maps built from all SNAP retailers describe a more volatile stock than those built from large stores. SRAM's June 2025 snapshot rests on ${n0(T.locs_2025)} SNAP retail addresses; ${f1(T.new_pct)} percent of them were not SNAP retail addresses in June 2020, and ${f1(T.lost_pct)} percent of June 2020 addresses had gone. Because turnover is highest in poorer counties and in the formats those counties rely on most, access that SRAM counts in a poorer county is more likely to rest on stores that are recent arrivals or that will not last. Pairing each release of the map with a measure of the persistence of its stores would let users tell stable access from access that depends on one convenience store's lease.`));
body.push(P(`Third, the findings are immediately relevant to current policy. USDA's updated staple food stocking standards for SNAP retailers take effect for existing retailers on November 4, 2026 (USDA FNS 2026b). The rule raises the required variety in each staple category from three to seven, and the Department notes that in low-access areas "one nearby convenience store may be the only access point for buying food." The results here do not predict how many stores will leave. They do identify where exits from small formats have historically been concentrated and show that only the location-level measure (E2) can distinguish a store leaving SNAP from a neighborhood losing SNAP retail. That is the measure that monitoring the rule's effect on access requires.`));

// 6 Limitations
body.push(H1("6. Limitations"));
body.push(P(`The source records SNAP authorization, not whether a business is open, and some end dates are administrative. The continuity window is a judgment, and address matching is literal: spelling variants of one address overstate location loss, while multiple stores at one street address understate it. The analysis is at county level because the tract assignment of stores requires boundary files not used here, and the SRAM access flags are measured once, in 2025.`));

// 7 Conclusion
body.push(H1("7. Conclusion"));
body.push(P(`Twenty years of SNAP retailer records show a stock of stores that turns over substantially but less than record counts suggest: about ${f1(N.exit_E2_pct)} percent of SNAP retail addresses go dark each year, and more than four in ten store exits are replaced in place within a year. Turnover is highest in poorer counties, and mostly because the same kinds of store exit more often there, not only because those counties rely on smaller stores. Food access is a flow as well as a stock. The next step is to move the analysis to census tracts, where it can show whether tracts classified as having access in 2025 kept it.`));

// Declarations
body.push(H1("Data and code availability"));
body.push(P(`All data used in this paper are publicly available from the U.S. Department of Agriculture (USDA FNS 2026a; USDA ERS 2026). The code and processed data needed to reproduce every table and figure are available at https://github.com/Tlayem/retailer-churn and archived on Zenodo; the DOI is listed in the repository.`, { align: AlignmentType.LEFT }));
// References
body.push(H1("References"));
const refs = [
  "Allcott, H., Diamond, R., Dubé, J.-P., Handbury, J., Rahkovsky, I., and Schnell, M. (2019). Food deserts and the causes of nutritional inequality. *Quarterly Journal of Economics*, 134(4), 1793–1844.",
  "Byrne, A. T., Dong, X., James, E., Handbury, J., and Meckel, K. (2024). Welfare implications of increased retailer participation in SNAP. Working paper, November 25, 2024.",
  "Chenarides, L., Çakır, M., and Richards, T. J. (2024). Dynamic model of entry: Dollar stores. *American Journal of Agricultural Economics*, 106(2), 852–882.",
  "Chenarides, L., Cho, C., Nayga, R. M., Jr., and Thomsen, M. R. (2021). Dollar stores and food deserts. *Applied Geography*, 134, 102497. https://doi.org/10.1016/j.apgeog.2021.102497",
  "Li, Q., and Zhao, S. (2025). Access to SNAP-authorized retailers and diet quality among SNAP recipients. *JAMA Health Forum*, 6(4), e250677. https://doi.org/10.1001/jamahealthforum.2025.0677",
  "U.S. Department of Agriculture, Economic Research Service (2026). Food Access Research Atlas, SNAP-authorized Retailer Access Map: data and documentation. Initial release July 2026. https://www.ers.usda.gov/data-products/food-access-research-atlas",
  "U.S. Department of Agriculture, Food and Nutrition Service (2026a). SNAP Retailer Locator historical data, 2005–2025. Data current as of December 31, 2025. https://www.fna.usda.gov/snap/retailer-locator/data",
  "U.S. Department of Agriculture, Food and Nutrition Service (2026b). Updated staple food stocking standards for retailers in the Supplemental Nutrition Assistance Program. Final rule. *Federal Register*, 91, 25082 (May 8, 2026).",
];
for (const r of refs) body.push(new Paragraph({ children: runs(r, { size: 22 }), spacing: { after: 120 },
  indent: { left: 480, hanging: 480 } }));

const doc = new Document({
  creator: A.name, title: "Retailer Churn and Food Access", description: "Working paper, September 2026",
  styles: { default: { document: { run: { font: FONT, size: 24 } } } },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 20 }),
        ...(FINAL ? [] : [new TextRun({ text: "   ·   DRAFT", font: FONT, size: 20, color: "C00000" })])] })] }) },
    children: body,
  }],
});
const out = path.join(ROOT, "paper", FINAL ? "Adesiyan_Retailer_Churn_Food_Access.docx" : "Adesiyan_Retailer_Churn_Food_Access_DRAFT.docx");
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log("wrote", out); });
