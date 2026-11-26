# Ordered prefix patterns in the public f69v radial labels

This test follows earlier work on the [28 radial loci](https://github.com/Ayan-Bandyopadhyay/voynich-swarm/pull/471), [initials and lengths](https://github.com/Ayan-Bandyopadhyay/voynich-swarm/pull/377), and [the three scan-cued starts](https://github.com/Ayan-Bandyopadhyay/voynich-swarm/pull/484). It examines shared initial runs extending beyond one symbol. An independent pass on the Yale scan associates one radial writing locus with each bar. The rotation search treats that locus order as observable. [Yale f69v canvas](https://collections.library.yale.edu/manifests/oid/2002046/canvas/1006199)

`plan.json` specifies the score, alignments and control distributions. In `sources.json`, historical names are represented as ordered symbol classes after the documented normalization. Within each source, each number denotes one distinct normalized unit. Replacing units by numbers preserves prefixes, lengths, initial classes and equality patterns exactly. Provenance points to the named editions. The manuscript uses EVA-basic units, with boundaries kept during segmentation and the units then collected by locus.

Put the script, plan and data in the same directory. Run from a Voynich Swarm checkout with verified input downloads. The outputs were reproduced using Python 3.12 and NumPy 2.3.5. [Public practice code used for the audit](https://github.com/Ayan-Bandyopadhyay/voynich-swarm/tree/bc9fdb9bde7bc932f0dec8c5afcce38e57e28dae)

```sh
python3 /path/to/ordered_prefix.py > observed.json
python3 /path/to/ordered_prefix.py --simulate > synthetic.json
```

The main nulls retain the order of lengths and the exact multiset of labels on the shuffled side. The additional sensitivity also fixes initial-symbol classes. For each shuffled list, repeat the same circular maximization. Scan-cued starts are a separate sensitivity. The synthetic check assesses the chosen score on exact and noisy prefix-preserving encodings of the same source lists.
