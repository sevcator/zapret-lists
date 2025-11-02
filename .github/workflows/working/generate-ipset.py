import requests

ASNS = ["AS8075", "AS8560", "AS12322", "AS12876", "AS13335", "AS14061", "AS14618", "AS16276", "AS16509", "AS20473", "AS20940", "AS24940", "AS31898", "AS36352", "AS48031", "AS54113", "AS60068", "AS60781", "AS62563", "AS199524"]

OUTPUT_FILE_V4 = "ipset-v4.txt"
OUTPUT_FILE_V6 = "ipset-v6.txt"

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

def save_to_files(results, v4_filename, v6_filename):
    with open(v4_filename, 'w') as v4_file, open(v6_filename, 'w') as v6_file:
        items = list(results.items())
        for i, (asn, (ipv4, ipv6)) in enumerate(items):
            if ipv4:
                v4_file.write(f"# {asn}\n")
                for prefix in ipv4:
                    v4_file.write(f"{prefix}\n")
                if i < len(items) - 1:
                    v4_file.write("\n")
            if ipv6:
                v6_file.write(f"# {asn}\n")
                for prefix in ipv6:
                    v6_file.write(f"{prefix}\n")
                if i < len(items) - 1:
                    v6_file.write("\n")

def main():
    results = {}
    for asn in ASNS:
        ipv4, ipv6 = get_cidrs_by_asn(asn)
        results[asn] = (ipv4, ipv6)
    save_to_files(results, OUTPUT_FILE_V4, OUTPUT_FILE_V6)

if __name__ == "__main__":
    main()
