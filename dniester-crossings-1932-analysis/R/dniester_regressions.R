# =============================================================================
# Crossings of the Dniester, February–June 1932: regression analyses
#
#   1. Ice and the number of crossing attempts
#   2. Ice and the success of attempts
#   3. Place of origin and success
#   4. Place of crossing and success
#
# Open this file in RStudio and press Source. It works from the repository
# folder (the one above R/), reads data/, and writes to results/.
# =============================================================================


# ---- 0. Packages -------------------------------------------------------------
# Installs any missing packages the first time; does nothing after that.
needed <- c("MASS", "sandwich", "lmtest", "ggplot2")
missing <- needed[!needed %in% rownames(installed.packages())]
if (length(missing) > 0) install.packages(missing, repos = "https://cloud.r-project.org")

# Work from the repository folder (the folder above R/). If you run the script
# some other way, set the working directory to the repository folder first.
if (requireNamespace("rstudioapi", quietly = TRUE) && rstudioapi::isAvailable()) {
  setwd(dirname(dirname(rstudioapi::getSourceEditorContext()$path)))
}
data_dir <- "data"

library(MASS)      # glm.nb(): negative binomial regression for counts
library(sandwich)  # vcovCL(): standard errors clustered by incident
library(lmtest)    # coeftest(), waldtest(): tests using those standard errors
library(ggplot2)   # figures

dir.create("results", showWarnings = FALSE)


# ---- 1. Read the data --------------------------------------------------------
# na.strings = "" turns empty cells into NA (R's missing value).
persons <- read.csv(file.path(data_dir, "persons.csv"), stringsAsFactors = FALSE, na.strings = "")
temperature <- read.csv(file.path(data_dir, "dubasari_daily_temperature_1928_1933.csv"),
                        stringsAsFactors = FALSE, na.strings = "")
temperature$date <- as.Date(temperature$date)

# An "attempt" is a person who went to the river from the Soviet side and
# either got across or was stopped there. This leaves out people arriving from
# Romania, people arrested at home before trying, people who disappeared
# without a confirmed crossing, and the one record with an unknown outcome.
attempts <- subset(persons,
                   direction == "left_to_right" &
                   outcome %in% c("crossed", "caught", "killed", "drowned", "fled_back"))

# Success = reached the Romanian bank (1) or not (0).
attempts$success <- as.integer(attempts$outcome == "crossed")

cat("Attempts:", nrow(attempts), " Crossed:", sum(attempts$success),
    " Success rate:", round(mean(attempts$success), 3), "\n")

# A note on what "success" can mean in this source. Guards recorded failed
# attempts in detail (they had the people in hand), but many successful
# crossings are known only from tracks in the snow or from informants, so the
# person's name and origin are often unknown. Keep this in mind when reading
# analyses 3 and 4.


# ---- 2. Helper functions -----------------------------------------------------

# Standard errors clustered by incident. People who crossed together share an
# outcome (a family is caught, or gets across, together), so they are not
# independent observations. Clustering by incident corrects for this.
clustered <- function(model) {
  coeftest(model, vcov = vcovCL(model, cluster = ~ incident_id))
}

# Turn a coefficient table into odds ratios (logit) or rate ratios (counts),
# with 95% confidence intervals.
ratio_table <- function(ct, label = "ratio") {
  est <- ct[, "Estimate"]
  se  <- ct[, "Std. Error"]
  out <- data.frame(term     = rownames(ct),
                    ratio    = exp(est),
                    ci_low   = exp(est - 1.96 * se),
                    ci_high  = exp(est + 1.96 * se),
                    p_value  = ct[, 4],
                    row.names = NULL)
  names(out)[2] <- label
  out
}

# Success rate by group, with exact (Clopper–Pearson) 95% confidence intervals.
success_by <- function(df, var) {
  groups <- split(df$success, df[[var]])
  out <- data.frame(group   = names(groups),
                    n       = sapply(groups, length),
                    crossed = sapply(groups, sum),
                    row.names = NULL)
  out$rate <- out$crossed / out$n
  ci <- t(mapply(function(k, n) binom.test(k, n)$conf.int, out$crossed, out$n))
  out$ci_low  <- ci[, 1]
  out$ci_high <- ci[, 2]
  out[order(-out$n), ]
}

# Write model output to a text file as well as the screen.
report <- function(title, x) {
  cat("\n\n=====", title, "=====\n")
  print(x)
  capture.output(cat("\n\n=====", title, "=====\n"), print(x),
                 file = "results/model_summaries.txt", append = TRUE)
}
unlink("results/model_summaries.txt")


