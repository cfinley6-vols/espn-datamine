# Reverse-Engineering ESPN's Hidden College Football APIs for Play-by-Play Data Pipelines

## Objective & Approach
This project aims to discover, reverse-engineer, and map undocumented ESPN REST API endpoints for college football to recover play-by-play, drive, and roster data. 

We will inspect network traffic from ESPN's web and mobile clients to identify hidden endpoints and query parameters, then build a Python pipeline to ingest, clean, and structure the nested JSON responses into a relational dataset. The final deliverable will be an open documentation schema and a functional data retrieval package for college football game-level analytics.

## Expected Data Source
- **Endpoint:** Data will be acquired from ESPN's internal, undocumented public endpoints:  
  `https://site.api.espn.com/apis/site/v2/sports/football/college-football/`
- **Method:** Data will be retrieved programmatically using Python.

## Team Members
- Siddh Patel (spate198)
- Davyn Mengeling (dmengeli)
- Connor Finley (cfinley6)
- Cade Damron (cdamron3)
