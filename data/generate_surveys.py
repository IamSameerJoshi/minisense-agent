import json
import random
from datetime import date, timedelta
from pathlib import Path

# Fix random seed for reproducibility
random.seed(42)

TOTAL_RECORDS = 60000  # Stays comfortably inside the 50k-100k requirement
OUTPUT_PATH = Path(__file__).resolve().parent / "survey_data.json"

CHANNELS = ["mobile", "web", "in-store kiosk", "email"]
BUSINESS_ID = "b_greenleaf_01"
BUSINESS_NAME = "GreenLeaf Bistro"
SURVEY_ID = "s_dining_exp"
SURVEY_NAME = "Guest Dining Experience"

# Seed texts correlated with ratings to produce realistic themes
POSITIVE_TEXTS = [
    "The Avocado Toast was fresh and delicious!",
    "House Cold Brew was incredible, friendly cashier.",
    "Quick service, clean dining area, and great Mediterranean bowl.",
    "Loved the morning vibe. Food came out in under 8 minutes.",
    "GreenLeaf Perks mobile ordering made pickup super seamless.",
]

NEUTRAL_TEXTS = [
    "Food was okay, but counter staff seemed distracted.",
    "Standard bistro experience. Prices are slightly high for portion size.",
    "Decent coffee, but the tables needed bussing.",
    "Avocado toast was good, wait was roughly 15 minutes.",
]

NEGATIVE_TEXTS = [
    "Waited over 25 minutes for a salad during lunch rush. Unacceptable.",
    "Cold brew was watery and the order was missing avocado add-on.",
    "Excessive wait times today. Staff did not apologize or escalate.",
    "Food was cold when served. Manager took forever to issue a refund.",
    "Poor cleanliness during the weekend peak hours.",
]

def generate_dataset():
    records = []
    
    # Date boundaries: April 1, 2026 to May 31, 2026 (61 days)
    start_date = date(2026, 4, 1)
    
    for i in range(1, TOTAL_RECORDS + 1):
        day_offset = random.randint(0, 60)
        record_date = start_date + timedelta(days=day_offset)
        
        # April (month 4): higher satisfaction
        # May (month 5): operational slump (more 1s, 2s, and 3s)
        if record_date.month == 4:
            rating = random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.05, 0.10, 0.35, 0.45])[0]
        else:
            rating = random.choices([1, 2, 3, 4, 5], weights=[0.15, 0.15, 0.20, 0.28, 0.22])[0]
            
        # Select free text aligned with rating
        if rating >= 4:
            text = random.choice(POSITIVE_TEXTS)
        elif rating == 3:
            text = random.choice(NEUTRAL_TEXTS)
        else:
            text = random.choice(NEGATIVE_TEXTS)
            
        records.append({
            "response_id": f"r_{i:06d}",
            "date": record_date.isoformat(),
            "business_id": BUSINESS_ID,
            "business_name": BUSINESS_NAME,
            "survey_id": SURVEY_ID,
            "survey_name": SURVEY_NAME,
            "rating": rating,
            "response_channel": random.choice(CHANNELS),
            "free_text": text
        })

    payload = {"responses": records}
    
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        
    print(f"Generated {len(records)} records at {OUTPUT_PATH}")

if __name__ == "__main__":
    generate_dataset()