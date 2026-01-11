import os
import requests
from bs4 import BeautifulSoup

# 1. State Management
DB_FILE = "seen_jobs.txt"

def load_seen_jobs():
    """Loads only the Job IDs to check for duplicates."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            # We split by '|' and take the first element (the ID)
            return set(line.split('|')[0].strip() for line in f if '|' in line)
    return set()

def save_seen_job(job_id, title, job_url):
    """Saves ID, Title, and URL to the file."""
    with open(DB_FILE, "a") as f:
        # Saving as: ID | Title | URL
        f.write(f"{job_id} | {title} | {job_url}\n")

def send_slack_notification(title, company, link):
    webhook_url = os.getenv("SLACK_WEBHOOK")
    if not webhook_url:
        print("⚠️ Skipping Slack: SLACK_WEBHOOK environment variable not set.")
        return

    payload = {
        "text": f"🚀 *New Salesforce Job!*\n*Role:* {title}\n*Company:* {company}\n*Link:* {link}"
    }
    try:
        r = requests.post(webhook_url, json=payload)
        print(f"Slack Response: {r.status_code}") # Helpful for debugging
    except Exception as e:
        print(f"Failed to send Slack alert: {e}")

def fetch_salesforce_jobs():
    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Salesforce%20Developer&geoId=90009650&f_TPR=r20000&sortBy=DD"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch jobs. Status Code: {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        job_cards = soup.find_all('li')
        seen_ids = load_seen_jobs()
        
        found_new = False

        for card in job_cards:
            title_tag = card.find('h3', class_='base-search-card__title')
            company_tag = card.find('h4', class_='base-search-card__subtitle')
            link_tag = card.find('a', class_='base-card__full-link')

            if title_tag and company_tag and link_tag:
                title = title_tag.text.strip()
                company = company_tag.text.strip()
                job_url = link_tag['href'].split('?')[0]
                job_id = job_url.split('-')[-1] 

                if job_id not in seen_ids:
                    found_new = True
                    print(f"✨ NEW JOB DETECTED: {title}")
                    
                    send_slack_notification(title, company, job_url)
                    # Updated to pass all three pieces of info
                    save_seen_job(job_id, title, job_url)
        
        if not found_new:
            print("No new jobs found since last check.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_salesforce_jobs()