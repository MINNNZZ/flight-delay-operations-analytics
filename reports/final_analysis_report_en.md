# Flight Delays and Cancellations — Client Report

**Publication note:** the locally validated PBIX binaries are not included in this source-only release. Screenshots and report/model definitions are available; see [distribution status](../docs/PBIX_DISTRIBUTION.md). References below to provided PBIX files describe the local project deliverables.

Language: English. Analysis period: **January–December 2015**. This report describes historical operations, not current airline performance. It uses the same sources, KPI definitions and conclusions as the [Vietnamese edition](final_analysis_report_vi.md). Airline names and codes follow the supplied historical lookup.

## Executive Summary

The typical flight arrived early, yet serious disruptions were common enough to require substantial operational attention. Across **5,819,079 scheduled flights**, mean arrival delay was **4.41 minutes** and the median was **−5 minutes**. However, **325,591 completed flights arrived at least 60 minutes late**, **89,884 were cancelled**, and **15,187 were diverted**. Together these mutually exclusive outcomes affected **430,662 flights, or 7.40% of the schedule**.

Five findings guide the investigation:

1. **Late-day risk is materially higher.** Severe-delay risk was 8.49% for scheduled departures at 17–21h versus 3.61% at 06–11h. The difference persists in several matched comparisons and outlier checks.
2. **Volume and risk imply different priorities.** ORD had the greatest positive arrival-delay minutes among identified origin airports. LGA combined a high severe-delay rate with substantial cancellations. Airport and route findings cover 11 resolved months.
3. **Cancellation management and severe-delay management require different playbooks.** February had the highest cancellation rate, while June had the highest severe-arrival rate. Weather labels accounted for 54.35% of cancellations.
4. **Carrier rankings need qualification.** NK retained an adverse severe-delay gap under the tested comparison settings. MQ had high cancellations, while its completed-flight comparison was sensitive to which flights remained comparable.
5. **Averages conceal operational tail risk.** The 95th percentile of arrival delay was 66 minutes and the 99th percentile was 167 minutes. Removing a small group of extreme observations does not eliminate the wider problem.

Management should first validate these historical candidates with recent data, then investigate late-day rotations and recovery capacity, distinguish cancellation recovery from delay propagation, and monitor rates, exposure and tail severity together. No intervention savings or financial losses can be quantified from this dataset.

## Business Problem

The working question is: **where, when and among which operating segments are delays and disruptions concentrated, what evidence supports possible drivers, and which investigations should management prioritize?** The original task did not specify a narrower question; this scope continues the agreed project investigation.

The decision concerns investigation and recovery priorities. It does not require flight-level prediction, profit optimization or an unsupported causal ranking of airlines.

## Dataset Overview

| Source | Size | Business grain |
| --- | ---: | --- |
| flights.csv | 5,819,079 rows × 31 columns | A scheduled flight leg on an operating date |
| airports.csv | 322 rows × 7 columns | An airport lookup keyed by IATA code |
| airlines.csv | 14 rows × 2 columns | An airline lookup keyed by airline code |

Coverage includes all 365 days and 12 months of 2015. A flight number alone is not a unique key. The checked business key combines date, airline, flight number, origin, destination and scheduled departure time. `FLIGHT_ID` is a row-order surrogate key, not a durable identifier across source replacements. Airport joins have separate origin and destination roles and must not multiply flight rows.

**Geographic coverage is limited to 5,332,914 scheduled flights across 11 months.** All 486,165 October records use unresolved numeric airport identifiers at both ends. These flights remain in system, airline and time analyses, but named-airport and route comparisons exclude them. A verified crosswalk was not available; codes were not inferred from traffic patterns.

Scheduled clocks are local HHMM; delay and duration fields are interpreted as minutes using field meaning and checked identities. Distance units lack independently verified source metadata and are not used for business conclusions. There are no actual timezone/date offsets, aircraft types, passenger loads, connections, crew records, maintenance logs, costs, measured weather or airport-capacity observations.

