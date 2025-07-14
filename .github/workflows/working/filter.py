import re
import requests

url = "https://raw.githubusercontent.com/bol-van/rulist/refs/heads/main/reestr_hostname_resolvable.txt"
r = requests.get(url)
r.raise_for_status()
lines = r.text.splitlines()

def load_patterns(filename):
    contains, startswith = [], []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip().lower()
            if not line or line.startswith("#"):
                continue
            if line.startswith("="):
                startswith.append(line[1:])
            else:
                contains.append(line)
    return contains, startswith

whitelist_contains, whitelist_startswith = load_patterns(".github/workflows/working/whitelist.txt")
blacklist_contains, blacklist_startswith = load_patterns(".github/workflows/working/blacklist.txt")

allowed_tlds = ('.com','.org','.net','.us','.app','.biz','.fm','.tv','.is','.wtf','.xyz')

res = set()

for line in lines:
    original=line.strip().lower()
    parts=original.split('.')
    d='.'.join(parts[-2:]) if len(parts)>=3 else original
    name=d.rsplit('.',1)[0]

    # 1. Whitelist: allow if contains or startswith whitelist patterns
    if any(w in d for w in whitelist_contains) or any(d.startswith(w) for w in whitelist_startswith):
        res.add(d)
        continue
    # 2. Check allowed TLDs
    if not d.endswith(allowed_tlds):
        continue
    # 3. Blacklist: reject if contains or startswith blacklist patterns
    if any(b in d for b in blacklist_contains) or any(d.startswith(b) for b in blacklist_startswith):
        continue
    # 4. Filters:
    # 4.1 Reject if 3+ chars then hyphen and letter (e.g. abc-def)
    if re.match(r'^.{3,}-[a-z]', d):
        continue
    # 4.2 Reject if starts with digit
    if d[0].isdigit():
        continue
    # 4.3 Reject if starts with 1-2 letters followed by non-letter
    if re.match(r'^[a-zA-Z]{1,2}[^a-zA-Z]', d):
        continue
    # 4.4 Reject if name ends with digit
    if name[-1].isdigit():
        continue
    # 4.5 Reject if hyphen followed by digits (e.g. -123)
    if re.search(r'-\d+', d):
        continue
    # 4.6 Reject if 3+ digits in a row anywhere
    if re.search(r'\d{3,}', d):
        continue
    # 4.7 Reject if first two chars of name are identical
    if len(name)>=2 and name[0]==name[1]:
        continue
    # 4.8 Reject if more than one hyphen
    if d.count('-')>1:
        continue
    # 4.9 Reject if length > 20 chars
    if len(d)>20:
        continue

    res.add(d)

with open("reestr_filtered.txt","w",encoding="utf-8") as f:
    f.write('\n'.join(sorted(res)))