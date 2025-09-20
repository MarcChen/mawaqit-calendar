import json
from pathlib import Path

import requests

from src.models.country_enum import CountrySelector

base_path = Path(__file__).parent.parent.parent / "data"
base_api_url = "https://mawaqit.net/api/2.0/mosque/map/{country_code}"


def fetch_mosque_data(country: CountrySelector):
    api_url = base_api_url.format(country_code=country.value)
    response = requests.get(api_url)
    response.raise_for_status()
    save_path = base_path / f"mawaqit_url_{country.value}.json"
    data = response.json()
    for obj in data:
        obj["processed"] = False
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data


if __name__ == "__main__":
    print("\nFetching mosque data directly from API...")
    mosque_data = fetch_mosque_data(CountrySelector.FRANCE)
    print(f"Extracted {len(mosque_data)} mosques from API.")
