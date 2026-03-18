#!/usr/bin/env bash
# Query weather for a city using wttr.in

CITY="${1:-}"
if [[ -z "$CITY" ]]; then
  echo "Usage: $0 <city_name>"
  exit 1
fi

# Format: Location, Temperature, Condition, Humidity, Wind
curl -s "wttr.in/${CITY}?format=%l:+%t+%C+%h+%w"
