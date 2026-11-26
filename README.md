# Conditional occurrence-gap calibration on public practice

This benchmark follows [the public local-rate audit](https://github.com/Ayan-Bandyopadhyay/voynich-swarm/pull/353). The analysis uses the matching 615 eligible paragraph lines of public Zandbergen–Landini and Takahashi practice on 31 pages. An eligible line contains only certain words made of the fixed ASCII EVA alphabet `acdefghiklmnopqrsty`. Cutting paragraph runs at omitted lines gives 128 Zandbergen–Landini runs and 131 Takahashi runs. The pooled and page statistics join retained runs with single spaces. The within-run statistic excludes all crossings between those runs.

A hit is an occurrence of a target EVA character. Gaps count raw EVA positions including the spacing between words. Synthetic hits occupy the non-space slots of the fixed Zandbergen–Landini layout. The pooled statistic uses Pearson correlation. The conditional statistics subtract each page or run's mean gap and pool lagged products and the corresponding squared norms. Each lag requires two eligible pairs within a contributing group and 25 pooled pairs. Lags 1–5 and 11–40 are averaged separately. Lag 20 is also evaluated on its own.

The position nulls keep the global count, each page's count or each paragraph run's count fixed. Within a stratum, all eligible locations are equally likely. The page statistic is also evaluated with the finer paragraph-count null, so the effect of preserving paragraph rates can be measured on the same page-level pairs. An intact-word null in the observed example shuffles words within their paragraph runs, preserving complete words and their multiplicities. Both types retain the page and paragraph order.

Each scenario has 64 simulated books and 99 conditional draws per test. The Monte Carlo p-value is `(1 + number of null scores at least as large) / 100`. Rejection means `p <= 0.05` for each displayed estimate. The summary includes Wilson intervals and pair support. The primary expected hit rate is 0.16. The two rate sensitivity runs use 0.124 and 0.036, close to the prevalences of `o` and `r` in the paired practice layouts. The simulated alternatives are:

- Independent hits at a constant rate or alternating page or paragraph rates. Alternating strata receive logit offsets of ±1.2, calibrated by the number of eligible slots to keep the expected mean fixed.
- A persistent hidden high/low state with rates `p*(1±a)`, amplitudes 0.20, 0.45 and 0.75, and redraw probability `1 - exp(-p/5)` per slot. The state starts in equilibrium independently on each page.
- Geometric occurrence gaps with 0.30 or 0.80 probability of copying the gap 20 occurrences earlier. Generate in eligible-slot coordinates, discard an initial 1,200 slots, and lay hits into the raw positions of each page. The layout and separators can attenuate the injected dependence.

The observational checks use `o` for a frequent symbol and `r` for the previously published lag-20 pattern. The transliterations are paired readings of the same pages. The observed p-values are descriptive, with the two symbols and bands kept separate.

Run from a checkout of [practice inputs and code at bc9fdb9](https://github.com/Ayan-Bandyopadhyay/voynich-swarm/tree/bc9fdb9bde7bc932f0dec8c5afcce38e57e28dae) after `python3 -m vs fetch`. The analysis used Python 3.12 and NumPy 2.3.5. Put this directory's three scripts in a directory of your choice and call them by path from the project checkout.

- `python3 /path/to/bench.py --scenario 0 > /path/to/primary/scenario-0.json`
- `python3 /path/to/rate_sensitivity.py --practice-rate o --scenario 0 > /path/to/rate-o/scenario-0.json`
- `python3 /path/to/rate_sensitivity.py --practice-rate r --scenario 0 > /path/to/rate-r/scenario-0.json`
- `python3 /path/to/bench.py --observe > /path/to/observed-comparisons.json`

Repeat each scenario command for indices 0–8. Run `python3 /path/to/summarize.py /path/to/primary` and likewise for the other two result directories. The primary seed is 19026011 and each scenario uses a child seed with its scenario index. The practice-rate runs add 20,000 or 30,000 to the seed.
