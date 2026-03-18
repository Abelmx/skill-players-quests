#!/usr/bin/env bash
# Query DNS records for a domain.
# Usage: lookup.sh <domain> [record_type]
# record_type: A, MX, NS, etc. Default: A. Use ALL for A + MX.

domain="${1:?Usage: $0 <domain> [record_type]}"
type="${2:-A}"

echo "=== DNS lookup for $domain (type: $type) ==="

if [[ "$type" == "ALL" ]]; then
  echo
  echo "--- A records ---"
  dig +short A "$domain"
  echo
  echo "--- MX records ---"
  dig +short MX "$domain"
else
  dig +short "$type" "$domain"
fi
