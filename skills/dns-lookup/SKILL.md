---
name: dns-lookup
description: Query DNS records and WHOIS information for domains. Use when the user asks about DNS records, domain registration, nameservers, MX records, or IP addresses of domains.
---

# DNS Lookup

Query DNS records and WHOIS information for domains.

## Tools

### dig (primary)

```bash
dig A example.com
dig MX example.com
dig NS example.com
```

### nslookup (fallback)

```bash
nslookup example.com
```

### whois

```bash
whois example.com
```

For registration, nameservers, and domain metadata.

## Script

```bash
./scripts/lookup.sh example.com
./scripts/lookup.sh example.com A
./scripts/lookup.sh example.com ALL
```

- `$1`: domain
- `$2`: record type (default: A). Use `ALL` for A + MX records.
