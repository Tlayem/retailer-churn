# Codebook

All files are written by `code/02_build.py` or `code/04_analysis.py`. Sources: FNS = USDA FNS SNAP
Retailer Locator historical data 2005–2025; SRAM = USDA ERS 2025 SNAP-authorized Retailer Access Map.
Dates are ISO (YYYY-MM-DD). An empty `end` means the spell was open on 31 Dec 2025 (or ran past the file).

## store_spells.csv.gz — one row per store spell (definition E1)

| column | definition | source / transformation |
|---|---|---|
| rid | FNS Record ID | FNS `Record ID` |
| start | first authorization date in the spell | min of merged `Authorization Date`s |
| end | last end date in the spell; empty if open | max of merged `End Date`s |
| n_records | authorization records merged into the spell | records of the same rid whose gap to the running end is ≤ 365 days |
| store_type | FNS store type | FNS `Store Type` (constant within rid; QA-checked) |
| group | Large store / Grocery / Convenience / Specialty / Other | mapping in `02_build.py` `GROUP` |
| st | state postal code | FNS `State` |
| fips | 2020 county FIPS | county name match to SRAM, else ZIP imputation; empty for 68 Alaska records |
| loc | address key | `street number|standardized street name|ZIP5`; `RID|<rid>` when no street address |
| end_on_batch_date | spell ended on a date shared by ≥ 1,000 FNS records nationally | flag |

## location_spells.csv.gz — one row per address spell (definition E2)

| column | definition |
|---|---|
| loc | address key (as above) |
| start / end | first authorization / last end of any SNAP store at the address, merging gaps ≤ 365 days |
| n_records | FNS records merged into the spell |
| st, fips | state and county of the address's most recent record |
| ever_large | the address hosted a Large store at some point |

## national_year.csv — national stock and flows

| column | definition |
|---|---|
| year | 2006–2024 |
| definition | `E0 record`, `E1 store`, `E2 location` |
| group | `All` or a store group (E0, E1 only) |
| stock_jan1 | spells active on 1 January (start < 1 Jan ≤ end) |
| entries / exits | spells starting / ending during the year |
| entry_rate / exit_rate | entries / stock_jan1, exits / stock_jan1 |

## county_year.csv — same as above by county (`fips`), E1 and E2, all store groups

## county_period.csv — one row per county (3,143 SRAM counties)

SRAM aggregates (tracts weighted by 2020 population, `POP2020`):

| column | definition |
|---|---|
| state, county20, county24, st | names from SRAM; `st` = postal code |
| pop2020 | 2020 Census population |
| lila_pop_share | share of population in tracts flagged low-income and low-access at 1 mile (urban) / 10 miles (rural), straight-line distance (`SD_SRAM_LILATracts_1And10`) |
| lila_pop_share_drive | the same with driving distance (`DD_SRAM_LILATracts_1And10`) |
| low_access_pop_share | population beyond 1 mile (urban tracts) or 10 miles (rural tracts) of a SNAP store / pop2020 (`SD_SRAM_lapop1`, `SD_SRAM_lapop10`) |
| lowinc_pop_share | share of population in low-income tracts (`LowIncomeTracts`) |
| urban_pop_share | share of population in urban tracts (`Urban`) |
| poverty_rate | population-weighted tract poverty rate, % (`PovertyRate`, ACS 2020–2024) |
| snap_hh_share | SNAP households / occupied housing units (`TractSNAP` / `OHU2020`) |
| no_vehicle_hh_share | households without a vehicle / occupied housing units (`TractHUNV` / `OHU2020`) |
| n_tracts, n_lila_tracts | tract counts |

Turnover (pooled 2006–2024; suffix E1 = stores, E2 = locations):

| column | definition |
|---|---|
| stock_jan1_E* | sum over years of 1 January stock (store-years or address-years) |
| exits_E*, entries_E* | sum over years |
| exit_rate_E*, entry_rate_E* | exits / stock, entries / stock — average annual rate |
| locs_2020, locs_2025 | SNAP retail addresses active on 30 Jun 2020 and 30 Jun 2025 (SRAM reference month) |
| new_since_2020 | active 30 Jun 2025, not active 30 Jun 2020 |
| lost_since_2020 | active 30 Jun 2020, not active 30 Jun 2025 |
| share_2025_new, share_2020_lost | the two above over locs_2025 and locs_2020 |

## county_analysis.csv — county_period plus analysis variables

`pov_q` county poverty quintile (1 = lowest); `conv_share_2025`, `large_share_2025` shares of stores open
30 Jun 2025 that are Convenience / Large store; regression variables `pov10` (poverty/10), `lila10`,
`urban10` (shares × 10), `log_pop`, `conv10`, and dependent variables `y_E1`, `y_E2`, `y_lost` in percent.

## location_turnover_2020_2025.csv.gz — addresses active on either date

`loc`, `now` (active 30 Jun 2025), `then` (active 30 Jun 2020), `st`, `fips`, `ever_large`.

## paper/stats.json

Every number quoted in the paper, abstract and slides. `build` repeats `build_log.json`.
