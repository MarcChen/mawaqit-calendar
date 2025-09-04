import pytest
from datetime import datetime, date
from unittest.mock import patch

from src.models.prayer_time import DailyPrayerTimes, MonthlyPrayerTimes, PrayerName
from tests.utils.base_test_case import BaseTestCase


class TestPrayerName(BaseTestCase):
    """Test cases for PrayerName enum"""

    def test_prayer_name_values(self):
        """Test that all prayer names have correct string values"""
        expected_prayers = {
            PrayerName.FAJR: "fajr",
            PrayerName.SHURUQ: "shuruq",
            PrayerName.DHUHR: "dhuhr",
            PrayerName.ASR: "asr",
            PrayerName.MAGHRIB: "maghrib",
            PrayerName.ISHA: "isha",
        }

        for prayer, expected_value in expected_prayers.items():
            assert prayer.value == expected_value

    def test_prayer_name_count(self):
        """Test that we have exactly 6 prayer names"""
        assert len(PrayerName) == 6


class TestDailyPrayerTimes(BaseTestCase):
    """Test cases for DailyPrayerTimes model"""

    def test_create_daily_prayer_times_valid(self):
        """Test creating DailyPrayerTimes with valid data"""
        daily_prayer = self.create_sample_daily_prayer_times()

        assert daily_prayer.day == self.sample_day
        assert daily_prayer.fajr == "06:49"
        assert daily_prayer.shuruq == "08:44"
        assert daily_prayer.dhuhr == "12:55"
        assert daily_prayer.asr == "14:47"
        assert daily_prayer.maghrib == "17:08"
        assert daily_prayer.isha == "18:47"

    def test_from_time_list_valid(self):
        """Test creating DailyPrayerTimes from time list"""
        times = ["05:30", "07:15", "12:30", "15:45", "18:20", "19:45"]
        daily_prayer = DailyPrayerTimes.from_time_list(times, 2025, 1, 10)

        assert daily_prayer.day == 10
        assert daily_prayer.fajr == "05:30"
        assert daily_prayer.shuruq == "07:15"
        assert daily_prayer.dhuhr == "12:30"
        assert daily_prayer.asr == "15:45"
        assert daily_prayer.maghrib == "18:20"
        assert daily_prayer.isha == "19:45"

    def test_from_time_list_invalid_count(self):
        """Test that from_time_list raises error with wrong number of times"""
        with pytest.raises(ValueError) as exc_info:
            DailyPrayerTimes.from_time_list(["05:30", "07:15"], 2025, 1, 10)

        assert "Must provide exactly 6 times" in str(exc_info.value)

    def test_day_validation(self):
        """Test day field validation"""
        # Valid day
        daily_prayer = self.create_sample_daily_prayer_times(day=1)
        assert daily_prayer.day == 1

        daily_prayer = self.create_sample_daily_prayer_times(day=31)
        assert daily_prayer.day == 31

        # Invalid days should raise validation error
        with pytest.raises(Exception):
            DailyPrayerTimes(
                day=0,
                fajr="06:00",
                shuruq="08:00",
                dhuhr="12:00",
                asr="15:00",
                maghrib="18:00",
                isha="20:00",
            )

        with pytest.raises(Exception):
            DailyPrayerTimes(
                day=32,
                fajr="06:00",
                shuruq="08:00",
                dhuhr="12:00",
                asr="15:00",
                maghrib="18:00",
                isha="20:00",
            )

    def test_get_datetime_valid_prayer(self):
        """Test getting datetime for a specific prayer"""
        daily_prayer = self.create_sample_daily_prayer_times()

        fajr_datetime = daily_prayer.get_datetime(PrayerName.FAJR, 2025, 1)

        self.assert_valid_datetime(fajr_datetime)
        assert fajr_datetime.year == 2025
        assert fajr_datetime.month == 1
        assert fajr_datetime.day == self.sample_day
        assert fajr_datetime.hour == 6
        assert fajr_datetime.minute == 49

    def test_get_all_datetimes(self):
        """Test getting all prayer times as datetime objects"""
        daily_prayer = self.create_sample_daily_prayer_times()

        all_datetimes = daily_prayer.get_all_datetimes(2025, 1)

        assert len(all_datetimes) == 6

        # Check that all prayer names are present
        for prayer in PrayerName:
            assert prayer.value in all_datetimes
            self.assert_valid_datetime(all_datetimes[prayer.value])

        # Check specific times
        assert all_datetimes["fajr"].hour == 6
        assert all_datetimes["fajr"].minute == 49
        assert all_datetimes["isha"].hour == 18
        assert all_datetimes["isha"].minute == 47

    def test_to_dict(self):
        """Test converting prayer times to dictionary"""
        daily_prayer = self.create_sample_daily_prayer_times()

        prayer_dict = daily_prayer.to_dict()

        expected_dict = {
            "fajr": "06:49",
            "shuruq": "08:44",
            "dhuhr": "12:55",
            "asr": "14:47",
            "maghrib": "17:08",
            "isha": "18:47",
        }

        assert prayer_dict == expected_dict

    def test_time_format_validation(self):
        """Test that time strings are in correct format"""
        daily_prayer = self.create_sample_daily_prayer_times()

        # All times should be in HH:MM format
        self.assert_time_format(daily_prayer.fajr)
        self.assert_time_format(daily_prayer.shuruq)
        self.assert_time_format(daily_prayer.dhuhr)
        self.assert_time_format(daily_prayer.asr)
        self.assert_time_format(daily_prayer.maghrib)
        self.assert_time_format(daily_prayer.isha)