## Data Quality Assessment

The assessment is **READY WITH WARNINGS** for system, airline and time analysis, and **NOT READY** for full-year named-airport/route rankings or UTC-linked aircraft rotations.

| Material issue | Scale | Interpretation, risk and decision |
| --- | ---: | --- |
| Unresolved October airport codes | 486,165 flights | Isolate named-geography analysis to 11 resolved months; preserve the records in other KPIs. Do not guess a crosswalk. |
| Missing arrival delay | 105,071 records | Exactly 89,884 cancellations plus 15,187 diversions; structural outcome missingness. Exclude from arrival metrics, retain in scheduled-flight reliability metrics. |
| Missing reported delay causes | 4,755,640 values in each cause column | Conditional reporting, not random loss of causes. All 1,063,439 arrivals delayed ≥15 minutes have all five causes; row-level cause sums match arrival delay. |
| Clock/duration inconsistencies | 2 records | Flag `TIME_ISSUE`; apply metric-specific eligibility rather than discard the entire flight. |
| Missing scheduled duration | 6 records | All are cancelled/diverted. Preserve; do not impute a typical duration. |
| Missing airport coordinates | 3 airport records | Avoid unsupported map placement; non-map metrics do not require invented coordinates. |
| Extreme arrival delays >360 minutes | 6,089 completed flights | Preserve potentially real operational disruptions; test sensitivity separately. |

No exact-row duplicates, duplicate business keys, invalid dates/weekdays, malformed HHMM values, unknown airline codes, negative durations/distances or invalid status combinations were found. HHMM=2400 is treated as a possible midnight convention, not automatically an error.

Source hashes and a shared profile run ID bind the quality assessment to the current files. Changed sources, incomplete profile publication or an unidentified quality gate block reuse. See the [quality assessment](data_quality_report.md), [profile](data_profile.json), [gate](quality_gate.json) and [source manifest](source_manifest.json). Supporting technical documents may retain their original language.

## Cleaning Decisions

All source values and rows were preserved. No blanket NULL deletion, mean imputation, duplicate removal or automatic outlier trimming was performed.

- Build `DATE` with sufficient numeric precision and validate all calendar values. Keep scheduled local departure hour and time bands separate from actual departure time.
- Preserve unresolved source airport codes while adding an unknown-member key and `GEO_ELIGIBLE`. A valid dimension foreign key does not resolve the real airport identity.
- Flag the cancelled NK 1012 record on December 24 with inconsistent departure clock; it is already outside departure-delay eligibility. Preserve the F9 1360 record on July 4 with a two-minute duration-identity discrepancy because its arrival delay is consistent; do not infer a rotation from it. Excluding that record does not change conclusions.
- Add explicit arrival eligibility, on-time, severe-delay and disruption flags. Arrival metrics exclude cancellations/diversions. Departure metrics exclude cancellations and the inconsistent departure clock, while retaining eligible diversions that departed.

After cleaning there are still **5,819,079 rows; zero rows removed**. Source missingness and source values are unchanged; duplicates remain zero. All cancelled/diverted flights and extreme arrival delays are retained. Independent readback compared every source column across the entire cleaned export and validated derived dates, flags and aggregate conservation. See [verification.json](verification.json) and [cleaning_validation.json](cleaning_validation.json).

## Analytical Approach

Calculate baseline distributions, means, medians, percentiles and event rates; segment by airline, origin, destination, route, scheduled hour, weekday, month/season and tail number. Investigate relevant airport × hour, airline × airport, route × time and airline × route interactions. Airport rankings require at least 10,000 scheduled flights and route rankings at least 1,000; these thresholds reduce tiny groups but do not guarantee reliability.

