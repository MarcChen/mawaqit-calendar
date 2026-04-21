"""Integration tests for mosque prayer time scraping.

Tests that we can successfully retrieve prayer data from real Mawaqit pages.
"""

from __future__ import annotations

import pytest

from src.scrapers.mawaqit_scraper import MawaqitScraper


class TestMosqueScraperIntegration:
    """Integration tests for scraping prayer times from Mawaqit."""

    GRANDE_MOSQUEE_PARIS_URL = "https://mawaqit.net/fr/m/grande-mosquee-de-paris"

    @pytest.mark.integration
    def test_scrape_grande_mosquee_de_paris(self):
        """Test scraping prayer data from Grande Mosquée de Paris.

        This is an integration test that makes a real HTTP request to
        the Mawaqit website to verify our scraper works correctly.
        """
        with MawaqitScraper() as scraper:
            mosque = scraper.scrape(self.GRANDE_MOSQUEE_PARIS_URL)

            # Verify mosque was scraped successfully
            assert mosque is not None, "Failed to scrape mosque data"

            # Verify basic mosque info
            assert mosque.name is not None, "Mosque name should be present"
            assert "mosquée" in mosque.name.lower() or "mosquee" in mosque.name.lower(), \
                f"Expected mosque name to contain 'mosquée', got: {mosque.name}"

            # Verify coordinates
            assert mosque.latitude is not None, "Latitude should be present"
            assert mosque.longitude is not None, "Longitude should be present"
            # Paris coordinates should be around 48.8566, 2.3522
            assert 48.0 < mosque.latitude < 49.0, \
                f"Latitude {mosque.latitude} not in Paris range"
            assert 2.0 < mosque.longitude < 3.0, \
                f"Longitude {mosque.longitude} not in Paris range"

            # Verify URL
            assert mosque.url is not None, "Mosque URL should be present"
            assert "mawaqit.net" in mosque.url, \
                f"Expected mawaqit.net in URL, got: {mosque.url}"

            # Verify prayer times
            assert mosque.prayer_time is not None, "Prayer times should be present"

            # Verify we have data for at least one month
            assert mosque.prayer_time.months, "Should have prayer time months"

            # Verify year
            assert mosque.year is not None, "Year should be extractable"
            assert 2024 <= mosque.year <= 2026, \
                f"Year {mosque.year} seems out of expected range"

            # Test getting a specific prayer time (January 1st)
            jan_1_prayers = mosque.prayer_time.get_prayer_time(1, 1)
            assert jan_1_prayers is not None, "Should have prayer times for Jan 1"

            prayers_dict = jan_1_prayers.to_dict()
            assert prayers_dict, "Prayer times should not be empty"

            # Verify expected prayers are present
            expected_prayers = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
            for prayer in expected_prayers:
                assert prayer in prayers_dict, \
                    f"Expected prayer '{prayer}' not found in {prayers_dict.keys()}"

            # Verify time format (HH:MM)
            for prayer_name, time_str in prayers_dict.items():
                assert ":" in time_str, \
                    f"Time '{time_str}' for {prayer_name} should be in HH:MM format"
                parts = time_str.split(":")
                assert len(parts) == 2, \
                    f"Time '{time_str}' should have hour and minute parts"
                hour, minute = int(parts[0]), int(parts[1])
                assert 0 <= hour <= 23, \
                    f"Hour {hour} out of range for {prayer_name}"
                assert 0 <= minute <= 59, \
                    f"Minute {minute} out of range for {prayer_name}"

    @pytest.mark.integration
    def test_mosque_metadata(self):
        """Test that mosque metadata is correctly extracted."""
        with MawaqitScraper() as scraper:
            mosque = scraper.scrape(self.GRANDE_MOSQUEE_PARIS_URL)

            assert mosque is not None
            assert mosque.metadata is not None, "Metadata should be present"

            # Timezone is important for calendar generation
            assert mosque.metadata.timezone is not None, \
                "Timezone should be present in metadata"

            # Verify ID is correctly derived from URL
            expected_id = "grande_mosquee_de_paris"
            assert mosque.id == expected_id, \
                f"Expected ID '{expected_id}', got '{mosque.id}'"

    @pytest.mark.integration
    def test_prayer_time_consistency(self):
        """Test that prayer times are consistent across the year."""
        with MawaqitScraper() as scraper:
            mosque = scraper.scrape(self.GRANDE_MOSQUEE_PARIS_URL)

            assert mosque is not None
            assert mosque.prayer_time is not None

            # Sample a few days to check consistency
            test_dates = [
                (1, 1),    # Jan 1
                (3, 15),   # March 15
                (6, 21),   # June 21
                (12, 25),  # Dec 25
            ]

            for month, day in test_dates:
                try:
                    prayers = mosque.prayer_time.get_prayer_time(month, day)
                    if prayers:  # Some dates might not have data
                        prayers_dict = prayers.to_dict()
                        assert len(prayers_dict) >= 5, \
                            f"Expected at least 5 prayers for {month}/{day}"

                        # Check that fajr is before isha (basic sanity check)
                        if "fajr" in prayers_dict and "isha" in prayers_dict:
                            fajr = prayers_dict["fajr"].split(":")
                            isha = prayers_dict["isha"].split(":")
                            fajr_hour = int(fajr[0])
                            isha_hour = int(isha[0])

                            # Fajr should be early morning, Isha in evening
                            assert fajr_hour < 12, \
                                f"Fajr at {fajr_hour} doesn't look like morning"
                            assert isha_hour >= 18 or isha_hour <= 5, \
                                f"Isha at {isha_hour} doesn't look like evening/night"

                except ValueError:
                    # Date doesn't exist (e.g., Feb 30)
                    pass
