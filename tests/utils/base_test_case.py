import pytest
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch
import tempfile
import json
from pathlib import Path

from src.models.prayer_time import (
    DailyPrayerTimes,
    MonthlyPrayerTimes,
    PrayerName,
    PrayerTime,
)
from src.models.mosque import Mosque, MosqueMetadata
from src.models.calendar_config import CalendarConfig, EventDuration, AlarmConfig


class BaseTestCase:
    """Base test case with common test utilities and fixtures"""

    def setup_method(self):
        """Set up common test fixtures"""
        self.sample_prayer_times = [
            "06:49",
            "08:44",
            "12:55",
            "14:47",
            "17:08",
            "18:47",
        ]
        self.sample_year = 2025
        self.sample_month = 1
        self.sample_day = 15

        # Sample monthly data
        self.sample_month_data = {
            "1": ["06:49", "08:44", "12:55", "14:47", "17:08", "18:47"],
            "2": ["06:49", "08:44", "12:56", "14:48", "17:09", "18:48"],
            "3": ["06:49", "08:44", "12:56", "14:49", "17:10", "18:49"],
        }

        # Sample mosque data
        self.sample_mosque_data = {
            "latitude": 48.8566,
            "longitude": 2.3522,
            "name": "Grande Mosquée de Paris",
            "url": "https://www.mosquee-de-paris.org",
            "label": "paris",
            "logo": "logo.png",
            "site": "www.mosquee-de-paris.org",
            "association": "Association de la Grande Mosquée de Paris",
            "metadata": {
                "parking": True,
                "ablutions": True,
                "ramadanMeal": False,
                "otherInfo": "Historic mosque in Paris",
                "womenSpace": True,
                "janazaPrayer": True,
                "aidPrayer": True,
                "adultCourses": True,
                "childrenCourses": True,
                "handicapAccessibility": False,
                "paymentWebsite": "https://payment.mosquee-de-paris.org",
                "countryCode": "FR",
                "timezone": "Europe/Paris",
                "image": "mosque_image.jpg",
                "interiorPicture": "interior.jpg",
                "exteriorPicture": "exterior.jpg",
            },
        }

    def create_sample_daily_prayer_times(
        self, day: int = None, times: List[str] = None
    ) -> DailyPrayerTimes:
        """Create a sample DailyPrayerTimes instance"""
        day = day or self.sample_day
        times = times or self.sample_prayer_times
        return DailyPrayerTimes.from_time_list(
            times, self.sample_year, self.sample_month, day
        )

    def create_sample_monthly_prayer_times(
        self,
        year: int = None,
        month: int = None,
        month_data: Dict[str, List[str]] = None,
    ) -> MonthlyPrayerTimes:
        """Create a sample MonthlyPrayerTimes instance"""
        year = year or self.sample_year
        month = month or self.sample_month
        month_data = month_data or self.sample_month_data
        return MonthlyPrayerTimes.from_month_dict(month_data, year, month)

    def create_sample_prayer_time(
        self, year: int = None, months: List[MonthlyPrayerTimes] = None
    ) -> PrayerTime:
        """Create a sample PrayerTime instance"""
        year = year or self.sample_year
        if months is None:
            # Create a few months of sample data
            months = [
                self.create_sample_monthly_prayer_times(year, 1),
                self.create_sample_monthly_prayer_times(year, 2),
                self.create_sample_monthly_prayer_times(year, 3),
            ]
        return PrayerTime(year=year, months=months)

    def create_sample_mosque(self, **overrides) -> Mosque:
        """Create a sample Mosque instance with optional overrides"""
        data = self.sample_mosque_data.copy()
        data.update(overrides)

        # Ensure prayer_time is provided if not in overrides
        if "prayer_time" not in data and "prayerTime" not in data:
            data["prayerTime"] = self.create_sample_prayer_time()

        return Mosque(**data)

    def create_sample_mosque_metadata(self, **overrides) -> MosqueMetadata:
        """Create a sample MosqueMetadata instance with optional overrides"""
        data = self.sample_mosque_data["metadata"].copy()
        data.update(overrides)
        return MosqueMetadata(**data)

    def create_sample_calendar_config(self, **overrides) -> CalendarConfig:
        """Create a sample CalendarConfig instance with optional overrides"""
        defaults = {
            "calendar_name": "Test Mosque Prayer Times",
            "calendar_description": "Prayer times for testing",
            "include_prayers": [
                PrayerName.FAJR,
                PrayerName.DHUHR,
                PrayerName.ASR,
                PrayerName.MAGHRIB,
                PrayerName.ISHA,
            ],
            "timezone": "Europe/Paris",
        }
        defaults.update(overrides)
        return CalendarConfig(**defaults)

    def create_temp_file(self, content: str = "", suffix: str = ".txt") -> Path:
        """Create a temporary file with given content"""
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
        temp_file.write(content)
        temp_file.close()
        return Path(temp_file.name)

    def create_temp_json_file(self, data: Dict[str, Any]) -> Path:
        """Create a temporary JSON file with given data"""
        content = json.dumps(data, indent=2)
        return self.create_temp_file(content, ".json")

    def assert_time_format(self, time_str: str, msg: Optional[str] = None):
        """Assert that a string is in HH:MM format"""
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            pytest.fail(msg or f"'{time_str}' is not in HH:MM format")

    def assert_valid_prayer_name(self, prayer_name: str, msg: Optional[str] = None):
        """Assert that a prayer name is valid"""
        valid_names = [prayer.value for prayer in PrayerName]
        assert prayer_name in valid_names, (
            msg or f"'{prayer_name}' is not a valid prayer name"
        )

    def assert_coordinate_range(
        self, coord: float, coord_type: str, msg: Optional[str] = None
    ):
        """Assert that coordinate is within valid range"""
        if coord_type.lower() == "latitude":
            assert coord >= -90, msg or f"Latitude {coord} is below -90"
            assert coord <= 90, msg or f"Latitude {coord} is above 90"
        elif coord_type.lower() == "longitude":
            assert coord >= -180, msg or f"Longitude {coord} is below -180"
            assert coord <= 180, msg or f"Longitude {coord} is above 180"
        else:
            pytest.fail(f"Unknown coordinate type: {coord_type}")

    def assert_valid_datetime(self, dt: datetime, msg: Optional[str] = None):
        """Assert that datetime object is valid"""
        assert isinstance(dt, datetime), msg or "Object is not a datetime instance"
        assert dt.year is not None, msg or "Datetime year is None"
        assert dt.month is not None, msg or "Datetime month is None"
        assert dt.day is not None, msg or "Datetime day is None"
