---
name: weather
description: Query real-time weather and forecast data. Use when the user asks about weather, temperature, humidity, or forecasts for any location. No API key needed.
---

# Weather Query

## Instructions

When the user asks about weather, temperature, humidity, or forecasts for a location, use one of these methods:

### Method (a) Quick curl wttr.in

```bash
curl "wttr.in/CITY?format=%l:+%t+%C+%h+%w"
```

### Method (b) Open-Meteo JSON API (no API key)

```bash
# Get coordinates first, then:
curl "https://api.open-meteo.com/v1/forecast?latitude=LAT&longitude=LON&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
```

### Method (c) Run the script

```bash
./scripts/get_weather.sh "CITY_NAME"
```

The script uses curl to query wttr.in and prints temperature, condition, humidity, and wind.

## Usage Examples

```bash
# Using the script
./scripts/get_weather.sh "Beijing"
./scripts/get_weather.sh "New York"

# Direct curl
curl "wttr.in/London?format=%l:+%t+%C+%h+%w"
```

## Notes

- No API key required for wttr.in or Open-Meteo.
- City names support most major cities worldwide.
