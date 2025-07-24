import requests
import json
import csv
from datetime import datetime, timedelta

# --- CONFIG ---
API_KEY = "xxx"
ENDPOINT = "https://api.perplexity.ai/chat/completions"
OUTPUT_FILE = "results_looping.csv"

companies = ["Wilmar", "Astra Agro Lestari", "Dinant", "Ocho Sur"]
issues = ["deforestation", "conflict", "indigenous", "corruption"]

def is_url_valid(url):
    try:
        resp = requests.head(url, timeout=5)
        return resp.status_code < 400
    except:
        return False

# --- Prepare CSV ---
with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Company", "Issue", "Title", "Summary", "Keywords", "Date Published", "Source URL"])

# --- Fetch News Function ---
def fetch_news(company, issue, days_back=30):
    """Fetch filtered news from Perplexity AI"""
    date_filter = (datetime.now() - timedelta(days=days_back)).strftime("%m/%d/%Y")

    user_prompt = (
        f"Has the company {company} had any news or article related to {issue}? "
        f"Find up recent investigative or news articles"
        f"Return results as JSON with fields: title, summary, keywords, companies, "
        f"date_published (MM-DD-YYYY), source_url. "
        f"Return only {{\"items\": [...]}}."
        
    )

    payload = {
        "model": "sonar-pro",
        "stream": False,
        "max_tokens": 1024,
        "temperature": 0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "summary": {"type": "string"},
                                    "keywords": {"type": "string"},
                                    "companies": {"type": "string"},
                                    "date_published": {"type": "string"},
                                    "source_url": {"type": "string"}
                                }
                            }
                        }
                    },
                    "required": ["items"]
                }
            }
        },
        "messages": [
            {"role": "system", "content": "You are a JSON-only news monitor. Return strict JSON only."},
            {"role": "user", "content": user_prompt}
        ],
        "search_after_date_filter": date_filter
    }

    response = requests.post(
        ENDPOINT,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json=payload
    )

    if response.status_code != 200:
        print(f"Error {response.status_code} for {company} - {issue}: {response.text}")
        return []

    try:
        data = response.json()
        content = data.get("choices", [])[0]["message"]["content"]
        parsed = json.loads(content)

        # Filter out invalid URLs and old dates
        items = []
        for item in parsed.get("items", []):
            url = item.get("source_url", "")
            date = item.get("date_published", "")
            # Skip broken links
            if not url or not is_url_valid(url):
                continue
            # Skip old news if date is not valid
            try:
                published = datetime.strptime(date, "%m-%d-%Y")
                if published < datetime.now() - timedelta(days=days_back):
                    continue
            except:
                continue
            items.append(item)
        return items
    except Exception as e:
        print(f"Error parsing response for {company} {issue}: {e}")
        return []

# --- Main Loop ---
all_results = []
for company in companies:
    for issue in issues:
        print(f"\nFetching news for {company} {issue}...")
        results = fetch_news(company, issue, days_back=30)
        # Save results
        with open(OUTPUT_FILE, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            for r in results:
                writer.writerow([
                    company,
                    issue,
                    r.get("title", ""),
                    r.get("summary", ""),
                    r.get("keywords", ""),
                    r.get("date_published", ""),
                    r.get("source_url", "")
                ])
        all_results.extend(results)

print(f"\nDONE. Total valid results saved: {len(all_results)}")
print(f"Open '{OUTPUT_FILE}' to view results.")