**Metric definitions:** on-time arrival means arrival delay <15 minutes among completed flights with valid arrival delay. Severe arrival delay means ≥60 minutes, a project operating definition. Cancellation, diversion and disruption rates use all scheduled flights. Disruption is the non-overlapping union of cancellation, diversion or severe completed arrival. Positive delay minutes do not net late arrivals against early arrivals.

Matched comparisons use explicit common-support restrictions and minimum group counts. Report the original contrast, the retained-subset unadjusted contrast and the standardized contrast separately. The comparison is observational; unmeasured demand, weather, crew, schedule and network differences remain.

The investigation uses descriptive and diagnostic methods, not a predictive model. Post-event cause fields are not valid pre-event predictors without addressing leakage. Historical block resampling examines stability, not the accuracy of a full-file count or the causal effect of changing a schedule.

## Key Findings

| KPI | Value | Denominator / scope |
| --- | ---: | --- |
| Scheduled flights | 5,819,079 | All scheduled flights, 12 months |
| Completed / arrival eligible | 5,714,008 | Neither cancelled nor diverted |
| On-time arrival | 81.39% | 4,650,569 / 5,714,008 |
| On-time across the schedule | 79.92% | 4,650,569 / 5,819,079 |
| Cancellation / diversion | 1.54% / 0.26% | All scheduled flights |
| Severe arrival ≥60 minutes | 5.70% | 325,591 / 5,714,008 |
| Any major disruption | 7.40% | 430,662 / 5,819,079 |
| Departure mean / median | 9.34 / −2 minutes | 5,729,195 eligible departures |
| Arrival mean / median | 4.41 / −5 minutes | Completed arrivals |
| Arrival p90 / p95 / p99 | 34 / 66 / 167 minutes | Completed arrivals |
| Arrival minimum / maximum / standard deviation | −87 / 1,971 / 39.27 minutes | Completed arrivals |
| Positive arrival delay minutes | 69,103,367 | Early minutes do not offset late minutes |

US appears only in January–June. Differences in AA/US flight counts must not be interpreted as organic growth or operational deterioration. Historical airline labels are preserved.

## High-Value Insights

### 1. Investigate late-day reliability before assuming a system-wide capacity problem

**Observation and context:** departures scheduled at 06–11h include 2,263,032 scheduled flights and 2,225,963 eligible arrivals. Mean arrival delay is 0.20 minutes, median −7 and severe-delay rate 3.61%. The 17–21h group includes 1,502,979 scheduled flights and 1,470,984 eligible arrivals: mean 9.47 minutes, median −2 and severe risk 8.49%, approximately 2.35 times the morning risk. Disruption including cancellations/diversions rises from 5.19% to 10.43%.

**Alternative explanations tested:** the evening mean is higher in all 12 months and all 14 carriers. Across 5,401 shared airline × origin × month strata with at least 30 arrivals per time group, minimum-count weighting retains a **10.06-minute mean gap** and a **5.26-percentage-point severe gap**. This comparison contains 1,791,184 morning and 1,257,762 evening arrivals; 82.26% of strata have the same direction. A separate route × month comparison retains a 10.52-minute mean gap. These are separate adjustments, not simultaneous control of every factor.

Removing arrivals delayed >360 minutes leaves means of −0.49 minutes in the morning and 9.10 minutes in the evening. The median also shifts from −7 to −2. A few extreme flights therefore do not explain the entire pattern.

**Interpretation and action:** the pattern is consistent with accumulating operational disruption, and late-aircraft labels are prominent, but linked rotations and UTC offsets are unavailable. Revalidate with recent data, then investigate specific late-day rotations, buffers and recovery capacity. Monitor severe delay, disruption and p95 with cancellation guardrails. Passenger and financial impacts are plausible but unmeasured.

**Analyst lesson:** a mean-by-hour chart is a starting point. Check medians, exposure, cancellation outcomes and matched segments before proposing a mechanism. The next question is which rotations lack recovery margin, not whether every airport needs more capacity.