class TestMonthlyPrayerTimes(BaseTestCase):
    """Test cases for MonthlyPrayerTimes model"""

    def test_create_monthly_prayer_times_valid(self):
        """Test creating MonthlyPrayerTimes with valid data"""
        monthly_prayer = self.create_sample_monthly_prayer_times()

        assert monthly_prayer.year == self.sample_year
        assert monthly_prayer.month == self.sample_month
        assert len(monthly_prayer.days) == 3  # 3 days in sample data

    def test_from_month_dict_valid(self):
        """Test creating MonthlyPrayerTimes from month dictionary"""
        month_data = {
            "1": ["06:00", "08:00", "12:00", "15:00", "18:00", "20:00"],
            "3": ["06:02", "08:02", "12:02", "15:02", "18:02", "20:02"],
            "2": ["06:01", "08:01", "12:01", "15:01", "18:01", "20:01"],
        }

        monthly_prayer = MonthlyPrayerTimes.from_month_dict(month_data, 2025, 2)

        assert monthly_prayer.year == 2025
        assert monthly_prayer.month == 2
        assert len(monthly_prayer.days) == 3

        # Check that days are sorted correctly
        days = [day.day for day in monthly_prayer.days]
        assert days == [1, 2, 3]

    def test_month_validation(self):
        """Test month field validation"""
        # Valid months
        for month in range(1, 13):
            monthly_prayer = self.create_sample_monthly_prayer_times(month=month)
            assert monthly_prayer.month == month

        # Invalid months should raise validation error
        with pytest.raises(Exception):
            days = [self.create_sample_daily_prayer_times()]
            MonthlyPrayerTimes(year=2025, month=0, days=days)

        with pytest.raises(Exception):
            days = [self.create_sample_daily_prayer_times()]
            MonthlyPrayerTimes(year=2025, month=13, days=days)

    def test_year_validation(self):
        """Test year field validation"""
        # Should accept reasonable years
        monthly_prayer = self.create_sample_monthly_prayer_times(year=2025)
        assert monthly_prayer.year == 2025

        monthly_prayer = self.create_sample_monthly_prayer_times(year=1900)
        assert monthly_prayer.year == 1900

    def test_empty_days_list(self):
        """Test behavior with empty days list"""
        monthly_prayer = MonthlyPrayerTimes(year=2025, month=1, days=[])
        assert len(monthly_prayer.days) == 0

    def test_daily_prayer_times_consistency(self):
        """Test that all daily prayer times in monthly data are consistent"""
        monthly_prayer = self.create_sample_monthly_prayer_times()

        for daily_prayer in monthly_prayer.days:
            assert isinstance(daily_prayer, DailyPrayerTimes)
            self.assert_time_format(daily_prayer.fajr)
            self.assert_time_format(daily_prayer.shuruq)
            self.assert_time_format(daily_prayer.dhuhr)
            self.assert_time_format(daily_prayer.asr)
            self.assert_time_format(daily_prayer.maghrib)
            self.assert_time_format(daily_prayer.isha)
