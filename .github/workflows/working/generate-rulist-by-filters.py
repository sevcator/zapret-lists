import re
import requests

SOURCE_URLS = [
    "https://raw.githubusercontent.com/bol-van/rulist/refs/heads/main/reestr_hostname_resolvable.txt",
    "https://antifilter.download/list/domains.lst",
    "https://community.antifilter.download/list/domains.lst",
    "https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/refs/heads/release/gfw.txt",
    "https://raw.githubusercontent.com/Loyalsoldier/v2ray-rules-dat/refs/heads/release/greatfire.txt",
]

def fetch_lines(urls):
    """Download all source lists and return a combined list of lines."""
    combined = []
    for url in urls:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        combined.extend(resp.text.splitlines())
    return combined

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

allowed_tlds = ('.com', '.org', '.net')

def normalize_domain(line):
    """Trim noise from a raw line to isolate a domain candidate."""
    domain = line.strip().lower()
    if not domain or domain.startswith(("#", "!")):
        return None
    if domain.startswith("||"):
        domain = domain[2:]
    domain = domain.lstrip(".")
    for sep in ("^", "/"):
        domain = domain.split(sep, 1)[0]
    domain = domain.split(":", 1)[0].lstrip("*").strip()
    if not domain or not re.match(r"^[a-z0-9.-]+$", domain):
        return None
    return domain

raw_domains = set()

for line in fetch_lines(SOURCE_URLS):
    domain = normalize_domain(line)
    if not domain:
        continue
    parts = domain.split(".")
    if len(parts) < 2:
        continue
    apex = ".".join(parts[-2:])
    if not apex.endswith(allowed_tlds):
        continue
    raw_domains.add(apex)

res = set()

for d in raw_domains:
    name = d.rsplit('.',1)[0]

    # 1. Whitelist: allow if contains or startswith whitelist patterns
    if any(w in d for w in whitelist_contains) or any(d.startswith(w) for w in whitelist_startswith):
        res.add(d)
        continue
    # 2. Blacklist: reject if contains or startswith blacklist patterns
    if any(b in d for b in blacklist_contains) or any(d.startswith(b) for b in blacklist_startswith):
        continue
    # 3. Filters:
    # 3.1 Reject if 3+ chars then hyphen and letter (e.g. abc-def)
    if re.match(r'^.{3,}-[a-z]', d):
        continue
    # 3.2 Reject if starts with digit
    if d[0].isdigit():
        continue
    # 3.3 Reject if starts with 1-2 letters followed by non-letter
    if re.match(r'^[a-zA-Z]{1,2}[^a-zA-Z]', d):
        continue
    # 3.4 Reject if name ends with digit
    if name[-1].isdigit():
        continue
    # 3.5 Reject if hyphen followed by digits (e.g. -123)
    if re.search(r'-\d+', d):
        continue
    # 3.6 Reject if 3+ digits in a row anywhere
    if re.search(r'\d{3,}', d):
        continue
    # 3.7 Reject if first two chars of name are identical
    if len(name)>=2 and name[0]==name[1]:
        continue
    # 3.8 Reject if more than one hyphen
    if d.count('-')>1:
        continue
    # 3.9 Reject if length > 20 chars
    if len(d)>20:
        continue

    res.add(d)

with open("reestr_filtered.txt","w",encoding="utf-8") as f:
    f.write('\n'.join(sorted(res)))