### 2. ORD is a volume priority; LGA is a reliability priority

**Evidence:** across resolved geography, ORD has 285,884 scheduled flights, 4,482,201 positive delay minutes, a 6.86% share of positive minutes in that scope and an 8.43% severe rate. LGA has 99,605 scheduled flights, 94,834 eligible arrivals, 8.77% severe risk, 4.55% cancellations and 13.14% disruption. Flights arriving at LGA have 9.44% severe risk across 94,527 eligible arrivals.

At LGA, morning-to-evening disruption rises from 8.51% to 19.64%, and mean arrival delay from −1.30 to 14.85 minutes. ORD disruption rises from 8.20% to 14.80%. Airport averages conceal important time interactions.

**Concentration check:** the top ten origin airports by positive delay minutes account for 38.30% of minutes and 36.33% of flights, which is not strong evidence of an extreme airport-level 80/20 effect. The top 20% of routes ranked by positive delay minutes account for 61.30% of severe arrivals and 56.67% of scheduled flights in resolved geography.

**Decision:** prioritize large absolute impact at ORD and late-day reliability/cancellation investigation at LGA. Drill into airline × airport × time before prescribing capacity expansion. Arrival outcomes on flights departing an airport do not establish that their delay originated there.

**Analyst lesson:** sample size, risk and contribution answer different allocation questions. Route ORD → JFK has a 13.59% severe rate across 1,538 completed arrivals, while SFO → LAX leads positive delay minutes with 222,421 minutes across 13,744 scheduled flights. Neither ranking substitutes for the other.

### 3. Separate cancellation recovery from delay propagation

February records 20,517 cancellations among 429,191 scheduled flights, or **4.78%**. June has a 1.81% cancellation rate but the highest severe-arrival rate, **8.15%**, representing 40,171 of 492,847 arrivals. October remains in system/time comparisons: severe risk is 3.36% and cancellation risk 0.50%.

Weather-coded cancellations are **48,851 / 89,884, or 54.35%**. Other cancellation counts are airline 25,262, NAS 15,749 and security 22. In contrast, weather accounts for just 4.95% of reported cause minutes on sufficiently delayed arrivals. These denominators and outcome populations differ; a small weather-minute share does not demonstrate that weather is unimportant.

Maintain separate playbooks for cancellation decisions/rebooking/recovery and for protecting the remaining schedule from propagated delay. Monitor cancellation, disruption, p95 and recovery time. Do not attribute February to a specific storm without event/weather observations, or infer recurring multi-year seasonality from a single year.

**Analyst lesson:** compare cause coverage and outcome eligibility before comparing category shares. The next investigation needs observed weather, recovery actions and passenger connections.

### 4. NK warrants segment investigation; MQ comparisons require explicit coverage

NK records 117,379 scheduled flights, 115,193 eligible arrivals and a 10.64% severe rate. MQ records 294,632 scheduled flights, a 5.10% cancellation rate and a 7.40% severe rate among completed arrivals. Completed-flight delay alone omits MQ's substantial cancellation burden.

For route × month × broad time-band cells with at least ten arrivals on each side, standardization weights each within-cell difference by `min(n_carrier, n_other)`. NK retains 2,879 cells, 81,016 NK arrivals and 296,019 comparison arrivals: the standardized gap is **+5.47 percentage points severe** and **+11.92 minutes mean**. MQ retains 2,875 cells, 110,498 MQ arrivals and 125,398 comparison arrivals: **+0.17 points severe** and **−2.16 minutes mean**.

The updated selection check is essential:

| Carrier | Raw gap across 11 resolved months | Raw gap in retained subset | Standardized gap in that subset |
| --- | ---: | ---: | ---: |
| NK | +5.26 percentage points | +5.36 points | +5.47 points |
| MQ | +1.94 percentage points | +0.12 points | +0.17 points |