# =============================================================================
# ANALYSIS 1. Ice and the number of crossing attempts
# =============================================================================
# Unit: one sector (identified by its ice-measuring station) on one day,
# 28 February – 26 June 1932: 4 stations x 120 days = 480 sector-days.
# Outcome: the number of attempts that day on that sector, including days
# with none. Counted two ways: people, and incidents (a family of seven is one
# incident but seven people).

stations <- c("Camenca", "Dubasari", "Krasni Mayak", "Tiraspol")
days     <- seq(as.Date("1932-02-28"), as.Date("1932-06-26"), by = "day")

panel <- expand.grid(date = days, ice_station = stations, stringsAsFactors = FALSE)

dated <- subset(attempts, !is.na(date) & ice_station %in% stations)
dated$date <- as.Date(dated$date)

people_per_day <- aggregate(person_id ~ date + ice_station, data = dated, FUN = length)
names(people_per_day)[3] <- "people"

incidents_per_day <- aggregate(incident_id ~ date + ice_station, data = dated,
                               FUN = function(x) length(unique(x)))
names(incidents_per_day)[3] <- "incidents"

panel <- merge(panel, people_per_day,    by = c("date", "ice_station"), all.x = TRUE)
panel <- merge(panel, incidents_per_day, by = c("date", "ice_station"), all.x = TRUE)
panel$people[is.na(panel$people)]       <- 0
panel$incidents[is.na(panel$incidents)] <- 0

# Ice thickness for every sector-day. The dataset gives the ice reading only
# on days when something happened, so for each station we take the reading
# from the nearest date on which one is recorded. Readings change rarely
# (the ice held at much the same thickness through March, then went), so
# this is a fair approximation, but it is an approximation.
readings <- unique(subset(persons,
                          !is.na(date) & ice_station %in% stations & !is.na(ice_thickness_cm),
                          select = c(date, ice_station, ice_thickness_cm)))
readings$day <- as.numeric(as.Date(readings$date))

nearest_ice <- function(day, station) {
  r <- readings[readings$ice_station == station, ]
  r$ice_thickness_cm[which.min(abs(r$day - day))]
}
panel$ice_cm <- mapply(nearest_ice, as.numeric(panel$date), panel$ice_station)
panel$frozen <- as.integer(panel$ice_cm > 0)

panel <- merge(panel, temperature, by = "date", all.x = TRUE)   # adds temp_c

write.csv(panel, "results/analysis1_sector_days.csv", row.names = FALSE)

# Counts with many zero days and a few very busy days are "overdispersed",
# so a negative binomial model fits better than a Poisson one.
# exp(coefficient) is a rate ratio: the factor by which the expected number
# of attempts changes for one more centimetre of ice. Sector is included
# (ice_station) so that busy and quiet sectors are compared with themselves.

m1_people    <- glm.nb(people    ~ ice_cm + ice_station, data = panel)
m1_incidents <- glm.nb(incidents ~ ice_cm + ice_station, data = panel)
m1_frozen    <- glm.nb(incidents ~ frozen + ice_station, data = panel)
m1_temp      <- glm.nb(incidents ~ ice_cm + temp_c + ice_station, data = panel)

report("1a. People per sector-day ~ ice (negative binomial)", summary(m1_people))
report("1b. Incidents per sector-day ~ ice (negative binomial)", summary(m1_incidents))
report("1c. Incidents per sector-day ~ river frozen or not", summary(m1_frozen))
report("1d. Incidents per sector-day ~ ice + temperature", summary(m1_temp))

t1 <- rbind(
  cbind(model = "people ~ ice",               ratio_table(coeftest(m1_people),    "rate_ratio")),
  cbind(model = "incidents ~ ice",            ratio_table(coeftest(m1_incidents), "rate_ratio")),
  cbind(model = "incidents ~ frozen",         ratio_table(coeftest(m1_frozen),    "rate_ratio")),
  cbind(model = "incidents ~ ice + temp",     ratio_table(coeftest(m1_temp),      "rate_ratio")))
write.csv(t1, "results/analysis1_rate_ratios.csv", row.names = FALSE)
report("1. Rate ratios", t1[!grepl("Intercept|ice_station", t1$term), ])

# A caution for interpretation: the river was frozen in March and open from
# April. Ice therefore also stands for everything else that changed between
# March and June: the thaw, the spring famine, more patrols. Model 1d adds
# temperature to show how much of the ice effect survives one such change.

