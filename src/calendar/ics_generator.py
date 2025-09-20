import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from icalendar import Alarm, Calendar, Event

from pydantic import BaseModel, Field, PrivateAttr
from src.config.settings import CALENDAR_DIR
from src.models.calendar_config import CalendarConfig, GeneratorConfig, PrayerName
from src.models.mosque import Mosque


class ICSGenerator(BaseModel):
    """ICS Calendar generator for prayer times"""

    calendar_config: CalendarConfig = Field(..., description="Calendar configuration")
    generator_config: GeneratorConfig = Field(default_factory=GeneratorConfig)
    mosque: Mosque = Field(..., description="Mosque data for calendar generation")

    # Private attributes for internal state
    _logger: logging.Logger = PrivateAttr()
    _calendar: Calendar | None = PrivateAttr(default=None)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._calendar = None

    def _create_calendar(self) -> Calendar:
        """Create the base calendar object"""
        cal = Calendar()

        # Set calendar properties
        cal.add("prodid", self.generator_config.product_id)
        cal.add("version", self.generator_config.version)
        cal.add("calscale", "GREGORIAN")
        cal.add("method", self.generator_config.method)

        # Set calendar metadata
        cal.add("x-wr-calname", self.calendar_config.calendar_name)
        if self.calendar_config.calendar_description:
            cal.add("x-wr-caldesc", self.calendar_config.calendar_description)

        if self.calendar_config.timezone:
            cal.add("x-wr-timezone", self.calendar_config.timezone)

        return cal

    def _get_timezone(self) -> ZoneInfo:
        """Get timezone object"""
        if self.calendar_config.timezone:
            return ZoneInfo(self.calendar_config.timezone)
        elif self.mosque and self.mosque.metadata and self.mosque.metadata.timezone:
            return ZoneInfo(self.mosque.metadata.timezone)
        else:
            return ZoneInfo("UTC")

    def _format_event_summary(self, prayer_name: str) -> str:
        """Format event summary using template"""
        return self.generator_config.event_summary_template.format(
            prayer_name=prayer_name.title(),
        )

    def _format_event_description(self) -> str:
        """Format event description using template"""
        if not self.mosque:
            return "Prayer time"

        return self.generator_config.event_description_template.format(
            mosque_name=self.mosque.name
        )

    def _create_prayer_event(
        self, prayer_name: str, prayer_datetime: datetime
    ) -> Event:
        """Create a single prayer event"""
        event = Event()

        # Basic event properties
        event.add("uid", str(uuid.uuid4()))
        event.add("dtstamp", datetime.now(self._get_timezone()))

        # Event time
        start_time = prayer_datetime.replace(tzinfo=self._get_timezone())
        event.add("dtstart", start_time)

        # Duration
        duration_minutes = self.calendar_config.event_duration.prayer_specific.get(
            PrayerName(prayer_name.lower()),
            self.calendar_config.event_duration.default_minutes,
        )
        end_time = start_time + timedelta(minutes=duration_minutes)
        event.add("dtend", end_time)

        # Event content
        event.add("summary", self._format_event_summary(prayer_name))
        event.add("description", self._format_event_description())

        # Location
        if self.generator_config.add_location_to_events and self.mosque:
            lat = self.mosque.latitude if self.mosque.metadata else 0.0
            lon = self.mosque.longitude if self.mosque.metadata else 0.0
            event.add("location", self.mosque.name)
            event.add("geo", f"{lat};{lon}")

        # URL
        if self.generator_config.add_url_to_events and self.mosque and self.mosque.url:
            event.add("url", self.mosque.url)

        # Alarms
        if self.calendar_config.alarm_config.enabled:
            for minutes_before in self.calendar_config.alarm_config.minutes_before:
                alarm = Alarm()
                alarm.add("action", "DISPLAY")
                alarm.add(
                    "description", f"{prayer_name} prayer in {minutes_before} minutes"
                )
                alarm.add("trigger", timedelta(minutes=-minutes_before))
                event.add_component(alarm)

        return event

    def _should_include_prayer(self, prayer_name: str) -> bool:
        """Check if prayer should be included based on configuration"""
        if prayer_name.lower() == "sunrise" and self.calendar_config.exclude_sunrise:
            return False

        try:
            prayer_enum = PrayerName(prayer_name.lower())
            return prayer_enum in self.calendar_config.include_prayers
        except ValueError:
            # Prayer name not in enum, include by default
            return True

    def _get_available_dates(self):
        """Get all available dates from scraped prayer time data"""
        if not self.mosque or not self.mosque.prayer_time:
            return []

        # Get the year from the mosque data
        year = self.mosque.year

        # Get all available months and days from the prayer time data
        available_dates = []

        # Iterate through all possible dates in the year
        for month in range(1, 13):
            for day in range(1, 32):
                try:
                    # Try to get prayer times for this date
                    daily_prayers = self.mosque.prayer_time.get_prayer_time(month, day)
                    if daily_prayers:
                        # Create a datetime object for this date
                        date_obj = datetime(year, month, day).date()
                        available_dates.append(date_obj)
                except (ValueError, AttributeError):
                    # Invalid date or no prayer times available
                    continue

        return sorted(available_dates)

    def generate_calendar(self) -> Calendar:
        """Generate the complete calendar"""
        if not self.mosque or not self.mosque.prayer_time:
            raise ValueError("Mosque and prayer time data are required")

        self._calendar = self._create_calendar()

        # Get all available dates from scraped data
        available_dates = self._get_available_dates()

        if not available_dates:
            self._logger.warning("No prayer time data available")
            return self._calendar

        self._logger.debug(
            f"Generating calendar for {len(available_dates)} available dates"
        )

        for current_date in available_dates:
            try:
                # Get prayer times for the current date
                daily_prayers = self.mosque.prayer_time.get_prayer_time(
                    current_date.month, current_date.day
                )

                if not daily_prayers:
                    continue

                # Create events for each prayer
                prayers_dict = daily_prayers.to_dict()

                for prayer_name, prayer_time_str in prayers_dict.items():
                    if not self._should_include_prayer(prayer_name):
                        continue

                    try:
                        # Parse prayer time
                        prayer_time = datetime.strptime(prayer_time_str, "%H:%M").time()
                        prayer_datetime = datetime.combine(current_date, prayer_time)

                        # Create and add event
                        event = self._create_prayer_event(prayer_name, prayer_datetime)
                        self._calendar.add_component(event)

                    except Exception as e:
                        self._logger.error(
                            f"Error creating event for {prayer_name} on {current_date}: {e}"  # noqa E501
                        )
                        continue

            except Exception as e:
                self._logger.error(f"Error processing date {current_date}: {e}")

        self._logger.debug(
            f"Generated calendar with {len(self._calendar.subcomponents)} events"
        )
        return self._calendar

    def save_calendar(self) -> None:
        """Save calendar to file"""
        if not self._calendar:
            self._calendar = self.generate_calendar()

        filepath = CALENDAR_DIR + f"/{self.mosque.year}/{self.mosque.id}.ics"

        # Create directory if needed
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        # Write calendar
        with open(filepath, "wb") as f:
            f.write(self._calendar.to_ical())

        self._logger.debug(f"Calendar saved to: {filepath}")

    def get_calendar_string(self) -> str:
        """Get calendar as string"""
        if not self._calendar:
            self._calendar = self.generate_calendar()

        return self._calendar.to_ical().decode("utf-8")


def generate_prayer_calendar(
    mosque: Mosque,
    calendar_name: str | None = None,
    output_file: str | None = None,
) -> ICSGenerator:
    """Convenience function to create a prayer calendar"""

    if not calendar_name:
        calendar_name = f"{mosque.name} - Prayer Times"

    calendar_config = CalendarConfig(
        calendar_name=calendar_name,
        calendar_description=f"Prayer times for {mosque.name}",
        timezone=mosque.metadata.timezone if mosque.metadata else None,
        output_filename=output_file,
    )

    generator = ICSGenerator(calendar_config=calendar_config, mosque=mosque)

    return generator


# Example usage
def main():
    import logging

    from src.scrapers.mawaqit_scraper import MawaqitScraper

    logging.basicConfig(level=logging.INFO)

    with MawaqitScraper() as scraper:
        mosque = scraper.scrape("https://mawaqit.net/fr/grande-mosquee-de-paris")

        if mosque:
            generator = generate_prayer_calendar(
                mosque=mosque, output_file="grande_mosquee_paris.ics"
            )

            generator.save_calendar()
            print("Calendar generated for all available prayer time data")


if __name__ == "__main__":
    main()