MQ's gap largely contracts **before** standardization, when the compared population changes. The full reduction cannot be credited to network-mix adjustment. This is a comparison of estimands, not a causal decomposition.

| Carrier | Time grouping / minimum arrivals per side | Standardized severe gap | Carrier arrivals retained | Carrier coverage within resolved geography |
| --- | --- | ---: | ---: | ---: |
| NK | Broad band / 10 | +5.47 points | 81,016 | 77.1% |
| NK | Broad band / 30 | +4.61 points | 48,758 | 46.4% |
| NK | Individual hour / 10 | +5.50 points | 44,403 | 42.3% |
| MQ | Broad band / 10 | +0.17 points | 110,498 | 43.0% |
| MQ | Broad band / 30 | +0.09 points | 48,369 | 18.8% |
| MQ | Individual hour / 10 | +1.23 points | 28,526 | 11.1% |

The individual-hour MQ comparison has only 28,561 comparison arrivals, 0.57% of all other-carrier arrivals in resolved geography. Finer matching narrows the hour difference but sharply reduces coverage. It does not establish network-wide equality or superiority. The other carriers are pooled, October is excluded, and cancellations have not been adjusted in these completed-flight comparisons.

Investigate NK's retained high-gap segments and MQ's cancellations separately. Tail N219FR has 13.94% severe risk on 1,306 arrivals, but tail rankings do not demonstrate maintenance defects without schedule adjustment and maintenance records.

**Analyst lesson:** when segmentation changes a ranking, change the investigation question. Always separate selection from adjustment and report what fraction of the original population remains.

### 5. Preserve the tail; do not let early arrivals cancel the management signal

Arrival delay has mean 4.41 minutes, median −5, p90 34, p95 66, p99 167 and maximum 1,971. The 6,089 arrivals delayed >360 minutes are about 0.11% of completed arrivals and contribute 4.64% of positive delay minutes. Excluding them reduces mean to 3.85 minutes and severe risk to 5.60%, compared with 5.70% originally. The broader problem survives.

The median describes the typical flight; p95 and severe rates describe harmful outcomes. Very large delays may be operationally real and should remain visible in irregular-operations analysis. The **69.10 million positive delay minutes** are flight-minutes summed across legs, not passenger-minutes, crew-hours or distinct aircraft-hours lost. Propagated disruption may be counted on multiple legs.

Use mean, median, severe/disruption rates, p95/p99 and exposure together. Do not improve presentation by deleting extreme events. The next step is to link severe events to validated recovery chains and passenger impacts.

### 6. The late-day direction survives paired historical day-block checks

The raw evening-minus-morning mean gap is **9.27 minutes**, the severe-rate gap **4.88 percentage points**, the severe risk ratio **2.35**, and the disruption-rate gap **5.25 points**.

Month-stratified circular day-block resampling uses 365 paired operating days, 3,000 repetitions and seed `20261112`. The same sampled dates are used for morning and evening; monthly day counts are retained, and outcomes are pooled using flight exposure.

| Contrast | 2.5th–97.5th percentile range, seven-day blocks |
| --- | ---: |
| Mean arrival delay, evening minus morning | +8.41 to +10.13 minutes |
| Severe-delay rate gap | +4.37 to +5.40 percentage points |
| Severe risk ratio | 2.24 to 2.46 |
| Disruption-rate gap | +4.65 to +5.87 percentage points |

One-day and fourteen-day blocks also retain the direction: mean ranges are +8.56 to +10.02 and +8.46 to +10.09 minutes, respectively. These are **within-2015 stability ranges under the resampling assumptions**, not uncertainty in exact full-file counts, a forecast, or a causal effect. Month-end wrap-around and the omission of dependence across month boundaries are approximations. The ranges apply to the raw 9.27-minute contrast, not the separately adjusted 10.06-minute contrast or airline effects.

## Root-Cause Analysis

