import os
import requests
from bs4 import BeautifulSoup

# 1. State Management: Load seen jobs from a file
DB_FILE = "seen_jobs.txt"

def load_seen_jobs():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return set(line.strip() for line in f)
    return set()

def save_seen_job(job_id):
    with open(DB_FILE, "a") as f:
        f.write(f"{job_id}\n")

def send_slack_notification(title, company, link):
    webhook_url = os.getenv("SLACK_WEBHOOK") # Securely pulled from GitHub Secrets
    if not webhook_url:
        print("⚠️ Skipping Slack: SLACK_WEBHOOK environment variable not set.")
        return

    payload = {
        "text": f"🚀 *New Salesforce Job!*\n*Role:* {title}\n*Company:* {company}\n*Link:* {link}"
    }
    try:
        requests.post(webhook_url, json=payload)
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
                
                # Extract unique ID from the end of the URL
                job_id = job_url.split('-')[-1] 

                if job_id not in seen_ids:
                    found_new = True
                    # Consolidated Console Output
                    print(f"✨ NEW JOB DETECTED ✨")
                    print(f"📌 Role: {title}")
                    print(f"🏢 Company: {company}")
                    print(f"🔗 URL: {job_url}")
                    print("-" * 30)
                    
                    send_slack_notification(title, company, job_url)
                    save_seen_job(job_id)
        
        if not found_new:
            print("No new jobs found since last check.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_salesforce_jobs()