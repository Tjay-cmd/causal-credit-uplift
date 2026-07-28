# Segment profile narrative (Phase 1 Hillstrom)

Built from saved test predictions only - no retraining.

## Persuadables (top decile by predicted CATE)

**T-learner:** Persuadables in this data tend to look like: recency mean/median 4.3/3.0 months, history $459/$387 (mean/median), mens=82.3%, womens=77.6%, newbie=55.9%; modal history_segment=3) $200 - $350 (30.9%), zip_code=Urban (44.8%), channel=Web (50.5%); observed visit treated/control=24.1%/12.6% (obs uplift=+0.116).

**CausalForestDML:** Persuadables in this data tend to look like: recency mean/median 3.9/3.0 months, history $506/$407 (mean/median), mens=87.1%, womens=83.6%, newbie=56.3%; modal history_segment=3) $200 - $350 (31.2%), zip_code=Urban (47.9%), channel=Web (42.8%); observed visit treated/control=28.9%/13.5% (obs uplift=+0.154).

## Sleeping Dogs / low-uplift (bottom decile by predicted CATE)

**T-learner:** Low/no-uplift customers (bottom decile; CATE still non-negative) tend to look like: recency mean/median 5.1/5.0 months, history $302/$189 (mean/median), mens=53.4%, womens=52.5%, newbie=45.7%; modal history_segment=1) $0 - $100 (33.8%), zip_code=Surburban (40.4%), channel=Web (39.8%); observed visit treated/control=20.5%/10.6% (obs uplift=+0.098). Bottom-decile mean predicted CATE is still non-negative (0.0168); labeling as low/no uplift rather than Sleeping Dogs. Share with CATE < 0: 14.4%.

**CausalForestDML:** Low/no-uplift customers (bottom decile; CATE still non-negative) tend to look like: recency mean/median 7.2/8.0 months, history $128/$82 (mean/median), mens=66.9%, womens=33.1%, newbie=54.5%; modal history_segment=1) $0 - $100 (58.7%), zip_code=Surburban (46.7%), channel=Web (64.7%); observed visit treated/control=18.8%/8.8% (obs uplift=+0.100). Bottom-decile mean predicted CATE is still non-negative (0.0620); labeling as low/no uplift rather than Sleeping Dogs. Share with CATE < 0: 0.0%.

## Do the two models agree on who is in the top 10%?

Top-decile customer_id overlap between T-learner and CausalForestDML: **58.1%** (495 of 852 customers; Jaccard=0.409).

**Agreement flag:** MODERATE overlap - some shared persuadables, but a large unique slice per model; do not treat either top-decile list as definitive alone.

Where the models agree on membership, shared feature tilts are the safer reference for designing heterogeneity in a synthetic Phase 2 dataset.

## T-learner negative-CATE individuals (sanity check)

The ~14% negative-CATE share cited earlier is within the T-learner bottom decile; across the full test set that is only **123 / 8,523 customers (1.4%)**, mean CATE=-0.059. Comparing their category mix to the full test set, this does **not** look like scattered noise around a positive mean: they are **under-represented** in `history_segment` $0- (13% vs 36% test, **-23 pp**) and **over-represented** in high-spend bands especially $750-,000 (21% vs 3%, **+18 pp**), plus **Rural** zip (32% vs 15%, **+17 pp**) and **Multichannel** (28% vs 12%, **+15 pp**), with Urban under-weight (**-17 pp**). So the negative scores concentrate among higher-history / Rural / Multichannel customers rather than being randomly sprinkled across categories.

## Closing note (Phase 1)

The concentrated negative-CATE finding (high-spend, Rural, Multichannel customers) is treated as a plausible but low-sample finding (1.4% of test set), not a confirmed population effect. It informs Phase 2 design in one specific way: the synthetic credit dataset's "Sleeping Dogs" segment will be defined around an analogous logic - customers already saturated on a channel/contact dimension, where additional treatment plausibly backfires - rather than an arbitrary or purely score-based rule.

Phase 1 is closed. No further Hillstrom analysis planned.