| Hypothesis | Evidence strength | Finding and limitation |
| --- | --- | --- |
| Late aircraft / propagation | Strong for recorded category; moderate for mechanism | 24,961,931 minutes, 39.84% of reported cause minutes; robust late-day association. No linked rotations/UTC to verify chains. |
| Airline operations | Strong for recorded category; insufficient for crew versus maintenance | 20,172,956 minutes, 32.20%; internal logs are unavailable. |
| NAS / capacity | Strong for recorded NAS; weak for a specific congestion mechanism | 14,335,762 minutes, 22.88%; NAS is broader than a capacity shortage. |
| Weather | Strong for cancellation label; insufficient for independent attribution | 54.35% of cancellations are weather-coded; measured weather is absent. |
| Time-of-day accumulation | Strong association; moderate operational interpretation | Airline–origin–month comparison retains +10.06 minutes; residual confounding and selection remain. |
| A few extreme flights explain everything | Not supported | Removing >360-minute delays leaves 5.60% severe risk and a late-day gap. |
| Airport-code issue explains every pattern | Not supported for system trends | October joins fail, but system/airline/time coverage remains full year. |
| Aircraft-specific maintenance failure | Insufficient data | Tail differences alone do not identify a technical defect. |

The **62,651,867 reported cause minutes** cover 90.66% of 69,103,367 positive delay minutes, because arrivals delayed 1–14 minutes have no cause report. Late aircraft plus airline represents 72.04% of **reported cause minutes**, not 72.04% of all business harm. Recorded categories are evidence about reporting, not independent causal verification.

## Business Impact

The 430,662 disrupted scheduled flights establish the scale of the reliability burden; 325,591 severely delayed completed flights indicate substantial recovery needs despite an early median arrival. Possible consequences include rebooking workload, connection risk, aircraft/crew recovery pressure and lower schedule reliability.

Passenger counts, missed connections, compensation, lost revenue and costs cannot be estimated from these files. Financial quantification requires loads/manifests, connection itineraries, crew duty, linked aircraft rotations, recovery actions and defensible unit costs. Proposed benefits remain hypotheses for a pilot.

## Recommendations

| Priority / problem | Evidence | Proposed action and owner | Expected effect | Success metric / confidence |
| --- | --- | --- | --- | --- |
| High: late-day recovery | Persistent evening gap, including matched/outlier checks | Network operations validates recent late-day ORD/LGA segments, then investigates rotations and recovery buffers with a comparison group | Reduce propagation where the mechanism is verified | Severe/disruption, p95, cancellations and utilization; moderate mechanism confidence |
| High: incomplete geography | October airport codes unresolved | Data owner obtains and independently verifies the crosswalk; checks join coverage and row conservation | Restore defensible full-year geography | Mapping completeness and stable flight counts; high confidence in the data need |
| Medium: carrier reliability | NK positive gaps; MQ high cancellation and selection sensitivity | Airline performance team investigates retained NK segments and MQ cancellation outcomes separately | Identify the appropriate operating process to change | Matched gap, cancellations and retained coverage on stable definitions; moderate for NK association, lower for MQ mechanism |
| Medium: misleading averages | Early median alongside 430,662 disruptions and p95=66 | BI owner displays exposure, both on-time denominators, cancellations/diversions, severe rates and tail metrics | Keep adverse outcomes visible | Independent reconciliation and coverage checks; high measurement confidence |
| Further investigation: true mechanisms and cost | No actual weather, linked rotations, crew or passenger costs | Link external operational records and evaluate a controlled pilot | Distinguish mechanisms and quantify impact | Linkage quality, recovery outcomes, passenger impact and a supported cost model; currently insufficient evidence |

Do not increase schedule buffers network-wide before testing utilization trade-offs. A lower completed-flight mean is not success if cancellations rise or flights disappear from the denominator.

## Power BI Story

