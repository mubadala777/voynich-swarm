"""Public experimental calibration for conditional EVA occurrence-gap tests."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path.cwd()))
from vs import corpus

ALPHABET = frozenset('acdefghiklmnopqrsty')
BANDS = {'short_1_5': tuple(range(1, 6)), 'long_11_40': tuple(range(11, 41)), 'lag_20': (20,)}
LAGS = tuple(sorted({i for band in BANDS.values() for i in band}))
MAX_LAG = max(LAGS)
BASE_RATE = 0.16
SEED = 19026011
MIN_PAIRS = 25
RUNS = 64
PERMUTATIONS = 99
ALPHA = 0.05
SCENARIOS = (
    ('iid_constant', 'iid', 0.0, 0.0),
    ('iid_page_rate_shifts', 'iid', 1.2, 0.0),
    ('iid_paragraph_rate_shifts', 'iid', 0.0, 1.2),
    ('iid_page_and_paragraph_shifts', 'iid', 1.2, 1.2),
    ('bursts_amplitude_0_20', 'burst', 0.20, 5.0),
    ('bursts_amplitude_0_45', 'burst', 0.45, 5.0),
    ('bursts_amplitude_0_75', 'burst', 0.75, 5.0),
    ('lag20_copy_probability_0_30', 'gap_copy', 0.30, 20),
    ('lag20_copy_probability_0_80', 'gap_copy', 0.80, 20),
)


def line_ids(pages):
    return {line.id for page in pages for line in page.lines
            if line.unit == 'P' and line.words and all(set(w) <= ALPHABET for w in line.words)}


def layout(pages, keep):
    books = []
    for page in pages:
        paragraphs = []
        paragraph = []
        for line in page.lines:
            if line.unit != 'P':
                continue
            if (line.para_start or line.id not in keep) and paragraph:
                paragraphs.append(paragraph)
                paragraph = []
            if line.id in keep:
                paragraph.append((line.id, ' '.join(line.words)))
            if line.para_end and paragraph:
                paragraphs.append(paragraph)
                paragraph = []
        if paragraph:
            paragraphs.append(paragraph)
        if paragraphs:
            books.append((page.id, paragraphs))
    return books


def template(book):
    offset = 0
    pages = []
    for page_id, paragraphs in book:
        groups = []
        for lines in paragraphs:
            text = ' '.join(text for _, text in lines)
            positions = np.fromiter((offset + i for i, c in enumerate(text) if c != ' '), dtype=np.int32)
            groups.append((lines[0][0], text, positions, offset))
            offset += len(text) + 1
        pages.append((page_id, groups))
    return pages


def masks(book):
    paragraphs = [g[2] for _, groups in book for g in groups]
    group_ids = []
    start = 0
    for _, groups in book:
        group_ids.append(slice(start, start + len(groups)))
        start += len(groups)
    pages = [np.concatenate(paragraphs[s]) for s in group_ids]
    return paragraphs, pages, group_ids


def concatenate_groups(paragraphs, group_slices):
    return [np.concatenate(paragraphs[s], axis=-1) for s in group_slices]


def sample_positions(slots, count, repetitions, rng):
    if not count:
        return np.empty((repetitions, 0), dtype=np.int32)
    scores = rng.random((repetitions, len(slots)))
    draw = np.argpartition(scores, count - 1, axis=1)[:, :count]
    draw.sort(axis=1)
    return slots[draw]


def gap_curve(groups, centered):
    repetitions = groups[0].shape[0]
    counts = np.zeros(MAX_LAG + 1, dtype=np.int64)
    moments = np.zeros((5, repetitions, MAX_LAG + 1))
    for hits in groups:
        gaps = np.diff(hits, axis=1).astype(np.float64)
        n = gaps.shape[1]
        if n <= 2:
            continue
        if centered:
            gaps -= gaps.mean(axis=1, keepdims=True)
        for h in LAGS:
            if n <= h + 1:
                break
            x, y = gaps[:, :-h], gaps[:, h:]
            counts[h] += n - h
            moments[0, :, h] += x.sum(axis=1)
            moments[1, :, h] += y.sum(axis=1)
            moments[2, :, h] += np.einsum('ij,ij->i', x, x)
            moments[3, :, h] += np.einsum('ij,ij->i', y, y)
            moments[4, :, h] += np.einsum('ij,ij->i', x, y)
    x, y, xx, yy, xy = moments
    with np.errstate(divide='ignore', invalid='ignore'):
        if centered:
            coefficient = xy / np.sqrt(xx * yy)
        else:
            coefficient = (xy - x * y / counts) / np.sqrt((xx - x*x/counts)*(yy-y*y/counts))
    coefficient[:, counts < MIN_PAIRS] = np.nan
    return coefficient, counts


def outcome(groups, centered):
    curve, counts = gap_curve(groups, centered)
    result = {}
    for name, lags in BANDS.items():
        lags = np.asarray(lags)
        viable = lags[np.isfinite(curve[:, lags]).all(axis=0)]
        if not len(viable):
            result[name] = None
            continue
        samples = curve[:, viable].mean(axis=1)
        first, simulations = samples[0], samples[1:]
        p = (1 + np.count_nonzero(simulations >= first - 1e-12)) / len(samples)
        result[name] = {'observed': float(first), 'null_mean': float(simulations.mean()),
                        'p': float(p), 'lags': int(len(viable)),
                        'pairs_by_lag': {str(h): int(counts[h]) for h in viable}}
    return result


def with_observed(obs, nulls):
    return [np.concatenate((first[None,:], otherwise), axis=0)
            for first, otherwise in zip(obs, nulls, strict=True)]


def compare(observed, paragraph_slots, page_slots, slices, repetitions, rng):
    actual_pages = concatenate_groups(observed, slices)
    actual_global = np.concatenate(actual_pages)
    null_paragraphs = [sample_positions(slots, len(hits), repetitions, rng)
                       for slots, hits in zip(paragraph_slots, observed, strict=True)]
    null_pages = [sample_positions(slots, len(hits), repetitions, rng)
                  for slots, hits in zip(page_slots, actual_pages, strict=True)]
    both_paragraphs = with_observed(observed, null_paragraphs)
    both_pages = with_observed(actual_pages, null_pages)
    global_null = [sample_positions(np.concatenate(page_slots), len(actual_global), repetitions, rng)]
    return {
        'pooled_given_global_count': outcome(with_observed([actual_global], global_null), False),
        'page_centered_given_page_counts': outcome(both_pages, True),
        'page_centered_given_paragraph_counts': outcome(concatenate_groups(both_paragraphs, slices), True),
        'paragraph_centered_given_paragraph_counts': outcome(both_paragraphs, True),
    }


def adjusted_rates(lengths, contrast, target):
    offsets = contrast * np.where(np.arange(len(lengths)) % 2 == 0, -1., 1.)
    low, high = -35., 35.
    for _ in range(60):
        midpoint = (low + high) / 2
        rates = 1 / (1 + np.exp(-(midpoint + offsets)))
        if np.average(rates, weights=lengths) < target:
            low = midpoint
        else:
            high = midpoint
    return 1 / (1 + np.exp(-((low + high) / 2 + offsets)))


def burst_hits(length, amplitude, lifetime_gaps, rng):
    resample = -np.expm1(-BASE_RATE / lifetime_gaps)
    transitions = np.flatnonzero(rng.random(length) < resample)
    states = rng.choice([-1., 1.], size=len(transitions) + 1)
    lifecycle = np.searchsorted(transitions, np.arange(length), side='right')
    rates = BASE_RATE * (1 + amplitude * states[lifecycle])
    return np.flatnonzero(rng.random(length) < rates)


def recurrence_hits(length, probability, lag, rng):
    eligible = length + 1200
    past = rng.geometric(BASE_RATE, size=lag)
    out = []
    at = 0
    i = 0
    while at < eligible:
        for j in range(lag):
            if i == 0 or rng.random() >= probability:
                if i > 0:
                    past[j] = rng.geometric(BASE_RATE)
            at += past[j]
            if 1200 <= at < eligible:
                out.append(at - 1200)
        i += 1
    return np.asarray(out, dtype=int)


def synthetic(regime, paragraph_slots, page_slots, slices, rng):
    _, name, a, b = regime
    if name == 'iid':
        rates = adjusted_rates([len(slot) for slot in page_slots], a, BASE_RATE)
        assigned = []
        for s, p in zip(slices, rates, strict=True):
            assigned.extend(adjusted_rates([len(slot) for slot in paragraph_slots[s]], b, p))
        return [slots[np.flatnonzero(rng.random(len(slots)) < p)]
                for slots, p in zip(paragraph_slots, assigned, strict=True)]
    found = []
    for slots, s in zip(page_slots, slices, strict=True):
        indices = burst_hits(len(slots), a, b, rng) if name == 'burst' else recurrence_hits(len(slots), a, b, rng)
        page_hits = slots[indices]
        for para in paragraph_slots[s]:
            start = np.searchsorted(page_hits, para[0], side='left')
            end = np.searchsorted(page_hits, para[-1], side='right')
            found.append(page_hits[start:end])
    return found


def observed(book, symbol):
    return [np.fromiter((offset + i for i, c in enumerate(text) if c == symbol), dtype=np.int32)
            for _, groups in book for _,text,_,offset in groups]


def word_order_comparison(book, symbol, actual, slices, repetitions, rng):
    draws = []
    for _, groups in book:
        for _, text, _, offset in groups:
            words = text.split()
            shuffled = []
            for _ in range(repetitions):
                trial = ' '.join(rng.permutation(words))
                shuffled.append([offset + i for i, c in enumerate(trial) if c == symbol])
            draws.append(np.asarray(shuffled, dtype=np.int32))
    paired = with_observed(actual, draws)
    return {
        'page_centered_given_paragraph_word_multisets': outcome(concatenate_groups(paired, slices), True),
        'paragraph_centered_given_paragraph_word_multisets': outcome(paired, True),
    }


def scalar_lag_stats(row):
    flat = {}
    for kind, bands in row.items():
        for band, values in bands.items():
            if values is not None:
                flat[kind + '/' + band] = values
    return flat


def run_scenario(index, book, runs, permutations):
    rng = np.random.default_rng(np.random.SeedSequence([SEED, index]))
    pslots, pages, slices = masks(book)
    regime = SCENARIOS[index]
    data = []
    for iteration in range(runs):
        hits = synthetic(regime, pslots, pages, slices, rng)
        row = scalar_lag_stats(compare(hits, pslots, pages, slices, permutations, rng))
        data.append({'hit_count':sum(len(h) for h in hits),'scores':row})
    return {'regime':regime, 'total_slots':sum(map(len,pages)), 'replicates':data}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--scenario', type=int, choices=range(len(SCENARIOS)))
    mode.add_argument('--observe', action='store_true')
    parser.add_argument('--runs', type=int, default=RUNS)
    parser.add_argument('--permutations', type=int, default=PERMUTATIONS)
    args = parser.parse_args()
    practice = {code: corpus.split_pages('practice', code)[1] for code in ('zl', 'it')}
    matched = line_ids(practice['zl']) & line_ids(practice['it'])
    books = {code:template(layout(pages,matched)) for code,pages in practice.items()}
    if args.observe:
        outputs = {}
        for code, book in books.items():
            pslots, pages, slices = masks(book)
            outputs[code] = {}
            for i, symbol in enumerate(('o','r')):
                rng = np.random.default_rng(np.random.SeedSequence([SEED, 100, i]))
                hits = observed(book, symbol)
                scores = compare(hits, pslots, pages, slices, args.permutations, rng)
                scores.update(word_order_comparison(book, symbol, hits, slices, args.permutations, rng))
                outputs[code][symbol] = {'hits':sum(map(len,hits)), 'slots':sum(map(len,pages)),
                                         'scores':scores}
        print(json.dumps({'matched_lines':len(matched),'layouts':{code: {'pages':len(book), 'runs':sum(len(groups) for _,groups in book)} for code,book in books.items()}, 'results':outputs}, sort_keys=True))
    else:
        print(json.dumps(run_scenario(args.scenario, books['zl'], args.runs, args.permutations), sort_keys=True))


if __name__ == '__main__':
    main()
