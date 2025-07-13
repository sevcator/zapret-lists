import requests

ASNS = ["AS12322", "AS12876", "AS13335", "AS14061", "AS14618", "AS16276", "AS16509", "AS199524", "AS20473", "AS20940", "AS24940", "AS31898", "AS36352", "AS48031", "AS54113", "AS60068", "AS60781", "AS62563", "AS8075", "AS8560"]
OUTPUT_FILE = "ipset.txt"

def get_cidrs_by_asn(asn):
    url = f"https://stat.ripe.net/data/announced-prefixes/data.json?resource={asn}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return [], []

    data = response.json()
    prefixes = data.get("data", {}).get("prefixes", [])

    ipv4 = sorted(p['prefix'] for p in prefixes if ':' not in p['prefix'])
    ipv6 = sorted(p['prefix'] for p in prefixes if ':' in p['prefix'])

    return ipv4, ipv6

def save_to_file(results, filename):
    with open(filename, 'w') as f:
        items = list(results.items())
        for i, (asn, (ipv4, ipv6)) in enumerate(items):
            f.write(f"# {asn}\n")
            f.write(f"# IPv4\n")
            for prefix in ipv4:
                f.write(f"{prefix}\n")
            f.write(f"# IPv6\n")
            for j, prefix in enumerate(ipv6):
                f.write(f"{prefix}\n" if j < len(ipv6) - 1 else f"{prefix}")
            if i < len(items) - 1:
                f.write("\n\n")

def main():
    results = {}
    for asn in ASNS:
        ipv4, ipv6 = get_cidrs_by_asn(asn)
        results[asn] = (ipv4, ipv6)
    save_to_file(results, OUTPUT_FILE)

if __name__ == "__main__":
    main()
