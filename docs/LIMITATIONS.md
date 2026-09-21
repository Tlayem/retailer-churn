# Limitations

1. **An authorization is not a store.** The source records SNAP authorization,
   not whether a business is open. A store can keep trading after leaving SNAP
   (withdrawal, disqualification, failure to reapply) and a closed store's
   authorization can linger until FNS removes it. Every "exit" in this project is
   an exit from SNAP retail, which is the relevant margin for SNAP households but
   not for all shoppers.

2. **End dates are partly administrative.** 52 end dates each carry 1,000 or more
   records nationally; about a quarter of store exits fall on them. These look like
   batch actions (for example, reauthorization non-response) and date when FNS
   recorded the exit, not when the store stopped trading. Annual rates are therefore
   lumpy; the county analysis pools 2006–2024 for that reason.

3. **The gap rule is a judgment.** A Record ID re-authorized within 365 days,
   and an address that hosts a new SNAP store within 365 days, are treated as
   continuous. The paper reports results at 0, 30, 180, 365 and 730 days. Exits in
   2025 are excluded because the year after them is not yet observed.

4. **Address matching is literal.** Locations are keyed on street number, a lightly
   standardized street name, and ZIP5. Inconsistent spelling of the same address
   splits one location into two and overstates location loss (E2 is an upper bound
   in that respect). Unit numbers are ignored, so two stores in one strip-mall
   address are one location, which understates loss. 4,215 records with no street
   address are keyed by Record ID.

5. **County, not tract.** Stores are assigned to 2020 counties by name (99.9%),
   with 426 records imputed from ZIP and 68 Alaska records unassigned. SRAM is a
   tract product; aggregating it to counties discards the within-county geography
   that defines food access. A tract version needs tract boundaries (not included).

6. **SRAM is measured once.** The access flags describe June 2025 stores and
   2020–2024 population. Using them to classify counties across 2006–2024 treats a
   2025 outcome as a fixed trait. 62.5% of counties have no population in a
   low-income, low-access tract under the 1-mile/10-mile straight-line definition,
   so the LILA measure has little variation at county level.

7. **Descriptive only.** Associations between poverty and turnover are
   conditional correlations with state fixed effects. They do not identify the
   effect of poverty, of store type, or of any policy on store survival.

8. **Coverage.** The file lists retailers authorized at any point in 2005–2025.
   Stores that left before 2005 are absent, so stock is complete from 1 January
   2006 onward but not before. 6,666 records carry a 1 January 1930 placeholder
   authorization date; they enter only as pre-period stock.

9. **Store type is one field per record** and can lag a change in format. The
   grouping of FNS store types into four groups is a judgment.
