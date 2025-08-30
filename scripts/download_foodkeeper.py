import requests
import json
import os

def download_foodkeeper_data():
    url = "https://www.foodsafety.gov/foodkeeper/downloads/FoodKeeperData.json"
    response = requests.get(url)

    if response.status_code == 200:
        with open(os.path.join(os.path.dirname(__file__), '../app/data/foodkeeper.json'), 'w') as f:
            json.dump(response.json(), f, indent=4)
        print("FoodKeeper data downloaded and saved as foodkeeper.json.")
    else:
        print(f"Failed to download FoodKeeper data. Status code: {response.status_code}")

if __name__ == "__main__":
    download_foodkeeper_data()