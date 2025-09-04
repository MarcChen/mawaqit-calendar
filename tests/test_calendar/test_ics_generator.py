import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import tempfile
from pathlib import Path
import uuid

from icalendar import Calendar, Event

from src.calendar.ics_generator import ICSGenerator
from src.models.calendar_config import (
    CalendarConfig,
    GeneratorConfig,
    EventDuration,
    AlarmConfig,
)
from src.models.prayer_time import PrayerName, DailyPrayerTimes, MonthlyPrayerTimes
from tests.utils.base_test_case import BaseTestCase


class TestICSGenerator(BaseTestCase):
    """Test cases for ICSGenerator"""

    def setup_method(self):
        """Set up test fixtures"""
        super().setup_method()

        # Create generator config
        self.generator_config = GeneratorConfig(
            product_id="-//Test//Test Calendar//EN",
            version="2.0",
            method="PUBLISH",
            event_summary_template="{prayer_name} Prayer",
            event_description_template="Prayer time at {mosque_name}",
        )

        # Create sample ICS generator
        self.calendar_config = self.create_sample_calendar_config()
        self.mosque = self.create_sample_mosque()

    def create_sample_ics_generator(self, **overrides) -> ICSGenerator:
        """Create a sample ICSGenerator instance"""
        defaults = {
            "calendar_config": self.calendar_config,
            "generator_config": self.generator_config,
            "mosque": self.mosque,
        }
        defaults.update(overrides)
        return ICSGenerator(**defaults)

    def test_create_ics_generator_valid(self):
        """Test creating ICSGenerator with valid data"""
        generator = self.create_sample_ics_generator()

        assert isinstance(generator.calendar_config, CalendarConfig)
        assert isinstance(generator.generator_config, GeneratorConfig)
        assert isinstance(generator.mosque, type(self.mosque))
        assert generator._logger is not None

    def test_create_calendar_properties(self):
        """Test calendar creation with correct properties"""
        generator = self.create_sample_ics_generator()

        # Use private method to test calendar creation
        calendar = generator._create_calendar()

        assert isinstance(calendar, Calendar)
        assert calendar["prodid"] == self.generator_config.product_id
        assert calendar["version"] == self.generator_config.version
        assert calendar["calscale"] == "GREGORIAN"
        assert calendar["method"] == self.generator_config.method
        assert calendar["x-wr-calname"] == self.calendar_config.calendar_name
        assert calendar["x-wr-caldesc"] == self.calendar_config.calendar_description
        assert calendar["x-wr-timezone"] == self.calendar_config.timezone

    def test_get_timezone_from_config(self):
        """Test timezone retrieval from calendar config"""
        generator = self.create_sample_ics_generator()

        timezone = generator._get_timezone()

        assert isinstance(timezone, ZoneInfo)
        assert str(timezone) == "Europe/Paris"

    def test_get_timezone_from_mosque(self):
        """Test timezone retrieval from mosque metadata"""
        # Create config without timezone
        config = self.create_sample_calendar_config(timezone=None)
        generator = self.create_sample_ics_generator(calendar_config=config)

        timezone = generator._get_timezone()

        # Should fall back to mosque timezone
        assert isinstance(timezone, ZoneInfo)
        assert str(timezone) == "Europe/Paris"

    def test_get_timezone_fallback_utc(self):
        """Test timezone fallback to UTC"""
        # Create config and mosque without timezone
        config = self.create_sample_calendar_config(timezone=None)
        mosque_data = self.sample_mosque_data.copy()
        mosque_data["metadata"]["timezone"] = None
        mosque = self.create_sample_mosque(**mosque_data)

        generator = self.create_sample_ics_generator(
            calendar_config=config, mosque=mosque
        )

        timezone = generator._get_timezone()

        assert isinstance(timezone, ZoneInfo)
        assert str(timezone) == "UTC"

    def test_format_event_summary(self):
        """Test event summary formatting"""
        generator = self.create_sample_ics_generator()

        summary = generator._format_event_summary("fajr")

        assert summary == "Fajr Prayer"

    def test_format_event_description(self):
        """Test event description formatting"""
        generator = self.create_sample_ics_generator()

        description = generator._format_event_description()

        assert description == f"Prayer time at {self.mosque.name}"

    def test_format_event_description_no_mosque(self):
        """Test event description formatting without mosque data"""
        # Create a generator and test the method that handles no mosque
        generator = self.create_sample_ics_generator()

        # Temporarily set mosque to None to test the fallback
        original_mosque = generator.mosque
        generator.mosque = None

        description = generator._format_event_description()
        assert description == "Prayer time"

        # Restore the mosque
        generator.mosque = original_mosque

    def test_create_prayer_event(self):
        """Test creating a prayer event"""
        generator = self.create_sample_ics_generator()

        prayer_datetime = datetime(2025, 1, 15, 6, 49)
        event = generator._create_prayer_event("fajr", prayer_datetime)

        assert isinstance(event, Event)
        assert event["uid"] is not None
        assert event["dtstamp"] is not None
        assert event["summary"] == "Fajr Prayer"
        assert event["description"] == f"Prayer time at {self.mosque.name}"

        # Check start time
        start_time = event["dtstart"].dt
        assert start_time.year == 2025
        assert start_time.month == 1
        assert start_time.day == 15
        assert start_time.hour == 6
        assert start_time.minute == 49

        # Check end time (should be start + duration)
        end_time = event["dtend"].dt
        expected_duration = self.calendar_config.event_duration.prayer_specific.get(
            PrayerName.FAJR, self.calendar_config.event_duration.default_minutes
        )
        expected_end = start_time + timedelta(minutes=expected_duration)
        assert end_time == expected_end

    def test_event_duration_prayer_specific(self):
        """Test prayer-specific event durations"""
        generator = self.create_sample_ics_generator()

        # Test different prayers with specific durations
        test_cases = [
            (PrayerName.FAJR, 15),
            (PrayerName.DHUHR, 30),
            (PrayerName.ASR, 30),
            (PrayerName.MAGHRIB, 20),
            (PrayerName.ISHA, 30),
        ]

        for prayer, expected_duration in test_cases:
            prayer_datetime = datetime(2025, 1, 15, 12, 0)
            event = generator._create_prayer_event(prayer.value, prayer_datetime)

            start_time = event["dtstart"].dt
            end_time = event["dtend"].dt
            actual_duration = (end_time - start_time).total_seconds() / 60

            assert actual_duration == expected_duration

    def test_event_duration_default(self):
        """Test default event duration for valid prayers"""
        # Create config with custom default duration
        event_duration = EventDuration(default_minutes=45)
        calendar_config = self.create_sample_calendar_config()
        calendar_config.event_duration = event_duration

        generator = self.create_sample_ics_generator(calendar_config=calendar_config)

        # Test with shuruq which is not in the prayer_specific defaults
        prayer_datetime = datetime(2025, 1, 15, 12, 0)
        event = generator._create_prayer_event("shuruq", prayer_datetime)

        start_time = event["dtstart"].dt
        end_time = event["dtend"].dt
        actual_duration = (end_time - start_time).total_seconds() / 60

        assert actual_duration == 45

    def test_event_timezone_handling(self):
        """Test that events are created with correct timezone"""
        generator = self.create_sample_ics_generator()

        prayer_datetime = datetime(2025, 1, 15, 6, 49)
        event = generator._create_prayer_event("fajr", prayer_datetime)

        start_time = event["dtstart"].dt

        # Should have timezone info
        assert start_time.tzinfo is not None
        assert str(start_time.tzinfo) == "Europe/Paris"

    @patch("uuid.uuid4")
    def test_event_uid_generation(self, mock_uuid):
        """Test that event UIDs are properly generated"""
        mock_uuid.return_value = Mock()
        mock_uuid.return_value.__str__ = Mock(return_value="test-uuid-123")

        generator = self.create_sample_ics_generator()

        prayer_datetime = datetime(2025, 1, 15, 6, 49)
        event = generator._create_prayer_event("fajr", prayer_datetime)

        assert event["uid"] == "test-uuid-123"
        mock_uuid.assert_called_once()

    def test_prayer_filtering(self):
        """Test prayer filtering based on configuration"""
        # Create config that includes only certain prayers
        include_prayers = [PrayerName.FAJR, PrayerName.MAGHRIB]
        calendar_config = self.create_sample_calendar_config(
            include_prayers=include_prayers
        )

        generator = self.create_sample_ics_generator(calendar_config=calendar_config)

        # Verify that only specified prayers are included
        assert len(generator.calendar_config.include_prayers) == 2
        assert PrayerName.FAJR in generator.calendar_config.include_prayers
        assert PrayerName.MAGHRIB in generator.calendar_config.include_prayers
        assert PrayerName.DHUHR not in generator.calendar_config.include_prayers

    def test_exclude_sunrise_option(self):
        """Test exclude sunrise configuration option"""
        calendar_config = self.create_sample_calendar_config(exclude_sunrise=True)
        generator = self.create_sample_ics_generator(calendar_config=calendar_config)

        assert generator.calendar_config.exclude_sunrise is True

    def test_alarm_configuration(self):
        """Test alarm configuration settings"""
        alarm_config = AlarmConfig(enabled=True, minutes_before=[10, 5])
        calendar_config = self.create_sample_calendar_config()
        calendar_config.alarm_config = alarm_config

        generator = self.create_sample_ics_generator(calendar_config=calendar_config)

        assert generator.calendar_config.alarm_config.enabled is True
        assert generator.calendar_config.alarm_config.minutes_before == [10, 5]

    def test_calendar_metadata_validation(self):
        """Test calendar metadata validation"""
        generator = self.create_sample_ics_generator()

        # Check required fields
        assert generator.calendar_config.calendar_name is not None
        assert isinstance(generator.calendar_config.include_prayers, list)
        assert len(generator.calendar_config.include_prayers) > 0

    def test_generator_config_defaults(self):
        """Test generator configuration defaults"""
        generator = self.create_sample_ics_generator()

        assert generator.generator_config.version == "2.0"
        assert generator.generator_config.method == "PUBLISH"
        assert "{prayer_name}" in generator.generator_config.event_summary_template
        assert "{mosque_name}" in generator.generator_config.event_description_template

    def test_error_handling_invalid_prayer_time(self):
        """Test error handling for invalid prayer time format"""
        generator = self.create_sample_ics_generator()

        # Test with invalid datetime
        with pytest.raises(Exception):
            generator._create_prayer_event("fajr", "invalid_datetime")

    def test_mosque_integration(self):
        """Test integration with mosque data"""
        # Test with mosque having all metadata
        generator = self.create_sample_ics_generator()

        # Verify mosque data is accessible
        assert generator.mosque.name == "Grande Mosquée de Paris"
        assert generator.mosque.metadata.timezone == "Europe/Paris"

        # Test description formatting uses mosque name
        description = generator._format_event_description()
        assert generator.mosque.name in description

    def test_multiple_prayer_event_creation(self):
        """Test creating multiple prayer events"""
        generator = self.create_sample_ics_generator()

        # Create events for different prayers
        base_datetime = datetime(2025, 1, 15, 6, 0)
        prayers = [
            ("fajr", base_datetime),
            ("dhuhr", base_datetime.replace(hour=12)),
            ("maghrib", base_datetime.replace(hour=18)),
        ]

        events = []
        for prayer_name, prayer_time in prayers:
            event = generator._create_prayer_event(prayer_name, prayer_time)
            events.append(event)

        assert len(events) == 3

        # Each event should have unique UID
        uids = [event["uid"] for event in events]
        assert len(set(uids)) == 3  # All UIDs should be unique
