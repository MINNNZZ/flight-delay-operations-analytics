# Source data setup

Raw files were supplied locally; their original download provenance and redistribution terms were not independently verified. They are not bundled in this repository.

Place lawful copies of these three files at the repository root (not inside scripts/). The original flight dataset has 31 columns, 5,819,079 rows, and coverage of 2015. A different source must be profiled anew; historical results are not validation of a replacement.

| File | Original SHA-256 |
| --- | --- |
| flights.csv | `afa4e42188b113dd69427a3fbd00a4b6979c6235c866f963c2899d18a3403a83` |
| airports.csv | `23c4cea98c318225bd923b2068ead8af089845071f79fd9ea0037ba6a61cd4e2` |
| airlines.csv | `ec54f453260c2a46fc76d497ab0eb0a4c13724b566fba8a7ce3bb8ad712acca3` |

## Expected flight columns

```text
YEAR,MONTH,DAY,DAY_OF_WEEK,AIRLINE,FLIGHT_NUMBER,TAIL_NUMBER,ORIGIN_AIRPORT,DESTINATION_AIRPORT,SCHEDULED_DEPARTURE,DEPARTURE_TIME,DEPARTURE_DELAY,TAXI_OUT,WHEELS_OFF,SCHEDULED_TIME,ELAPSED_TIME,AIR_TIME,DISTANCE,WHEELS_ON,TAXI_IN,SCHEDULED_ARRIVAL,ARRIVAL_TIME,ARRIVAL_DELAY,DIVERTED,CANCELLED,CANCELLATION_REASON,AIR_SYSTEM_DELAY,SECURITY_DELAY,AIRLINE_DELAY,LATE_AIRCRAFT_DELAY,WEATHER_DELAY
```

## Running and refreshing

Run the sequence in README after providing the files. scripts/profile_data.py creates a new profile identity and source hashes; scripts/analyze_flights.py applies readiness checks and writes the large cleaned export. Original source records are preserved. The full readback verifies every source column.

Large files are ignored by Git. Do not commit raw files or the generated gzip export. The supplied hashes identify the original bytes; an equivalent CSV can have a different hash due to encoding/serialization and still requires a fresh validation run.

PBIX release assets contain an embedded model and can be viewed without refreshing. To refresh PBIX/PBIP, supply/rebuild the processed files, then update the local file locations in Power Query/model partitions. PBIP definitions are source artifacts, not substitutes for an imported model cache.
