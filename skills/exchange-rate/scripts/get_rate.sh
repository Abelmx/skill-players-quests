#!/usr/bin/env bash
# Query exchange rate using frankfurter.app API

FROM="${1:-}"
TO="${2:-}"
if [[ -z "$FROM" || -z "$TO" ]]; then
  echo "Usage: $0 FROM TO"
  echo "Example: $0 USD EUR"
  exit 1
fi

curl -s "https://api.frankfurter.app/latest?from=${FROM}&to=${TO}" | python3 -c "
import json, sys
d = json.load(sys.stdin)
to_code = '${TO}'
from_code = '${FROM}'
if 'rates' in d and to_code in d['rates']:
    print(f\"1 {from_code} = {d['rates'][to_code]} {to_code}\")
else:
    print('Error:', d.get('message', 'Unknown error'), file=sys.stderr)
    sys.exit(1)
"
