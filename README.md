# Crossings of the Dniester, 1932: analysis code and maps

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23671593.svg)](https://doi.org/10.5281/zenodo.23671593)

Code and figures for the analysis of 822 people who crossed, or tried to cross, the Dniester between the Moldavian ASSR and Romanian Bessarabia between 28 February and 26 June 1932.

The dataset itself is published on Zenodo, with its sources, method and codebook:

> McFarlane, Arthur. *Crossings of the Soviet–Romanian border on the Dniester, February–June 1932* [dataset]. Version 1.0. Zenodo, 2026. https://doi.org/10.5281/zenodo.23299300

Related article: McFarlane, Arthur. "Crossing the River Between Worlds." *Contemporary European History* 35 (2026). https://doi.org/10.1017/S0960777326101969

## What is here

| Folder or file | Contents |
|---|---|
| `data/` | A copy of the dataset files the code uses (`persons.csv`, `incidents.csv`, `dubasari_daily_temperature_1928_1933.csv`), the gazetteer of places (`gazetteer.csv`), and clipped Natural Earth map layers. |
| `R/dniester_regressions.R` | The regression analyses (below). Writes tables, model summaries and four charts to `results/`. |
| `python/make_maps.py` | Draws the three maps in `figures/`. |
| `python/build_gazetteer.py` | Builds `data/gazetteer.csv`: coordinates and sources for every place in the dataset, and which bank of the Dniester each lies on. |
| `python/check_regressions.py` | An independent re-implementation of the R models, used to check them. |
| `python/prepare_naturalearth.py` | Clips the Natural Earth layers to the area mapped. Already run; only needed to rebuild `data/naturalearth/`. |
| `figures/` | The maps, as PNG (300 dpi) and PDF. |

## The questions

1. Did ice on the river change **how many** people tried to cross?
2. Did ice change **whether they got across**?
3. Did success depend on **where people came from**?
4. Did success depend on **where they crossed**?

An *attempt* is a person who went to the river from the Soviet bank and either reached the Romanian bank or was stopped there (caught, killed, drowned or turned back): 692 people, of whom 338 crossed. People arrested at home before setting out, those who disappeared without a confirmed crossing, and those crossing from the Romanian side are left out.

## Methods

- **Number of attempts (1).** Counts of people and of incidents for each of four ice-measuring sectors on each of 120 days (480 sector-days), modelled with negative binomial regression and a fixed effect for each sector. Ice is the nearest station reading; a second model adds air temperature at Dubasari.
- **Success (2–4).** Logistic regression of whether each person crossed. People who crossed together shared one fate, so standard errors are clustered by incident. Places with fewer than ten attempts are grouped as "other". Places where everyone or no one crossed (for example Molovata, 24 of 24) give no usable odds ratio; they are reported as success rates and left out of the regressions.

## Main results

| Question | Result |
|---|---|
| Ice and number of attempts | Each extra centimetre of ice: about 10% more people at the river (rate ratio 1.10, 95% CI 1.08–1.13). A frozen sector saw about ten times as many incidents as open water (10.4, 6.2–17.4). |
| Ice and success | No effect (odds ratio 1.005 per cm, p = 0.70), including after allowing for fog, time of day and sector. |
| Origin and success | Success rates differ sharply by home village, but no single village differs clearly from Cioburciu once group crossings are allowed for. Crossing from one's own village made no difference. |
| Place and success | Place matters. Rybnitsa: 18 of 19 crossed, in eight incidents (odds ratio 25.8 against Cioburciu). |

Attempts with no recorded time, and people of unknown origin, succeeded far more often. This reflects the source: the guards recorded what they saw, and people who crossed unseen left fewer details behind. Results resting on a single incident (Delacau, 26 people in one night; Teiu; Telita) describe that event, not the place.

## The maps

- **Figure 3, Failure flows:** where people who failed to cross came from, with lines to the place where they tried.
- **Figure 4, Successful origin clusters:** home villages of people who got across; darker dots mean more people.
- **Figure 5, Successful crossing points:** where people got across; darker dots mean more people.

Places are located from GeoNames and Wikipedia; `data/gazetteer.csv` gives the source and a note for each. The 1932 border followed the Dniester, which is drawn from Natural Earth's simplified river line.

## Running the code

**R** (4.3 or later): open `R/dniester_regressions.R` in RStudio and press Source. Missing packages (MASS, sandwich, lmtest, ggplot2) install on first run.

**Python** (3.10 or later): from this folder, run

```
pip install -r requirements.txt
python python/make_maps.py
python python/check_regressions.py
```

## Authorship

I compiled the dataset from the archival file ANA, f. A-49, inv. 1, d. 2084, and checked every record against photographs of the file. I chose the research questions and the models, and the interpretation is mine. I wrote the code with the help of an AI assistant (Claude, by Anthropic), and checked its results against an independent re-implementation (python/check_regressions.py).

## Licence

Code: MIT licence (see `LICENSE`). Data and figures: CC BY 4.0, as for the dataset on Zenodo. Map layers: Natural Earth, public domain.
