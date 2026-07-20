---
name: concept2-logbook
description: Use this skill for reading or analyzing Concept2 Logbook data — rowing, skiing, biking workouts via the official API. Triggers include Concept2, logbook, erg data, workout history, rowing stats, fetch results.
---

# Concept2 Logbook Skill

## Overview

This skill enables fetching, summarizing, and analyzing workout data from the Concept2 Logbook API (https://log.concept2.com/developers/documentation/). Ideal for fitness tracking, progress reports, and training insights.

## Setup

1. User must obtain a personal access token:
   - Log into https://log.concept2.com
   - Go to Profile > Applications > "Concept2 Logbook API integration"
   - Generate a long-lived token (easiest for personal use; scopes: results:read, user:read)

2. Store token securely (never commit to code).

## Scripts

- `scripts/fetch_logbook.py`: Basic fetcher for paginated results. Supports date filters.
  - Usage: `python3 scripts/fetch_logbook.py --token YOUR_TOKEN --from-date 2026-01-01 --output workouts.json`

Extend with more scripts for summaries, charts (e.g., via matplotlib if available), or stroke data.

## Key Endpoints (read-only)

- GET `/api/users/me` : User profile
- GET `/api/users/me/results` : List workouts (paginate with ?page= &number= ; filters: from, to, type=rower)
- GET `/api/users/me/results/{id}` : Single workout details
- GET `/api/users/me/results/{id}/strokes` : Detailed stroke data (if available)

Always use `Accept: application/vnd.c2logbook.v1+json` header.

## Usage Instructions

When user asks to read/analyze logbook:

1. Confirm they have token (guide if needed).
2. Use `bash` tool or run script to fetch data into artifacts/.
3. Parse JSON, compute stats (total meters, avg pace, PRs, trends).
4. For summaries: aggregate distance/time by week/month, identify improvements.
5. Visualize if possible (tables, or suggest plots).

Handle pagination by following "meta.pagination.links.next".

Respect rate limits (none currently, but be polite).

For full API details, reference the official docs or create `references/api-reference.md`.