daily <- aggregate(cbind(incidents, people) ~ date, data = panel, FUN = sum)
daily$frozen <- aggregate(frozen ~ date, data = panel, FUN = max)$frozen
fig1 <- ggplot(daily, aes(date, incidents, fill = factor(frozen, labels = c("open", "frozen")))) +
  geom_col() +
  labs(x = NULL, y = "Incidents per day (all sectors)", fill = "River",
       title = "Crossing attempts from the Soviet bank, 28 February – 26 June 1932") +
  theme_minimal()
ggsave("results/fig1_attempts_by_day.png", fig1, width = 9, height = 4.5, dpi = 200)


# =============================================================================
# ANALYSIS 2. Ice and the success of attempts
# =============================================================================
# Unit: one person who attempted a crossing, where the ice reading is known.
# Outcome: crossed (1) or not (0). Logistic regression; exp(coefficient) is an
# odds ratio per centimetre of ice. Standard errors clustered by incident.

a2 <- subset(attempts, !is.na(ice_thickness_cm))
# Time of day as categories, with night as the reference. Events with no
# recorded hour are kept as their own category: they are mostly tracks found
# after the event, nearly all successful, so lumping them with daytime would
# make night look far worse for crossers than it was.
a2$time_of_day <- relevel(factor(a2$time_of_day), ref = "night")

m2      <- glm(success ~ ice_thickness_cm, family = binomial, data = a2)
m2_frz  <- glm(success ~ I(ice_thickness_cm > 0), family = binomial, data = a2)
# Adjusted model: fog and darkness should help people get across unseen; the
# sector controls for differences in guarding along the river.
m2_adj  <- glm(success ~ ice_thickness_cm + fog + time_of_day + ice_station,
               family = binomial, data = a2)

report("2a. Success ~ ice (logit, clustered SEs)", clustered(m2))
report("2b. Success ~ frozen or not", clustered(m2_frz))
report("2c. Success ~ ice + fog + time of day + sector", clustered(m2_adj))

t2 <- rbind(
  cbind(model = "success ~ ice",                       ratio_table(clustered(m2),     "odds_ratio")),
  cbind(model = "success ~ frozen",                    ratio_table(clustered(m2_frz), "odds_ratio")),
  cbind(model = "success ~ ice + fog + time + sector", ratio_table(clustered(m2_adj), "odds_ratio")))
write.csv(t2, "results/analysis2_odds_ratios.csv", row.names = FALSE)

r2 <- success_by(a2, "ice_thickness_cm")
r2$ice_cm <- as.numeric(r2$group)
write.csv(r2, "results/analysis2_success_by_ice.csv", row.names = FALSE)
report("2. Success rate by ice reading", r2)

fig2 <- ggplot(r2, aes(ice_cm, rate)) +
  geom_pointrange(aes(ymin = ci_low, ymax = ci_high)) +
  geom_text(aes(label = paste0("n = ", n)), nudge_x = 1.2, hjust = 0, size = 3) +
  labs(x = "Ice thickness at nearest station (cm)", y = "Share who crossed",
       title = "Success of crossing attempts by ice thickness") +
  theme_minimal()
ggsave("results/fig2_success_by_ice.png", fig2, width = 7, height = 4.5, dpi = 200)


# =============================================================================
# ANALYSES 3 and 4. Place of origin, place of crossing, and success
# =============================================================================
# Places with fewer than 10 attempts are grouped as "other": with a handful of
# people, a success rate means little. "unknown" is kept as its own group,
# because whether a person's origin is known is itself linked to the outcome
# (see the note in section 1). The reference group is Cioburciu (Chobruchi),
# the busiest village, so each odds ratio compares a place with Chobruchi.

group_small <- function(x, min_n = 10) {
  counts <- table(x)
  ifelse(x %in% names(counts)[counts >= min_n], x, "other")
}

# A logit model cannot estimate an odds ratio for a group where everyone
# crossed, or no one did ("separation"): the estimate runs off towards
# infinity, and clustered standard errors can make it look highly
# significant. Such groups are therefore left out of the regressions and
# reported only in the success-rate tables.
separated <- function(df, var) {
  r <- success_by(df, var)
  r$group[r$crossed == 0 | r$crossed == r$n]
}

# ---- Analysis 3: place of origin ----
a3 <- attempts
a3$origin_group <- relevel(factor(group_small(a3$origin_modern)), ref = "Cioburciu")

r3 <- success_by(a3, "origin_group")
write.csv(r3, "results/analysis3_success_by_origin.csv", row.names = FALSE)
report("3. Success rate by place of origin", r3)
report("3. Origins where all or none crossed (odds ratios not meaningful)",
       separated(a3, "origin_group"))

