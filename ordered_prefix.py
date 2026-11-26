"""Test deeper shared prefixes in public f69v and published mansion lists."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path.cwd()))
from vs import corpus, ivtff

SIZE = 28
ALIGNMENTS = [(i, d) for d in (1, -1) for i in range(SIZE)]
ORIGINS = np.asarray([[(i - start) * direction % SIZE for i in range(SIZE)]
                      for start, direction in ALIGNMENTS])
SCAN_STARTS = [4, 5, 6]
ROOT = Path(__file__).resolve().parent


def labels(edition):
    page = next(p for p in corpus.pages(edition) if p.id == 'f69v')
    radial = {int(line.id.split('.')[1]): line.words for line in page.lines if line.unit == 'R'}
    assert set(radial) == set(range(4,32))
    return [tuple(g for word in radial[i] for g in ivtff.segment(word, 'eva-basic')) for i in range(4,32)]



def quality(seq):
    return all('?' not in c and '*' not in c for c in seq)


def depth(first, second):
    count = 0
    for a, b in zip(first,second):
        if a != b or count == 4:
            break
        count += 1
    return max(0, count - 1)


def similarity(labels):
    return np.asarray([[depth(a,b) for b in labels] for a in labels], dtype=np.float64)


def choose_shuffles(labels, repetitions, rng, condition_initial):
    by = defaultdict(list)
    for i,label in enumerate(labels):
        if quality(label) and label:
            group = (len(label), label[0]) if condition_initial else len(label)
            by[group].append(i)
    plans = np.tile(np.arange(SIZE), (repetitions,1))
    variation = 1
    for group in by.values():
        if len(group) > 1:
            original = np.asarray(group)
            plans[:,original] = rng.permuted(np.broadcast_to(original,(repetitions,len(group))), axis=1)
            variants = Counter(labels[i] for i in group)
            variation *= math.factorial(len(group)) // math.prod(math.factorial(c) for c in variants.values())
    return plans, variation


def standardize(v):
    centered = v - v.mean(axis=-1,keepdims=True)
    norm = np.linalg.norm(centered,axis=-1,keepdims=True)
    return np.divide(centered,norm,out=np.zeros_like(centered),where=norm>0), norm[...,0] > 0


def size_test(manuscript, names, repetitions, seed, condition_initial=False):
    rng = np.random.default_rng(seed)
    all_i, all_j = np.triu_indices(SIZE,k=1)
    both_known = np.asarray([quality(label) for label in manuscript])
    valid = both_known[all_i] & both_known[all_j]
    i,j = all_i[valid], all_j[valid]
    vm, hm = similarity(manuscript), similarity(names)
    vx, vgood = standardize(vm[i,j])
    hi,hj = ORIGINS[:,i],ORIGINS[:,j]
    hx,hgood = standardize(hm[hi,hj])
    if not vgood or not hgood.any():
        return {'status':'uninformative prefix variation','eligible_pairs':len(i)}
    observed = np.where(hgood, hx@vx, -np.inf)
    hist_idx, hist_var = choose_shuffles(names,repetitions,rng,condition_initial)
    man_idx, man_var = choose_shuffles(manuscript,repetitions,rng,condition_initial)
    vx_ensemble, goods = standardize(vm[man_idx[:,i],man_idx[:,j]])
    null_v = np.where(goods[:,None] & hgood[None,:], vx_ensemble @ hx.T, -np.inf)
    hist_scores = []
    for start in range(0,repetitions,48):
        selection = hist_idx[start:start+48,:]
        transformed, legal = standardize(hm[selection[:,hi],selection[:,hj]])
        hist_scores.append(np.where(legal,np.einsum('bai,i->ba',transformed,vx),-np.inf))
    null_h = np.concatenate(hist_scores)
    answer = {'eligible_pairs':len(i),'manuscript_nonzero_pairs':int(np.count_nonzero(vm[i,j])),
              'name_full_nonzero_pairs':int(np.count_nonzero(hm[all_i,all_j])),
              'distinct_length_class_arrangements':{'names':str(hist_var),'manuscript':str(man_var)}}
    for label, choices in (('all_56', np.arange(56)), ('clockwise_top_3', np.asarray(SCAN_STARTS))):
        best = choices[np.argmax(observed[choices])]
        value = observed[best]
        if not np.isfinite(value):
            answer[label] = {'status':'uninformative at allowed starts'}
            continue
        hit_h = np.max(null_h[:,choices],axis=1)
        hit_v = np.max(null_v[:,choices],axis=1)
        ph = (1+np.count_nonzero(hit_h>=value-1e-12))/(1+repetitions)
        pv = (1+np.count_nonzero(hit_v>=value-1e-12))/(1+repetitions)
        start,direction = ALIGNMENTS[best]
        answer[label] = {'score':float(value),'best_first_locus':'f69v.'+str(start+4),'direction':direction,
                         'p_names':float(ph),'p_manuscript':float(pv),'p_both':float(max(ph,pv))}
    return answer


def exact_heads(values, positions, width, alignments):
    report=[]
    for start,direction in alignments:
        expected = [(start+direction*(pos-1))%SIZE for pos in positions]
        stems = [values[i][:width] for i in expected]
        conflicts = any(len({stem[k] for stem in stems if len(stem)>k and quality((stem[k],))}) > 1
                        for k in range(width))
        report.append({'start':start+4, 'direction':direction, 'loci':[i+4 for i in expected],
                       'prefixes':[' '.join(p) for p in stems], 'known_conflict':conflicts,
                       'all_complete':all(len(p)==width and quality(p) for p in stems)})
    return report


def synthetic(names, repetitions=999, seeds=8, tag=0):
    vocabulary = sorted({letter for name in names for letter in name})
    reports = {}
    for noise in (0.0,0.02):
        runs = []
        for i in range(seeds):
            rng = np.random.default_rng(np.random.SeedSequence([690202,tag,i,int(noise*100)]))
            index = dict(zip(vocabulary,rng.permutation(len(vocabulary)),strict=True))
            start = rng.integers(SIZE)
            d = rng.choice([1,-1])
            placed = [None] * SIZE
            for n, name in enumerate(names):
                renamed = [int(rng.integers(len(vocabulary))) if rng.random()<noise else int(index[s]) for s in name]
                placed[(start+d*n)%SIZE] = tuple(str(j) for j in renamed)
            out = size_test(placed,names,repetitions,[690202,tag,100+i,int(noise*100)])
            fit = out.get('all_56',{})
            runs.append({'seed':i,'true_first_locus':'f69v.'+str(start+4),'true_direction':int(d),
                         'fit':fit})
        reports[str(noise)] = {'trials':runs,'p_both_at_most_0_01':sum(r['fit'].get('p_both',1)<=.01 for r in runs)}
    return reports


def holm(records):
    pairs = sorted((result['all_56']['p_both'], edi, source)
                   for edi, sources in records.items() for source,result in sources.items()
                   if 'p_both' in result.get('all_56',{}))
    adjusted = 0.0
    for i,(p,edi,source) in enumerate(pairs):
        adjusted = max(adjusted,min(1.,p*(len(pairs)-i)))
        records[edi][source]['all_56']['holm_p_both'] = adjusted


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--permutations',type=int,default=3999)
    parser.add_argument('--simulate',action='store_true')
    args=parser.parse_args()
    frozen=json.loads((ROOT/'sources.json').read_text())
    names = {key: [tuple(units) for units in value['normalized_codes']] for key, value in frozen.items()}
    if args.simulate:
        print(json.dumps({s:synthetic(values,tag=i) for i,(s,values) in enumerate(names.items())},ensure_ascii=False))
        return
    records,sens,head_checks={},{},{}
    for i,edi in enumerate(('zl','it')):
        man=labels(edi)
        records[edi]={}
        sens[edi]={}
        head_checks[edi]={}
        for j,(source,values) in enumerate(names.items()):
            records[edi][source]=size_test(man,values,args.permutations,[690202,i,j,0])
            sens[edi][source]=size_test(man,values,args.permutations,[690202,i,j,1],condition_initial=True)
            head_checks[edi][source] = exact_heads(man,frozen[source]['shared_head_positions'],2,
                                                   [ALIGNMENTS[k] for k in SCAN_STARTS])
        arabic = exact_heads(man,[22,23,24,25],3,ALIGNMENTS)
        head_checks[edi]['arabic_written_three_unit_head']={
            'all_alignments':len(arabic),'known_clashes':sum(row['known_conflict'] for row in arabic),
            'all_loci_clear_through_three':sum(row['all_complete'] for row in arabic),
            'potentially_compatible':[row for row in arabic if not row['known_conflict']],
        }
    holm(records)
    print(json.dumps({'primary':records,'initial_and_length_sensitivity':sens,'head_checks':head_checks,
                      'permutations_per_side':args.permutations,'seed':690202,
                      'protocol_sha256':hashlib.sha256((ROOT/'plan.json').read_bytes()).hexdigest(),
                      'source_sha256':hashlib.sha256((ROOT/'sources.json').read_bytes()).hexdigest()},ensure_ascii=False))


if __name__=='__main__':
    main()
