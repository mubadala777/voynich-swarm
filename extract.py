"""Extract Sanjana's historical romanization from Dinkard XI–XIII scan OCR.

Requires Python 3.12+ and PyMuPDF 1.26.6. All three source PDFs are pinned.
The embedded training intervals were selected by footnote-rule geometry on
alternate volume XI pages. The three-band detector uses these intervals to
learn body, original-script OCR, and apparatus character distributions.
"""
import argparse
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

import fitz


VOLUMES = (
    (11, 'dinkard-xi.pdf', 19, 121,
     '31deefc65b2ac3950fddd1af9e7cc215cd3da04c8076f22667175539f85061ab'),
    (12, 'dinkard-xii.pdf', 21, 124,
     '171f0995400453abac3a5e71a15ff447ba0735082cc4844067f3d88a0a3cc64a'),
    (13, 'dinkard-xiii.pdf', 39, 140,
     'abde6e85c5775e887a28926e46e4e3daf451960fc31b25fa292ecab80484c985'),
)

# Volume XI PDF page number, first and last transliteration line centers,
# and apparatus rule, all normalized to page height.
SEED_BANDS = (
    (21, 0.539, 0.752, 0.783),
    (23, 0.543, 0.763, 0.795),
    (25, 0.566, 0.802, 0.833),
    (27, 0.568, 0.82, 0.854),
    (29, 0.553, 0.767, 0.796),
    (31, 0.54, 0.773, 0.802),
    (33, 0.562, 0.821, 0.851),
    (35, 0.542, 0.775, 0.802),
    (37, 0.564, 0.8, 0.827),
    (39, 0.512, 0.718, 0.751),
    (41, 0.524, 0.723, 0.744),
    (43, 0.553, 0.795, 0.824),
    (45, 0.52, 0.703, 0.732),
    (47, 0.548, 0.773, 0.797),
    (49, 0.601, 0.829, 0.858),
    (51, 0.539, 0.757, 0.794),
    (55, 0.525, 0.732, 0.759),
    (57, 0.556, 0.81, 0.841),
    (59, 0.541, 0.771, 0.795),
    (61, 0.506, 0.712, 0.74),
    (63, 0.542, 0.775, 0.805),
    (67, 0.549, 0.784, 0.812),
    (69, 0.523, 0.783, 0.814),
    (71, 0.549, 0.793, 0.818),
    (73, 0.559, 0.788, 0.815),
    (75, 0.584, 0.842, 0.872),
    (77, 0.537, 0.799, 0.827),
    (79, 0.572, 0.811, 0.843),
    (81, 0.51, 0.715, 0.741),
    (83, 0.559, 0.817, 0.846),
    (85, 0.512, 0.726, 0.759),
    (87, 0.554, 0.81, 0.843),
    (89, 0.595, 0.849, 0.88),
    (99, 0.557, 0.815, 0.842),
    (101, 0.586, 0.824, 0.849),
    (103, 0.572, 0.822, 0.851),
    (105, 0.594, 0.849, 0.874),
    (107, 0.651, 0.842, 0.869),
    (109, 0.582, 0.827, 0.855),
    (111, 0.618, 0.875, 0.899),
    (115, 0.586, 0.836, 0.859),
    (119, 0.574, 0.812, 0.837),
)


def rows(page):
    data = []
    for word in page.get_text('words'):
        x, y0, x1, y1, text = word[:5]
        y = (y0 + y1) / 2
        data.append((y,x,x1,text))
    groups = []
    for y,x,x1,text in sorted(data):
        if groups and abs(y - groups[-1][0]) <= .008*page.rect.height:
            groups[-1][1].append((x,x1,text))
        else:
            groups.append((y,[(x,x1,text)]))
    out=[]
    for y, words in groups:
        _,_,tokens=zip(*sorted(words))
        out.append((y,' '.join(tokens)))
    return out


def letters(s):
    t=unicodedata.normalize('NFKD',s.lower())
    chars=[]
    for c in t:
        if unicodedata.combining(c):
            continue
        if c.isalpha():
            chars.append(c if 'LATIN' in unicodedata.name(c,'') else '#')
        else:
            chars.append(' ')
    return ' '.join(''.join(chars).split())


def grams(s):
    s='^'+letters(s)+'$'
    return Counter(s[i:i+3] for i in range(len(s)-2))


def make_models(pdf):
    labels = tuple(Counter() for _ in range(3))
    with fitz.open(pdf) as doc:
        for page_number, first, last, footer in SEED_BANDS:
            page = doc[page_number - 1]
            for y, line in rows(page):
                y /= page.rect.height
                if y < .12 or y > .94:
                    continue
                if y + .013 < first:
                    index = 0
                elif first - .002 <= y <= last + .002:
                    index = 1
                elif y > footer + .005:
                    index = 2
                else:
                    continue
                labels[index].update(grams(line))
    vocabulary = set.union(*(set(counts) for counts in labels))
    return tuple((counts, math.log(sum(counts.values()) + len(vocabulary) * .4))
                 for counts in labels)