Two language-specific files are provided: [English Power BI](https://github.com/MINNNZZ/flight-delay-operations-analytics/releases/tag/v1.0.0) and [Vietnamese Power BI](https://github.com/MINNNZZ/flight-delay-operations-analytics/releases/tag/v1.0.0). Both contain the same embedded model and seven pages; DAX formulas and technical field identifiers remain unchanged. Visible titles, narrative text, recommendation content and display labels are localized. The desktop application's menus follow its own language setting.

| Page | Main question and visual story | Management decision |
| --- | --- | --- |
| 1. Executive overview | KPI cards, monthly severe/cancellation trend, mean/median/p95 | Assess scale and tail risk together |
| 2. Airline performance | Severe/cancellation bars with sample-size tooltips | Select carrier segments for investigation; do not infer causes from ranks |
| 3. Airports: volume and risk | Fixed baseline top lists for risk and total positive minutes; 11-month scope | Distinguish high-volume from high-risk priorities |
| 4. Routes: intervention priorities | Fixed route risk/volume lists with thresholds and exposure | Identify candidate route-level investigations |
| 5. Timing and delay accumulation | Hourly severe, mean/median and monthly rates | Investigate late-day recovery patterns |
| 6. Evidence on possible drivers | Recorded cause minutes and denominator caveats | Separate recorded labels from mechanisms |
| 7. Actions and monitoring | Localized static recommendation panel, pilot design and guardrails | Assign proposed owners and define evaluation metrics |

Baseline top lists are fixed, not dynamic rankings. Cause-category values and technical identifiers may retain source terminology. The original model was previously checked against 21 DAX KPIs; language-specific validation is recorded separately in [localization_verification.json](../powerbi/desktop/localization_verification.json). The statistical sensitivity tables and bootstrap intervals in this written report are not additional Desktop visuals.

## Success Metrics

Monitor severe arrivals per eligible completed arrival; cancellation/diversion/disruption per scheduled flight; on-time among completed arrivals and across the schedule; p95/p99 arrival delay; positive delay minutes; flight exposure; unresolved-code coverage; and retained matched-comparison coverage. Agree a recent baseline and targets before a pilot. Review comparable routes/time windows and protect against cancellation increases, reduced flight volume or eligibility changes. Utilization, recovery time and passenger outcomes need additional records.

## Limitations

The files describe 2015, not current operations. Geographic findings exclude October, whereas system/time/airline findings include it. The source files' provenance and some units are not independently certified. Comparisons are observational and retain unmeasured confounding. Common-support restrictions and finer strata alter the analyzed population. Cause fields are conditionally reported after outcomes. Only one year is available; recurrent seasonality is not established. Aircraft type, actual UTC offsets, weather, crew, maintenance, passengers and financial data are absent.

Historical resampling depends on the chosen blocks and month boundaries and cannot establish a future or causal effect. Cancellation differences are not adjusted by completed-flight carrier comparisons. The Power BI model's embedded source paths should be reviewed before refresh after workspace moves. Localization does not change or re-estimate the underlying data.

## Next Steps

1. Obtain recent flight data, validate its source and repeat quality/coverage checks rather than carrying historical conclusions forward.
2. Resolve October airport identifiers with an independently checked crosswalk.
3. Link rotations, actual dates/timezones, weather and recovery records to test the most plausible mechanisms.
4. Define an operational pilot with stable comparison groups, recent baselines and cancellation/utilization guardrails.
5. Add passenger/connection and cost evidence before quantifying business losses or savings.

The central analytical lesson is to keep **population selection, adjustment, observed association and causal explanation separate**. Every management claim should be tied to its denominator, scope, exposure and the evidence actually available.

Evidence: [analysis summary](analysis_summary.json), [full-export verification](verification.json), [robustness summary](robustness_summary.json), [new statistical review](skill_review/statistical_review.json), [carrier sensitivity](skill_review/carrier_comparison_sensitivity.csv), [day-block stability](skill_review/time_block_stability.csv) and the underlying tables in `reports/tables/`.
