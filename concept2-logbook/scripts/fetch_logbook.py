#!/usr/bin/env python3
"""
Concept2 Logbook fetcher script.
Fetches workout data using API token.
"""

import requests
import json
import sys
import argparse
from datetime import datetime

def fetch_results(token, base_url="https://log.concept2.com", page=1, per_page=50, from_date=None, to_date=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.c2logbook.v1+json"
    }
    params = {
        "page": page,
        "number": per_page
    }
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    
    url = f"{base_url}/api/users/me/results"
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def main():
    parser = argparse.ArgumentParser(description="Fetch Concept2 Logbook workouts")
    parser.add_argument("--token", required=True, help="API access token")
    parser.add_argument("--from-date", help="Start date YYYY-MM-DD")
    parser.add_argument("--to-date", help="End date YYYY-MM-DD")
    parser.add_argument("--output", default="logbook.json", help="Output file")
    args = parser.parse_args()
    
    data = fetch_results(args.token, from_date=args.from_date, to_date=args.to_date)
    with open(args.output, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved to {args.output}")
    print(f"Total results: {data.get('meta', {}).get('pagination', {}).get('total', 0)}")

if __name__ == "__main__":
    main()