def score_line(line,models):
    g=grams(line)
    return tuple(sum(v*(math.log(n[k]+.4)-total) for k,v in g.items()) for n,total in models)


def band(page,models):
    h=page.rect.height
    data=[(y/h,l) for y,l in rows(page) if .15 < y/h <= .92 and len(letters(l))>=3]
    if len(data)<7:
        return [],{'reason':'not enough text rows'}
    nodes=[score_line(line,models) for _,line in data]
    cumul=[[0] for _ in models]
    for ss in nodes:
        for components,val in zip(cumul,ss):
            components.append(components[-1]+val)
    best=None
    for i,(begin,_) in enumerate(data):
        if not .30 <= begin <= .68:
            continue
        # Page transitions are marked by whitespace/rules and appear between rows.
        start_gap=begin-data[i-1][0] if i else .02
        for j in range(i+3,len(data)):
            end=data[j][0]
            if end > .90 or end-begin > .39:
                break
            before=cumul[0][i]
            roman=cumul[1][j+1]-cumul[1][i]
            after=cumul[2][-1]-cumul[2][j+1]
            end_gap=data[j+1][0]-end if j+1<len(data) else .03
            s=before+roman+after+95*(start_gap+end_gap)
            candidate=s,i,j
            if best is None or candidate > best:
                best=candidate
    if best is None:
        return [],{'reason':'no admissible band'}
    _,i,j=best
    selected=data[i:j+1]
    values=[r-max(l,p) for l,r,p in nodes[i:j+1]]
    if sum(values) / max(1, sum(len(letters(line)) for _,line in selected)) < .50:
        return [],{'reason':'weak roman support','start':selected[0][0],'end':selected[-1][0]}
    return selected,{'start':round(selected[0][0],3),'end':round(selected[-1][0],3),
                     'first_score':round(values[0],1),'last_score':round(values[-1],1),
                     'low_rows':sum(v<0 for v in values),'lines':len(selected),
                     'first_text':selected[0][1][:100],'last_text':selected[-1][1][-100:]}


def clean_line(t):
    if re.match(r'^(?:transliteration of the pahlavi text|chapter\s+\w+\.$)',t,re.I):
        return ''
    # Remove numbered chapter and sentence locators. Treat common OCR lookalikes as numerals only in a syntactic locator.
    t=re.sub(r'(?:^|(?<=\. ))[IVXLCDMΙΧΟΛΜΥΠιχουπivxlcdm]{2,10}[.,:;]+\s+(?=[(A-ZÀ-Ö])',' ',t)
    # Keep casing/special Latin characters. The normalizer downstream folds diacritics.
    t=re.sub(r'\([0-9Il]+[.,]?\)', ' ', t)
    return re.sub(r'\s+',' ',t).strip()


def keep(c):
    return (c.isalpha() and 'LATIN' in unicodedata.name(c,'')) or unicodedata.combining(c)


def prepare_page(page):
    rows = []
    dropped = 0
    for line in unicodedata.normalize('NFC', page).splitlines():
        retained = []
        for token in line.split():
            if any(c.isalpha() and 'LATIN' not in unicodedata.name(c, '') for c in token):
                dropped += 1
                continue
            retained.append(''.join(c if keep(c) else ' ' for c in token))
        line = re.sub(r' +', ' ', ' '.join(retained)).strip()
        if line:
            rows.append(line)
    return '\n'.join(rows), dropped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf_directory', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    for _, name, _, _, sha in VOLUMES:
        if hashlib.sha256((args.pdf_directory / name).read_bytes()).hexdigest() != sha:
            raise ValueError(f'Dinkard scan has unexpected checksum: {name}')

    models = make_models(args.pdf_directory / VOLUMES[0][1])
    gathered = []
    audit = []
    for volume, name, first_page, last_page, _ in VOLUMES:
        with fitz.open(args.pdf_directory / name) as doc:
            for page in range(first_page, last_page + 1):
                selected, info = band(doc[page - 1], models)
                # The last Book Pahlavi row on this leaf was misclassified as Roman.
                if (volume, page) == (12, 49):
                    if selected[0][1] != 'CUNT pa 4)':
                        raise ValueError('Unexpected OCR at the reviewed vol. XII PDF page 49')
                    selected = selected[1:]
                    info.update(start=round(selected[0][0], 3), first_text=selected[0][1][:100],
                                lines=len(selected), reviewed_exclusion='CUNT pa 4)')
                raw_text = '\n'.join(filter(None, (clean_line(line) for _, line in selected)))
                text, dropped = prepare_page(raw_text)
                if not text:
                    raise ValueError(f'No text on volume {volume}, PDF page {page}')
                gathered.append(text)
                audit.append({'volume': volume, 'page': page, 'dropped_non_latin_tokens': dropped, **info})

    encoded = ('\n\n'.join(gathered) + '\n').encode('utf-8')
    args.output.write_bytes(encoded)
    args.output.with_suffix('.audit.json').write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n')
    print(len(encoded), hashlib.sha256(encoded).hexdigest(), 'pages', len(gathered),
          'dropped OCR tokens', sum(row['dropped_non_latin_tokens'] for row in audit))


if __name__ == '__main__':
    main()
