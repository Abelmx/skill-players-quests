---
name: exchange-rate
description: Query real-time currency exchange rates. Use when the user asks about foreign exchange rates, currency conversion, or currency prices. No API key needed.
---

# Exchange Rate Query

## Instructions

When the user asks about foreign exchange rates, currency conversion, or currency prices:

### frankfurter.app API (recommended, no API key)

```bash
curl "https://api.frankfurter.app/latest?from=USD&to=EUR"
```

### exchangerate-api.com (free tier)

```bash
curl "https://api.exchangerate-api.com/v4/latest/USD"
```

### Run the script

```bash
./scripts/get_rate.sh FROM TO
```

Example: `./scripts/get_rate.sh USD EUR` — prints the current USD to EUR rate.

## Usage Examples

```bash
# USD to EUR
./scripts/get_rate.sh USD EUR

# GBP to JPY
./scripts/get_rate.sh GBP JPY

# Direct curl
curl "https://api.frankfurter.app/latest?from=USD&to=CNY"
```

## Notes

- No API key required for frankfurter.app.
- Use standard 3-letter currency codes (USD, EUR, GBP, JPY, CNY, etc.).
