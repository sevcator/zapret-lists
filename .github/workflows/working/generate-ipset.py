import ipaddress
import socket
from typing import Dict, Iterable, List, Set, Tuple
from urllib.parse import urlparse

import requests

SUITE_URL = "https://raw.githubusercontent.com/hyperion-cs/dpi-checkers/refs/heads/main/ru/tcp-16-20/suite.json"
OUTPUT_FILE = "ipset.txt"

REQUEST_TIMEOUT = 15


def fetch_json(url: str):
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def extract_hosts(items: Iterable[dict]) -> List[str]:
    hosts: Set[str] = set()

    for item in items:
        raw_url = item.get("url")
        if not raw_url:
            continue

        try:
            parsed = urlparse(raw_url)
            host = parsed.hostname
            if host:
                hosts.add(host.lower())
        except Exception:
            continue

    return sorted(hosts)


def resolve_host(host: str) -> Set[str]:
    ips: Set[str] = set()

    try:
        # If host is already an IP address
        ipaddress.ip_address(host)
        ips.add(host)
        return ips
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        for info in infos:
            sockaddr = info[4]
            ip = sockaddr[0]
            ips.add(ip)
    except socket.gaierror:
        pass

    return ips


def normalize_asn(asn_value) -> str:
    asn_str = str(asn_value).strip()
    if not asn_str:
        return ""
    if asn_str.upper().startswith("AS"):
        return asn_str.upper()
    return f"AS{asn_str}"


def get_asns_by_ip(ip: str) -> Set[str]:
    """
    Resolve ASN for an IP using RIPE Stat.
    The API may return either a single ASN or a list of ASNs.
    """
    url = f"https://stat.ripe.net/data/network-info/data.json?resource={ip}"
    result: Set[str] = set()

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json().get("data", {})
    except requests.RequestException:
        return result
    except ValueError:
        return result

    # Most common response format
    asns = data.get("asns")
    if isinstance(asns, list):
        for item in asns:
            if isinstance(item, dict):
                maybe_asn = item.get("asn")
                if maybe_asn is not None:
                    normalized = normalize_asn(maybe_asn)
                    if normalized:
                        result.add(normalized)
            else:
                normalized = normalize_asn(item)
                if normalized:
                    result.add(normalized)

    # Fallback for alternate response format
    if not result:
        maybe_asn = data.get("asn")
        if maybe_asn is not None:
            normalized = normalize_asn(maybe_asn)
            if normalized:
                result.add(normalized)

    return result


def get_prefixes_by_asn(asn: str) -> Tuple[List[str], List[str]]:
    """
    Return (ipv4_prefixes, ipv6_prefixes) for an ASN.
    """
    url = f"https://stat.ripe.net/data/announced-prefixes/data.json?resource={asn}"

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return [], []
    except ValueError:
        return [], []

    prefixes = data.get("data", {}).get("prefixes", [])

    ipv4 = []
    ipv6 = []

    for item in prefixes:
        prefix = item.get("prefix")
        if not prefix:
            continue
        if ":" in prefix:
            ipv6.append(prefix)
        else:
            ipv4.append(prefix)

    ipv4 = sorted(set(ipv4), key=lambda x: (ipaddress.ip_network(x, strict=False).network_address,
                                            ipaddress.ip_network(x, strict=False).prefixlen))
    ipv6 = sorted(set(ipv6), key=lambda x: (ipaddress.ip_network(x, strict=False).network_address,
                                            ipaddress.ip_network(x, strict=False).prefixlen))

    return ipv4, ipv6


def save_ipset(asn_to_prefixes: Dict[str, Tuple[List[str], List[str]]], output_file: str) -> None:
    all_ipv4: List[str] = []
    all_ipv6: List[str] = []

    for ipv4, ipv6 in asn_to_prefixes.values():
        all_ipv4.extend(ipv4)
        all_ipv6.extend(ipv6)

    all_ipv4 = sorted(
        set(all_ipv4),
        key=lambda x: (
            ipaddress.ip_network(x, strict=False).network_address,
            ipaddress.ip_network(x, strict=False).prefixlen,
        ),
    )
    all_ipv6 = sorted(
        set(all_ipv6),
        key=lambda x: (
            ipaddress.ip_network(x, strict=False).network_address,
            ipaddress.ip_network(x, strict=False).prefixlen,
        ),
    )

    with open(output_file, "w", encoding="utf-8") as f:
        for prefix in all_ipv4:
            f.write(prefix + "\n")

        for prefix in all_ipv6:
            f.write(prefix + "\n")


def main():
    print(f"[1/5] Downloading suite: {SUITE_URL}")
    suite = fetch_json(SUITE_URL)

    print("[2/5] Extracting domains")
    hosts = extract_hosts(suite)
    print(f"Domains found: {len(hosts)}")

    print("[3/5] Resolving IPs")
    all_ips: Set[str] = set()
    host_to_ips: Dict[str, Set[str]] = {}

    for host in hosts:
        ips = resolve_host(host)
        host_to_ips[host] = ips
        all_ips.update(ips)

    print(f"Unique IPs found: {len(all_ips)}")

    print("[4/5] Resolving ASN by IP")
    all_asns: Set[str] = set()
    ip_to_asns: Dict[str, Set[str]] = {}

    for ip in sorted(all_ips, key=lambda x: (":" in x, x)):
        asns = get_asns_by_ip(ip)
        ip_to_asns[ip] = asns
        all_asns.update(asns)

    print(f"Unique ASNs found: {len(all_asns)}")
    for asn in sorted(all_asns):
        print(asn)

    print("[5/5] Fetching ASN prefixes and writing ipset.txt")
    asn_to_prefixes: Dict[str, Tuple[List[str], List[str]]] = {}

    for asn in sorted(all_asns):
        ipv4, ipv6 = get_prefixes_by_asn(asn)
        asn_to_prefixes[asn] = (ipv4, ipv6)

    save_ipset(asn_to_prefixes, OUTPUT_FILE)
    print(f"Done. Result written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()