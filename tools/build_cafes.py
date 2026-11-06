#!/usr/bin/env python3
"""全区の認知症カフェを、tools/cafes/*.json から ninchisho_cafe_other_wards.geojson に組み立てる。
位置は国土地理院の住所検索（住所からの推定）。結果の一致状況を表示する。"""
import json, glob, time, urllib.parse, urllib.request, os, sys
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
cache_p = os.path.join(here, 'geocode_cache.json')
cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
def geocode(addr):
    if addr in cache: return cache[addr]
    u = 'https://msearch.gsi.go.jp/address-search/AddressSearch?q=' + urllib.parse.quote(addr)
    r = json.load(urllib.request.urlopen(u, timeout=30))
    cache[addr] = [(x['properties']['title'], x['geometry']['coordinates']) for x in r][:1]
    time.sleep(0.3)
    return cache[addr]
feats = []; bad = []
for f in sorted(glob.glob(os.path.join(here, 'cafes', '*.json'))):
    d = json.load(open(f, encoding='utf-8'))
    for r in d['cafes']:
        if 'lonlat' in r:
            ll = r['lonlat']
            ok = (isinstance(ll, (list, tuple)) and len(ll) == 2
                  and all(isinstance(v, (int, float)) for v in ll)
                  and 138.9 <= ll[0] <= 140.0 and 35.4 <= ll[1] <= 35.95)   # 東京23区の範囲（経度・緯度の取り違えも検出）
            if not ok: bad.append((d['ward'], r['name'], str(ll))); continue
            title, xy, src = r.get('geocode_match', '地図サイトの座標'), [float(ll[0]), float(ll[1])], '地図サイト由来の座標（未確認）'
        else:
            g = geocode(r.get('geocode_query', r['address']))
            if not g: bad.append((d['ward'], r['name'], r['address'])); continue
            title, xy = g[0]
            src = '国土地理院 住所検索（住所からの推定・未確認）'
        p = {
            'name': r['name'], 'category': r.get('category', '認知症カフェ'), 'ward': d['ward'],
            'district': r.get('district', ''), 'venue': r.get('venue', ''), 'address': r['address'],
            'schedule': r.get('schedule', ''), 'fee': r.get('fee', '記載なし'),
            'reservation': r.get('reservation', '記載なし'), 'paused': r.get('paused', False),
            'geocode': src, 'geocode_match': title, **({'geocode_note': r['geocode_note']} if r.get('geocode_note') else {}),
            'source': d['source'], 'source_url': d['source_url'],
            'contact_org': r.get('contact_org', ''), 'phone': r.get('phone', ''),
        }
        if r.get('email'): p['email'] = r['email']
        feats.append({'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': xy}, 'properties': p})
        print(d['ward'], '|', r['name'], '|', r['address'], '->', title)
json.dump(cache, open(cache_p, 'w'), ensure_ascii=False)
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(root, 'ninchisho_cafe_other_wards.geojson'), 'w'), ensure_ascii=False, indent=1)
print('total', len(feats), 'ungeocoded', bad)
