from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
from src.models.prayer_time import PrayerName


class EventDuration(BaseModel):
    """Duration configuration for calendar events"""

    default_minutes: int = Field(
        default=60, description="Default event duration in minutes"
    )
    prayer_specific: Dict[PrayerName, int] = Field(
        default_factory=lambda: {
            PrayerName.FAJR: 15,
            PrayerName.DHUHR: 30,
            PrayerName.ASR: 30,
            PrayerName.MAGHRIB: 20,
            PrayerName.ISHA: 30,
        },
        description="Specific duration for each prayer in minutes",
    )


class AlarmConfig(BaseModel):
    """Alarm/reminder configuration for events"""

    enabled: bool = Field(default=True, description="Enable alarms for events")
    minutes_before: List[int] = Field(
        default=[15, 5], description="Minutes before event to trigger alarm"
    )


class CalendarConfig(BaseModel):
    """Configuration for calendar generation"""

    calendar_name: str = Field(..., description="Name of the calendar")
    calendar_description: Optional[str] = Field(
        None, description="Calendar description"
    )

    # Prayer selection
    include_prayers: List[PrayerName] = Field(
        default=[
            PrayerName.FAJR,
            PrayerName.DHUHR,
            PrayerName.ASR,
            PrayerName.MAGHRIB,
            PrayerName.ISHA,
        ],
        description="Prayers to include in calendar",
    )
    exclude_sunrise: bool = Field(
        default=False, description="Exclude sunrise from calendar"
    )

    # Event configuration
    event_duration: EventDuration = Field(default_factory=EventDuration)
    alarm_config: AlarmConfig = Field(default_factory=AlarmConfig)

    # Calendar metadata
    timezone: Optional[str] = Field(None, description="Timezone for the calendar")
    location: Optional[str] = Field(None, description="Location description")

    # Output configuration
    output_filename: Optional[str] = Field(
        None, description="Output filename for ICS file"
    )

    @field_validator("output_filename")
    def validate_output_filename(cls, v):
        if v and not v.endswith(".ics"):
            return f"{v}.ics"
        return v


class GeneratorConfig(BaseModel):
    """Configuration for the ICS generator itself"""

    product_id: str = Field(
        default="-//Mawaqit Calendar//Prayer Times//EN",
        description="Calendar product identifier",
    )
    version: str = Field(default="2.0", description="ICS version")
    method: Optional[str] = Field(default="PUBLISH", description="Calendar method")

    # Event formatting
    event_summary_template: str = Field(
        default="{prayer_name}", description="Template for event summary"
    )
    event_description_template: str = Field(
        default="Prayer time at {mosque_name}",
        description="Template for event description",
    )

    # Additional features
    add_location_to_events: bool = Field(
        default=True, description="Add location to events"
    )
    add_url_to_events: bool = Field(
        default=True, description="Add mosque URL to events"
    )

    class Config:
        use_enum_values = True
