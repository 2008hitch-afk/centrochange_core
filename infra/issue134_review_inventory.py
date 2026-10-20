#!/usr/bin/env python3
"""Review actual browser-rendered text, without a fixed legacy blacklist.

Input/output are private evidence files. Every unique visible string is kept
for human review; risk hints merely sort the inventory and never confer PASS.
"""
import argparse
import csv
import json
from pathlib import Path
import re

ENGLISH_GRAMMAR = re.compile(
    r'\b(?:the|and|with|for|from|once|will|please|click|select|make|against|'
    r'between|before|after|instead|only|your|this|these|existing|available|'
    r'issued|discounted|rounded|outstanding|attachment|followup|ledger|'
    r'payment|invoice|supplier|customer|item|practitioner|filter|transfer)\b', re.I)
SECOND_TIME = re.compile(r'(?<!\d)\d{1,2}:\d{2}:\d{2}(?!\d)')
ISO_DATE = re.compile(r'(?<!\d)20\d{2}-\d{2}-\d{2}(?!\d)')
AM_PM = re.compile(r'(?<!\w)\d{1,2}:\d{2}\s*(?:AM|PM)\b', re.I)


def classify(text):
    """Hint only; all rows are retained, including technical/audit strings."""
    risks=[]
    if ENGLISH_GRAMMAR.search(text): risks.append('POSSIBLE_ENGLISH')
    if SECOND_TIME.search(text): risks.append('VISIBLE_SECONDS')
    if ISO_DATE.search(text): risks.append('VISIBLE_ISO_DATE')
    if AM_PM.search(text): risks.append('VISIBLE_AM_PM')
    if text.lstrip().startswith(('{','[')): risks.append('POSSIBLE_CANONICAL_PAYLOAD')
    return '|'.join(risks) or 'MANUAL_REVIEW'


def review(files, output):
    records={}
    for source in files:
        for screen in json.loads(Path(source).read_text()):
            for item in screen.get('items', []):
                key=(item['kind'],item['text'])
                row=records.setdefault(key, {'kind':item['kind'], 'text':item['text'],
                    'hint':classify(item['text']), 'count':0, 'examples':set()})
                row['count']+=1
                row['examples'].add(f"{screen.get('role')}:{screen.get('width')}:{screen.get('screen')}")
    with Path(output).open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=('hint','kind','text','count','examples'))
        writer.writeheader()
        for row in sorted(records.values(),key=lambda row:(row['hint']=='MANUAL_REVIEW',
                                                          -row['count'],row['text'])):
            writer.writerow({**row,'examples':'; '.join(sorted(row['examples'])[:4])})
    Path(output).chmod(0o600)
    counts={}
    for row in records.values():
        for hint in row['hint'].split('|'): counts[hint]=counts.get(hint,0)+1
    return {'unique_visible_items':len(records),'review_hints':counts}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('output')
    parser.add_argument('inventories',nargs='+')
    args=parser.parse_args()
    print(json.dumps(review(args.inventories,args.output),sort_keys=True))
