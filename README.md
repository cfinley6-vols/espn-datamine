# Reverse-Engineering ESPN's Hidden College Football APIs for Play-by-Play Data Pipelines

## Objective & Approach
This project performs a digital archaeology and schema discovery analysis of ESPN’s College Football REST API, specifically focusing on the game summary endpoint to map every statistical and metadata artifact tracked by the platform.

Instead of merely extracting high-level box scores, we execute recursive JSON structural traversals to decode nested data hierarchies across team statistics, individual athlete metrics, drive sequences, and play-by-play events. We then parse these deeply nested arrays—including stat keys, categories, and labels—to generate a comprehensive data dictionary and structural map. The final deliverable is an open documentation schema and an automated Python toolset that catalog and flatten ESPN's JSON payloads into relational data structures for game-level analytics.

## Expected Data Source
- **Endpoint:** Data will be acquired from ESPN's internal, undocumented public endpoints:  
  `https://site.api.espn.com/apis/site/v2/sports/football/college-football/`
- **Method:** Data will be retrieved programmatically using Python.

## Team Members
- Siddh Patel (spate198)
- Davyn Mengeling (dmengeli)
- Connor Finley (cfinley6)
- Cade Damron (cdamron3)
