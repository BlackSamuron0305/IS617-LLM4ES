# Country lists

`nationalities.csv` holds every nationality the experiment puts into the visa application, one row per country (35 rows). The `lists` column says which list a country is on; a country can be on both (for example `applicant;conflict`).

| List | What it holds |
|---|---|
| `applicant` | The 22 Arab League nationalities plus 7 placebo nationalities from six continents (Maldives and Cambodia are both in Asia). Wealth comes from the World Bank. |
| `conflict` | Conflict countries only. Arab League members the ACLED Conflict Index rates *extreme* or *high* (7), and non-Arab countries it rates *extreme* (7: 6 reference countries plus the placebo country Ecuador). 14 countries. |

Every column is filled for every row, except `acled_rank` for countries outside ACLED's published top 60 (see below). `visa_required` means a Schengen visa is required, as listed in Regulation (EU) 2018/1806, Annex I (visa required) and Annex II (visa-free); `arab_identity_contested` is `false` for all non-Arab countries. Until 2026-11-18 these were two files, `applicant_nationalities.csv` and `conflict_nationalities.csv`; they are in the git history.

## Wealth: World Bank income groups

Columns `wb_income_group` and `wealth_group`, filled for all 35 countries (the 6 reference countries were added and checked against the API on 2026-11-18).

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

Columns `acled_rank` and `acled_level`. ACLED's public table ranks only its top 60 countries. Countries in it have both columns (Libya 35 turbulent, Malawi 58 low/inactive). The 18 countries not in it have `acled_level` = `low/inactive` (ACLED rates every country ranked 51 or lower as low/inactive) and an empty `acled_rank`, because ACLED publishes no rank for them.

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

- **Our rule (current, 2026-11-18):** an Arab League country is on the conflict list if ACLED rates it *extreme* or *high* (rank 1 to 30): Palestine, Syria, Sudan, Yemen, Somalia, Lebanon, Iraq. A non-Arab country is on it only if ACLED rates it *extreme* (rank 1 to 10): Myanmar, Mexico, Nigeria, Ecuador, Brazil, Haiti, Pakistan. All of them, with no selection by hand. ACLED counts all organised violence, including gang violence, which is why Mexico, Brazil and Ecuador are on the list. Libya is not on it: ACLED rates it *turbulent* (rank 35).
- **Earlier rules, the same day:** first *extreme* or *high* for every country (30), then *high* only (20). The 15 non-Arab *high* countries of the second rule (Cameroon, DR Congo, Ukraine, Colombia, India, Guatemala, Russia, Bangladesh, Ethiopia, Kenya, South Sudan, Honduras, Mali, Central African Republic, Burundi) were removed; they are in the git history.
- **Checked on 2026-11-18:** all 30 extreme and high countries matched ACLED's table for rank and level, and the level boundaries above match the table (10 extreme, 20 high, 20 turbulent). Equal ranks (for example three countries at 11) are ACLED's own.

## Passport strength: Henley Passport Index

Columns `passport_rank` and `passport_visa_free`, filled for all 35 countries (for the 6 reference countries added later, from the same API's 2026 entries).

- **Source:** the Henley Passport Index, 2026 data, taken on 2026-11-18 from <https://api.henleypassportindex.com/api/v3/countries> (the data behind <https://www.henleyglobal.com/passport-index/ranking>).
- **Scale:** `passport_visa_free` is the number of destinations (out of 227) a holder can enter without a visa obtained in advance. `passport_rank` follows from it: 1 is the strongest passport (Singapore, 193), 104 the weakest (Afghanistan, 22). Countries with the same count share a rank.

## Overlaps to keep in mind

- Ecuador (ACLED rank 6, extreme) is a placebo country and on the conflict list. Jamaica (rank 28, high) is a placebo country but not on the conflict list, since non-Arab countries need *extreme*. Papua New Guinea (on the World Bank's 2027 conflict list, not ranked by ACLED) is a placebo country.

## Same rules for every nationality (checked 2026-11-19)

The design needs the rules for a tourist visa to Estonia to be the same for every nationality that needs a visa. Checked so far:

- **Travel documents.** The EU list of travel documents that Member States recognise (Part I, notifications until 16 November 2026, <https://home-affairs.ec.europa.eu/travel-documents-issued-third-countries-and-territorial-entities-part-i_en>; the Estonia column of the XLSX was read cell by cell). Estonia recognises the ordinary passport of all 35 countries. Two carry a condition that a current passport meets: Somalia ("The new travel document issued as from 1/2/2007 are recognised") and Algeria ("Only passports in which the validity is not extended"). The Palestinian passport is recognised without comment. The colour key (green recognised, red not, yellow no position) is from the Belgian immigration office, <https://dofi.ibz.be/en/themes/entry/border-control/travel-documents/list-recognised-travel-documents>, as the file has none.
- **Belarus.** Estonia restricts visas for Russian citizens for all purposes, but for Belarusian citizens only for short-term work, business and teleworking, not for tourism (<https://www.vm.ee/en/consular-visa-and-travel-information/visa-information/restrictions-accepting-visa-applications>, page undated). Belarus stays a placebo. The embassy in Minsk takes no visa applications, which does not matter for applicants who apply in the UAE.
- **Prior consultation (Article 22 of the Visa Code).** Annex 16 of the Visa Code Handbook (version 1 November 2024, <https://home-affairs.ec.europa.eu/document/download/e6139169-6ec7-4374-a50a-eb2333411e3f_en>) lists the countries for which at least one Member State requires prior consultation, without naming the Member State. 15 Arab League countries are on it (Algeria, Egypt, Iraq, Jordan, Lebanon, Libya, Mauritania, Morocco, Palestine, Saudi Arabia, Somalia, Sudan, Syria, Tunisia, Yemen), 7 are not (Bahrain, Comoros, Djibouti, Kuwait, Oman, Qatar, UAE); of the others, Nigeria, Pakistan and Belarus are on it. Whether Estonia itself consults for any of them cannot be checked from public sources. Prior consultation changes the procedure (other states may object), not the grounds for refusal; it is a limit to state.
- **Not checked:** Article 25a visa measures.
