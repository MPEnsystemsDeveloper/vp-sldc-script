# scraper.py
import cloudscraper # <-- CHANGE: Import cloudscraper
from bs4 import BeautifulSoup
import os
import json
import time
import re
from datetime import datetime, date

# ... (STATES and other constants remain the same) ...
STATES = [
    "Andhra Pradesh", "Assam", "Bihar", "Chhattisgarh", "Delhi", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jammu & Kashmir", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Puducherry", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal"
]
BASE_URL_TEMPLATE = "https://vidyutpravah.in/state-data/{state}"
OUTPUT_DIR = "data"
LATEST_FILE = "latest.json"

def format_state_for_url(state_name):
    return state_name.lower().replace(" ", "-").replace("&", "and").strip()

def scrape_state_data(scraper, url, state_name): # <-- CHANGE: Pass scraper object
    print(f"Fetching data for {state_name} from {url}...")
    try:
        # --- CHANGE: Use the scraper object to make the request ---
        response = scraper.get(url, timeout=30) 
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # ... (Rest of the scraping logic remains the same) ...
        time_block_tag = soup.find('b')
        time_block = time_block_tag.get_text(strip=True) if time_block_tag else None
        demand_container = soup.find(lambda tag: "State's Demand Met" in tag.get_text())
        demand_met_yesterday = None
        demand_met_current = None
        if demand_container:
            yesterday_tag = demand_container.find(string=re.compile(r'YESTERDAY'))
            if yesterday_tag and hasattr(yesterday_tag, 'find_next'):
                yesterday_value_tag = yesterday_tag.find_next('span')
                if yesterday_value_tag:
                    demand_met_yesterday = yesterday_value_tag.get_text(strip=True)
            current_tag = demand_container.find(string=re.compile(r'CURRENT'))
            if current_tag and hasattr(current_tag, 'find_next'):
                current_value_tag = current_tag.find_next('span')
                if current_value_tag:
                    demand_met_current = current_value_tag.get_text(strip=True)

        if time_block and demand_met_yesterday and demand_met_current:
            print(f"  - Extracted: Time='{time_block}', Yesterday='{demand_met_yesterday}', Current='{demand_met_current}'")
            return {"time_block": time_block, "demand_met_yesterday": demand_met_yesterday, "demand_met_current": demand_met_current}
        else:
            print(f"  - Missing fields for {state_name}")
            return None
    except Exception as e:
        print(f"  - An error occurred for {state_name}: {e}")
        return None

def main_scraper():
    newly_scraped_data = []
    today_str = date.today().strftime("%d-%m-%Y")
    
    # --- CHANGE: Create a single scraper instance for all requests ---
    scraper = cloudscraper.create_scraper()

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()

    out_dir_path = os.path.join(script_dir, OUTPUT_DIR)
    os.makedirs(out_dir_path, exist_ok=True)

    for state in STATES:
        formatted_state = format_state_for_url(state)
        full_url = BASE_URL_TEMPLATE.format(state=formatted_state)
        # --- CHANGE: Pass the scraper to the function ---
        scraped_info = scrape_state_data(scraper, full_url, state)
        if scraped_info:
            state_json_obj = { "urlScraped": full_url, "key": formatted_state, "key_name": "vidyutpravah", "time_block": scraped_info['time_block'], "date": today_str, "isManual": 1, f"parsed_{formatted_state}": { "State's Demand Met": { "YESTERDAY ": scraped_info['demand_met_yesterday'], "CURRENT ": scraped_info['demand_met_current']}}}
            newly_scraped_data.append(state_json_obj)
        time.sleep(2)

    if newly_scraped_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_name = f"all_state_power_data_{timestamp}.json"
        timestamped_path = os.path.join(out_dir_path, timestamped_name)
        print(f"Saving {len(newly_scraped_data)} entries to {timestamped_path} ...")
        with open(timestamped_path, 'w', encoding='utf-8') as f:
            json.dump(newly_scraped_data, f, indent=4)
        latest_path = os.path.join(out_dir_path, LATEST_FILE)
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(newly_scraped_data, f, indent=4)
        print("Data saved.")
    else:
        print("No data scraped this run.")

if __name__ == "__main__":
    main_scraper()