sep3 <- separated(a3, "origin_group")
a3m  <- subset(a3, !(origin_group %in% sep3))
a3m$origin_group <- droplevels(a3m$origin_group)
m3_null <- glm(success ~ 1,            family = binomial, data = a3m)
m3      <- glm(success ~ origin_group, family = binomial, data = a3m)
report("3a. Success ~ origin (logit, clustered SEs)", clustered(m3))
# Does origin matter at all? A Wald test of all origin terms together,
# using the clustered standard errors.
report("3b. Joint test of origin",
       waldtest(m3_null, m3, vcov = function(m) vcovCL(m, cluster = ~ incident_id)))

# Did people who crossed near their own village do better than those who had
# travelled to the border? (Only where both places are known.)
a3k <- subset(a3, origin_modern != "unknown" & location_modern != "unknown")
a3k$local <- as.integer(a3k$origin_modern == a3k$location_modern)
m3_local <- glm(success ~ local, family = binomial, data = a3k)
report("3c. Success ~ crossing from own village", clustered(m3_local))
report("3c. Success rate: own village (1) or not (0)", success_by(a3k, "local"))

# Origin is known for far more of the caught than of those who crossed, so
# model 3d repeats 3a without the "unknown" group as a check.
a3d <- subset(a3m, origin_group != "unknown")
a3d$origin_group <- droplevels(a3d$origin_group)
m3_known <- glm(success ~ origin_group, family = binomial, data = a3d)
report("3d. Success ~ origin, known origins only", clustered(m3_known))

t3 <- rbind(
  cbind(model = "success ~ origin",              ratio_table(clustered(m3),       "odds_ratio")),
  cbind(model = "success ~ origin (known only)", ratio_table(clustered(m3_known), "odds_ratio")),
  cbind(model = "success ~ own village",         ratio_table(clustered(m3_local), "odds_ratio")))
write.csv(t3, "results/analysis3_odds_ratios.csv", row.names = FALSE)

# ---- Analysis 4: place of crossing ----
a4 <- attempts
a4$place_group <- relevel(factor(group_small(a4$location_modern)), ref = "Cioburciu")

r4 <- success_by(a4, "place_group")
write.csv(r4, "results/analysis4_success_by_place.csv", row.names = FALSE)
report("4. Success rate by place of crossing", r4)
report("4. Places where all or none crossed (odds ratios not meaningful)",
       separated(a4, "place_group"))

sep4 <- separated(a4, "place_group")
a4m  <- subset(a4, !(place_group %in% sep4))
a4m$place_group <- droplevels(a4m$place_group)
m4_null <- glm(success ~ 1,           family = binomial, data = a4m)
m4      <- glm(success ~ place_group, family = binomial, data = a4m)
report("4a. Success ~ place of crossing (logit, clustered SEs)", clustered(m4))
report("4b. Joint test of place",
       waldtest(m4_null, m4, vcov = function(m) vcovCL(m, cluster = ~ incident_id)))

# Some places were crossed mostly in March, others mostly in spring, so place
# and ice are tangled together. Model 4c holds ice constant.
a4c <- subset(a4m, !is.na(ice_thickness_cm))
a4c$place_group <- droplevels(a4c$place_group)
m4_ice <- glm(success ~ place_group + ice_thickness_cm, family = binomial, data = a4c)
report("4c. Success ~ place + ice", clustered(m4_ice))

t4 <- rbind(
  cbind(model = "success ~ place",       ratio_table(clustered(m4),     "odds_ratio")),
  cbind(model = "success ~ place + ice", ratio_table(clustered(m4_ice), "odds_ratio")))
write.csv(t4, "results/analysis4_odds_ratios.csv", row.names = FALSE)

# Figures for analyses 3 and 4: success rate with 95% intervals, by place.
plot_rates <- function(r, title, file) {
  r$group <- factor(r$group, levels = r$group[order(r$rate)])
  p <- ggplot(r, aes(rate, group)) +
    geom_pointrange(aes(xmin = ci_low, xmax = ci_high)) +
    geom_text(aes(label = paste0("n = ", n)), x = 1.02, hjust = 0, size = 3) +
    scale_x_continuous(limits = c(0, 1.15), breaks = seq(0, 1, 0.25)) +
    labs(x = "Share who crossed (95% interval)", y = NULL, title = title) +
    theme_minimal()
  ggsave(file, p, width = 8, height = 5, dpi = 200)
}
plot_rates(r3, "Success of crossing attempts by place of origin", "results/fig3_success_by_origin.png")
plot_rates(r4, "Success of crossing attempts by place of crossing", "results/fig4_success_by_place.png")

cat("\nDone. Results are in the results/ folder.\n")
