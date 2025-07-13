import re, requests

url = "https://raw.githubusercontent.com/bol-van/rulist/refs/heads/main/reestr_hostname.txt"
allowed_tlds = ('.org', '.com', '.eu', '.xxx', '.to')
whitelist_patterns = ['rezka.ag', 'rutracker', 'ntc.party', 'prostovpn.org', 'rule34', 'paheal', 'e621.net', 'yande.re', 'pixiv', 'zerochan.net', 'donmai.us']
banned_keywords = ['kraken', 'zoo', 'poker', 'azino', 'asino', 'flibus.ta', 'flibusta', 'narko', 'luxury', 'slot', 'lucky', 'bet', 'avto', 'btc', 'bnb', 'usdt', 'ltc', 'bitcoin', 'litecoin', 'binance', 'crypto', 'onion', 'tor', 'market', 'shop', 'darknet', 'mef', 'ukraine', 'ulkan', 'crypto', 'trading', 'trade', 'admiral', 'lord', 'kino', 'kolhoz', 'kolxoz', 'gold', 'hydra', 'leon', 'immediate', 'kra', 'niger', 'save', 'egas', 'play', 'dj', 'dl', 'online', 'forum', 'world', 'die', 'death', 'navalny', 'putin', 'vpn', 'proxy', 'parimatch', 'sport', 'call', 'vip', 'diamond', 'pasport', 'passport', 'pay', 'pin-', 'child', 'loli', 'deti', 'gay', 'trans', 'gender', 'film', 'king']

r = requests.get(url)
r.raise_for_status()
lines = r.text.splitlines()
res = set()

for line in lines:
    original = line.strip().lower()
    parts = original.split('.')
    d = '.'.join(parts[-2:]) if len(parts) >= 3 else original
    name = d.rsplit('.', 1)[0]
    
    if any(wp in d for wp in whitelist_patterns):
        res.add(d)
        continue
    
    if d[0].isdigit(): continue
    if re.match(r'^[a-zA-Z]{1,2}[^a-zA-Z]', d): continue
    if not d.endswith(allowed_tlds): continue
    if any(b in d for b in banned_keywords): continue
    if name[-1].isdigit(): continue
    if re.search(r'-\d+', d): continue
    if re.search(r'\d{3,}', d): continue
    if len(name) >= 2 and name[0] == name[1]: continue
    if d.count('-') > 1: continue
    if len(d) > 20: continue
    
    res.add(d)

with open("reestr.txt", "w", encoding="utf-8") as f:
    f.write('\n'.join(sorted(res)))
