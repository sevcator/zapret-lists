def get_base_domain(domain):
    parts = domain.strip().split(".")
    if len(parts) < 2:
        return domain
    return ".".join(parts[-2:])

def filter_subdomains_inplace(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        domains = set(line.strip() for line in f if line.strip())

    base_domains = set(get_base_domain(d) for d in domains)

    with open(file_path, "w", encoding="utf-8") as f:
        for domain in sorted(base_domains):
            f.write(domain + "\n")

if __name__ == "__main__":
    filter_subdomains_inplace("module/list/reestr.txt")
