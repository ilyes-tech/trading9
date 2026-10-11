"""Bounded Crossref bibliography lookup. Research-only, no authorization effects."""
import argparse, json, urllib.parse, urllib.request

def lookup(query, limit):
    if not query.strip() or not 1 <= limit <= 5:
        raise ValueError('INVALID_QUERY_OR_LIMIT')
    url = 'https://api.crossref.org/works?' + urllib.parse.urlencode({'query.bibliographic': query, 'rows': limit, 'select': 'DOI,title,published,author,type'})
    req = urllib.request.Request(url, headers={'User-Agent': 'TradingAI-JARVIS-Research/1.0 (bibliographic-only)'})
    with urllib.request.urlopen(req, timeout=12) as response:
        payload = json.load(response)
    results = []
    for item in payload.get('message', {}).get('items', [])[:limit]:
        doi = item.get('DOI', '')
        if not isinstance(doi, str) or not doi.startswith('10.'):
            continue
        title = item.get('title', [''])
        title = title[0] if isinstance(title, list) and title else ''
        results.append({'doi': doi, 'title': str(title)[:300], 'url': 'https://doi.org/' + urllib.parse.quote(doi, safe='/'), 'published': item.get('published', {}).get('date-parts', []), 'type': item.get('type')})
    return {'kind': 'V57_SCIENTIFIC_SOURCE_LOOKUP_V1', 'status': 'BIBLIOGRAPHY_ONLY', 'query': query, 'results': results, 'novelty_proven': False, 'independent_replication_proven': False, 'research_execution_authorized': False, 'orders_allowed': False, 'mt5_allowed': False, 'holdout_allowed': False}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', required=True)
    parser.add_argument('--limit', type=int, default=3)
    args = parser.parse_args()
    try:
        print(json.dumps(lookup(args.query, args.limit), ensure_ascii=False, indent=2))
    except Exception as exc:
        print('STOP|FAIL|SCIENTIFIC_SOURCE_LOOKUP|' + type(exc).__name__ + ':' + str(exc)[:200])
        raise SystemExit(3)
