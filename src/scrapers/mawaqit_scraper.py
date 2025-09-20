import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from src.models.mosque import Mosque, MosqueMetadata
from src.models.prayer_time import PrayerTime
from src.scrapers.base_scraper import BaseScraper


class MawaqitScraper(BaseScraper):
    def __init__(self, delay_range: tuple = (1, 3), timeout: int = 30):
        super().__init__(delay_range, timeout)

    def extract_conf_data(self, url: str) -> dict | None:
        """Extract confData from the mosque page"""
        try:
            soup = self.get_and_parse(url)
            if not soup:
                return None

            for script in soup.find_all("script"):
                if script.string and "confData" in script.string:
                    # Extract the confData object
                    match = re.search(
                        r"var confData = ({.*?});", script.string, re.DOTALL
                    )
                    if match:
                        json_str = match.group(1)
                        # Fix trailing commas and other JSON issues
                        json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError as e:
                            self.logger.error(f"JSON decode error: {e}")
                            continue

            self.logger.warning(f"No confData found in {url}")
            return None

        except Exception as e:
            self.logger.error(f"Error extracting data from {url}: {e}")
            return None

    def create_mosque_metadata(self, conf_data: dict) -> MosqueMetadata:
        """Create MosqueMetadata from confData"""
        return MosqueMetadata(
            parking=conf_data.get("parking"),
            ablutions=conf_data.get("ablutions"),
            ramadanMeal=conf_data.get("ramadanMeal"),
            otherInfo=conf_data.get("otherInfo"),
            womenSpace=conf_data.get("womenSpace"),
            janazaPrayer=conf_data.get("janazaPrayer"),
            aidPrayer=conf_data.get("aidPrayer"),
            adultCourses=conf_data.get("adultCourses"),
            childrenCourses=conf_data.get("childrenCourses"),
            handicapAccessibility=conf_data.get("handicapAccessibility"),
            paymentWebsite=conf_data.get("paymentWebsite"),
            countryCode=conf_data.get("countryCode"),
            timezone=conf_data.get("timezone"),
            image=conf_data.get("image"),
            interiorPicture=conf_data.get("interiorPicture"),
            exteriorPicture=conf_data.get("exteriorPicture"),
        )

    def create_prayer_time(self, conf_data: dict) -> PrayerTime | None:
        """Create PrayerTime from confData"""
        try:
            # Extract prayer times data
            calendar_data = conf_data.get("calendar", [])

            return PrayerTime.from_calendar_data(calendar_data)
        except Exception as e:
            self.logger.error(f"Error creating PrayerTime: {e}")
            return None

    def scrape(self, url: str) -> Mosque | None:
        """
        Main scraping method - implementation of abstract method from BaseScraper

        Args:
            url: Mawaqit mosque URL to scrape

        Returns:
            Mosque object or None if failed
        """
        self.logger.debug(f"Starting to scrape mosque from: {url}")

        conf_data = self.extract_conf_data(url)
        if not conf_data:
            self.logger.error("Failed to extract confData")
            return None

        try:
            metadata = self.create_mosque_metadata(conf_data)

            prayer_time = self.create_prayer_time(conf_data)

            mosque = Mosque(
                latitude=conf_data.get("latitude"),
                longitude=conf_data.get("longitude"),
                name=conf_data.get("name"),
                url=conf_data.get("url"),
                label=conf_data.get("label"),
                logo=conf_data.get("logo"),
                site=conf_data.get("site"),
                association=conf_data.get("association"),
                steamUrl=conf_data.get("streamUrl"),
                scrapedAt=datetime.now(ZoneInfo("Europe/Paris")),
                prayerTime=prayer_time,
                metadata=metadata,
            )

            self.logger.debug(f"Successfully created Mosque object for: {mosque.name}")
            return mosque

        except Exception as e:
            self.logger.error(f"Error creating Mosque object: {e}")
            return None


def main():
    """Test the scraper"""
    import logging

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    with MawaqitScraper() as scraper:
        url = "https://mawaqit.net/fr/grande-mosquee-de-paris"

        mosque = scraper.scrape(url)
        if mosque:
            print("Successfully scraped mosque:")
            print(f"Name: {mosque.name}")
            print(f"Location: {mosque.latitude}, {mosque.longitude}")
            print(f"URL: {mosque.url}")
            print(f"Association: {mosque.association}")
            print(f"Site: {mosque.site}")
            print(f"Timezone: {mosque.metadata.timezone if mosque.metadata else 'N/A'}")
            print(f"Prayer times available: {mosque.prayer_time is not None}")
            print(f"Year of prayer times: {mosque.year if mosque.year else 'N/A'}")
            print(f"id: {mosque.id}")
            print(f"Prayer times example {mosque.prayer_time.get_prayer_time(1, 1)}")
            mosque.save()


if __name__ == "__main__":
    main()
