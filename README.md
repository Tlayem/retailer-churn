# Retailer Churn and Food Access

**Version 0.1.0 — working paper, September 2026.**

Replication package for the working paper *Retailer Churn and Food Access* (Adesiyan, September 2026),
with the paper, a slide presentation, and every processed file needed to reproduce its numbers.

Food-access maps count the stores near people on one date. This project measures how often those stores
come and go. It turns USDA's 20-year file of SNAP-authorized retailers into store-level and address-level
spells, computes entry and exit three ways (record, store, location), and links the result to USDA's new
SNAP-authorized Retailer Access Map (SRAM, July 2026) at county level.

Headline results (from `paper/stats.json`): stores left SNAP at 8.8% a year in 2006–2024;
43.6% of those exits were followed by a new SNAP store at the
same address within a year; addresses lost all SNAP retail at 5.0% a year.

## Run it

Python 3.11 with pandas, numpy, matplotlib, statsmodels; Node 18+ with `docx`.

```
python code/01_fetch.py        # downloads (or checks hand-downloaded) inputs, logs SHA-256
python code/02_build.py        # spells and panels; optional arg = continuity window in days (default 365)
python code/03_qa.py           # writes data/processed/qa_report.txt; exits 1 on a failed check
python code/04_analysis.py     # figures, tables, paper/stats.json   (--final: publication versions)
node   code/05_document.js     # manuscript .docx + paper/abstract.txt (--final)
python code/06_slides.py       # talk slides as Slides-artifact files (--final)
python code/07_slides_pdf.py   # portable PDF of the slides, figures embedded (--final)
```

USDA hosts sometimes refuse automated downloads. If `01_fetch.py` stops, save the two files from the
landing pages below into `data/raw/` under the names it prints; the script then verifies their hashes.

## Sources

| Source | Vintage | Landing page |
|---|---|---|
| USDA FNS, SNAP Retailer Locator historical data 2005–2025 | current as of 31 Dec 2025; page updated 19 Feb 2026 | https://www.fna.usda.gov/snap/retailer-locator/data |
| USDA ERS, Food Access Research Atlas: 2025 SNAP-authorized Retailer Access Map data | initial release July 2026; updated 27 Jul 2026 | https://www.ers.usda.gov/data-products/food-access-research-atlas/download-the-data |

Both are U.S. government works in the public domain. Hashes: `data/raw/PROVENANCE.txt`.

## What is where

- `data/processed/` — `store_spells.csv.gz`, `location_spells.csv.gz`, `national_year.csv`, `county_year.csv`,
  `county_period.csv`, `county_analysis.csv`, `sram_county.csv`, `qa_report.txt`, `build_log.json`
- `paper/` — manuscript, `stats.json`, `abstract.txt`, `figures/`, `tables/`
- `slides/` — the talk as a PDF (`Retailer_Churn_Food_Access_slides*.pdf`); the slide source files are rebuilt by `06_slides.py`
- `docs/` — `CODEBOOK.md` (every column defined) and `LIMITATIONS.md`

`records_clean.csv.gz` (the cleaned record file, ~40 MB) is rebuilt by `02_build.py` and not committed.

## Limitations

See `docs/LIMITATIONS.md`. In short: authorization is not the same as a store being open, some end dates are
administrative batch dates, the continuity window is a judgment, and the analysis is at county level.

## License and citation

Code under [MIT](LICENSE). Data, figures, the paper and other documents under [CC BY 4.0](LICENSE-DATA),
with attribution to USDA FNS and ERS as sources. Cite as in `CITATION.cff`: Adesiyan, T. F. (2026). *Retailer Churn and Food Access* (Version 0.1.0).

Maintainer: Taiwo Adesiyan, Middle Tennessee State University · adesiyanfausiyat010@gmail.com · ORCID 0000-0002-2023-3624
