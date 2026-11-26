import argparse
from collections import defaultdict
from math import sqrt
from pathlib import Path
import json
from statistics import median

ROOT = Path(__file__).resolve().parent


def wilson(successes, total):
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z*z/total
    center = (p + z*z/(2*total)) / denominator
    radius = z * sqrt(p*(1-p)/total + z*z/(4*total*total)) / denominator
    return [round(max(0, center - radius), 4), round(min(1, center + radius), 4)]


def summary(book):
    eligible = defaultdict(list)
    for replicate in book['replicates']:
        for test, record in replicate['scores'].items():
            eligible[test].append(record)
    result = {}
    for test, records in sorted(eligible.items()):
        rejects = sum(r['p'] <= .05 for r in records)
        result[test] = {
            'rejections': rejects,
            'eligible_books': len(records),
            'total_books': len(book['replicates']),
            'rejection_fraction': round(rejects/len(records), 4),
            'wilson_95': wilson(rejects, len(records)),
            'median_observed': round(median(r['observed'] for r in records), 6),
            'median_null_mean': round(median(r['null_mean'] for r in records), 6),
            'median_excess': round(median(r['observed'] - r['null_mean'] for r in records), 6),
            'median_supported_lags': median(r['lags'] for r in records),
            'median_pairs_summed_over_lags': median(sum(r['pairs_by_lag'].values()) for r in records),
        }
        for lag in ('1', '20', '40'):
            available = [r['pairs_by_lag'][lag] for r in records if lag in r['pairs_by_lag']]
            if available:
                result[test]['books_supporting_lag_' + lag] = len(available)
                result[test]['median_pairs_lag_' + lag] = median(available)
    return {'regime':book['regime'], 'eligible_character_slots':book['total_slots'],
            'books':len(book['replicates']), 'median_hit_rate':round(median(r['hit_count']/book['total_slots'] for r in book['replicates']),5),
            'tests':result}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path, default=ROOT, nargs="?")
    args = parser.parse_args()
    files = [args.directory / f'scenario-{i}.json' for i in range(9)]
    books = [summary(json.loads(file.read_text())) for file in files]
    print(json.dumps(books, indent=2, sort_keys=True))
