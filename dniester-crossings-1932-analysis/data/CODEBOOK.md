# Codebook

## persons.csv

One row per person. 822 rows.

| Column | Type | Meaning |
|---|---|---|
| `person_id` | integer | Record number, 1–822, in date order. |
| `incident_id` | integer | Groups people who crossed, or were caught, together. Matches `incidents.csv`. |
| `date` | date (YYYY-MM-DD) | Date of the event. Empty when the report gives only the month. |
| `date_precision` | text | `day`; `month` (month only); `month_decade_2` (10th–19th of the month); `month_decade_4` (30th–31st). |
| `year`, `month`, `day` | integer | Parts of the date. `day` is empty when unknown. |
| `time` | HH:MM | Hour given in the report. The reports' "24th hour" (the hour ending at midnight) is recorded as 24:00, the end of the day. |
| `time_of_day` | text | `night` (21:00–04:59), `morning` (05:00–11:59), `afternoon` (12:00–16:59), `evening` (17:00–20:59), `unknown`. Also `night` where the report says "at night" without an hour. |
| `direction` | text | `left_to_right`: from the Soviet bank towards Romania. `right_to_left`: from the Romanian bank into the Soviet Union. |
| `outcome` | text | `crossed`: reached the other bank. `caught`: detained at or near the river, or on arrival from Romania. `killed`: shot dead or mortally wounded. `drowned`. `fled_back`: turned back, or escaped into the Soviet rear. `arrested_before_attempt`: arrested at home or while preparing to leave. `disappeared`: left the village; crossing unconfirmed. `unknown`. |
| `outcome_code` | integer | 0 crossed, 1 killed, 2 caught, 4 drowned, 5 fled back, 6 arrested before attempt, 7 disappeared. Empty if unknown. |
| `returned_by_romania` | text | For people who crossed and were sent back by the Romanian authorities: `immediately`, or the date they were handed over. |
| `name` | text | Name as given in the report, romanised; or relationship to a named person ("Wife of …", "Child of …"); `unknown` if not given. |
| `sex` | text | `male`, `female`, `unknown`. |
| `sex_code` | integer | 0 male, 1 female, 99 unknown. |
| `age_years` | integer | Age in years, where the report gives it. |
| `age_group` | text | `child` (under 13), `teen` (13–17), `minor` (under 18, more precise age not given), `adult`, `unknown`. Taken from `age_years` where known, otherwise from the report's wording. |
| `social_class` | text | Class label used in the report: `bedniak` (poor peasant), `seredniak` (middle peasant), `kulak`, `kolkhoznik` (collective-farm member), `kolkhoznik (household member)`, `worker`, `unemployed`, `deserting soldier`, `mennonite`, `prisoner`, `prison warden`, `former officer`, `unknown`. |
| `occupation` | text | Occupation or status as recorded, in English. `single farmer` translates *edinolichnik* (a peasant farming outside the collective farm). |
| `in_group` | 0/1 | 1 if the person crossed, or tried to, as part of a group. Empty if not known. |
| `group_size` | integer | Size of the group, as stated in the report. |
| `location_source` | text | Place of the event as written in the report, romanised. |
| `location_modern` | text | Present official name of that place. |
| `origin_source` | text | Home village or town as written in the report, romanised. |
| `origin_modern` | text | Present official name of that place. |
| `ice_station` | text | Ice-measuring station nearest to the place of the event: `Camenca`, `Dubasari`, `Krasni Mayak`, `Tiraspol`, `unknown`. |
| `ice_thickness_cm` | number | Ice thickness at that station on the nearest date of measurement. 0 = no ice. |
| `temp_c` | number | Daily air temperature at Dubasari, °C (see `dubasari_daily_temperature_1928_1933.csv`). |
| `snow_mm` | number | Daily snowfall, mm. |
| `rain_mm` | number | Daily rainfall, mm. |
| `fog` | 0/1 | 1 if fog was recorded that day. |
| `report_weather` | text | The report's own note on weather and ice for that date, in English, where it gives one. |
| `person_note` | text | Details about this person from the reports: wounds, reasons for crossing, family ties, how the crossing was made. |
| `narrative` | text | English translation or summary of the report entry, shared by everyone in the incident. `[...]` marks names and details left out because they are given in the record; other words in square brackets are the translator's. |
| `source_citation` | text | Archival reference, e.g. `ANA, f. A-49, inv. 1, d. 2084, f. 8`. Where later reports add to an entry, all folios are given. f. 41v is the unnumbered reverse of f. 41. |

## incidents.csv

One row per incident. 233 rows. Date, time, direction, place and weather are taken from the first person in the incident.

| Column | Meaning |
|---|---|
| `incident_id` | As in `persons.csv`. |
| `date` … `report_weather` | As in `persons.csv`. |
| `n_persons` | Number of people in the incident. |
| `n_crossed`, `n_caught`, `n_killed`, `n_drowned`, `n_fled_back`, `n_arrested_before_attempt`, `n_disappeared`, `n_unknown` | Number of people with each outcome. |
| `narrative`, `source_citation` | As in `persons.csv`. |

## report_weather.csv

| Column | Meaning |
|---|---|
| `report_date` | Date the note refers to. |
| `source_citation` | Archival reference. |
| `text_romanised` | The note as written, romanised. |
| `text_english` | English translation. |

## dubasari_daily_temperature_1928_1933.csv

| Column | Meaning |
|---|---|
| `date` | Date. |
| `temp_c` | Daily air temperature at Dubasari, °C. Empty where no reading survives. |

## Romanisation

Library of Congress, without diacritics: а a, б b, в v, г g, д d, е e, ё e, ж zh, з z, и i, й i, к k, л l, м m, н n, о o, п p, р r, с s, т t, у u, ф f, х kh, ц ts, ч ch, ш sh, щ shch, ъ ", ы y, ь ', э e, ю iu, я ia.
