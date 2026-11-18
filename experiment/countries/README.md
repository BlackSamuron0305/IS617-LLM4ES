# Country lists

Two lists of nationalities that the experiment puts into the visa application.

| File | What it holds |
|---|---|
| `applicant_nationalities.csv` | The 22 Arab League nationalities plus 7 placebo nationalities, one per continent. Wealth comes from the World Bank. |
| `conflict_nationalities.csv` | Conflict countries only: every country the ACLED Conflict Index rates *extreme* or *high*. 7 are Arab League members and 23 are reference countries. |

## Wealth: World Bank income groups

Used in `applicant_nationalities.csv` (`wb_income_group`, `wealth_group`).

- **Source:** the World Bank country classifications by income level for fiscal year 2027. They took effect on 1 July 2026 and apply until 30 June 2027.
  - Thresholds: <https://datahelpdesk.worldbank.org/knowledgebase/articles/906519-world-bank-country-and-lending-groups>
  - Each country's group (the `incomeLevel` field): <https://api.worldbank.org/v2/country?format=json&per_page=400>
- **Scale:** a country's group depends on its gross national income per person in 2025, calculated with the World Bank Atlas method, in US dollars.

| World Bank group | Income per person (2025) | Our `wealth_group` |
|---|---|---|
| Low income | $1,175 or less | poor |
| Lower middle income | $1,176 to $4,635 | normal |
| Upper middle income | $4,636 to $14,375 | normal |
| High income | more than $14,375 | rich |

We merge the two middle groups into one "normal" group, so the comparison is poor against normal against rich.

- **Checked on 2026-11-18:** all 29 rows match the World Bank API. That API already shows the 2027 groups: for example, Jordan appears as upper middle income, a group it only entered in July 2026. The World Bank's name for Palestine is "West Bank and Gaza".

## Conflict: ACLED Conflict Index

Used in `conflict_nationalities.csv` (`acled_rank`, `acled_level`).

- **Source:** the ACLED Conflict Index, results of December 2025. ACLED (Armed Conflict Location & Event Data) is a public database of political violence and protest events.
  - Overview and method: <https://acleddata.com/series/acled-conflict-index> and <https://acleddata.com/general-guide/about-conflict-index>
  - Ranking table used here: <https://apps.acleddata.com/conflictindex2025/newindextable2025.csv>
- **Data period:** conflict events from 1 December 2024 to 28 November 2025.
- **Scale:** ACLED ranks every country on four measures:
  1. **Deadliness:** the number of people reported killed.
  2. **Danger:** the number of violent events aimed at civilians.
  3. **Diffusion:** how widely the violence is spread across the country (the share of populated 10 km x 10 km squares with at least 10 events in the year).
  4. **Fragmentation:** the number of armed groups and militias that are active.

  The overall rank is the average of the four ranks. The level follows from that rank:

| Level | Overall rank |
|---|---|
| Extreme | 1 to 10 |
| High | 11 to 30 |
| Turbulent | 31 to 50 |
| Low/Inactive | 51 and lower |

- **Our rule:** a country counts as a conflict country if ACLED rates it *extreme* or *high*. That gives 30 countries; we take all of them, with no selection by hand. ACLED counts all organised violence, including gang violence, which is why Mexico, Brazil, Ecuador and others are on the list. Libya is not on it: ACLED rates it *turbulent* (rank 35).
- **Checked on 2026-11-18:** all 30 rows match ACLED's table for rank and level, and the level boundaries above match the table (10 extreme, 20 high, 20 turbulent). Equal ranks (for example three countries at 11) are ACLED's own.

## Overlaps to keep in mind

- Jamaica (ACLED rank 28, high) and Papua New Guinea (on the World Bank's 2027 conflict list, not ranked by ACLED) are placebo countries in `applicant_nationalities.csv`.
