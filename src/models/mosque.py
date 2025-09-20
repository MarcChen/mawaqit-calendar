import json
import logging
import os
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator
from src.config.settings import GLOBAL_METADATA_PATH, PROCESSED_DATA_DIR
from src.models.prayer_time import PrayerTime

logger = logging.getLogger(__name__)


class MosqueMetadata(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",  # Allow extra fields (calendarUrl) for flexibility
        frozen=False,
    )

    parking: bool | None = None
    ablutions: bool | None = None
    ramadan_meal: bool | None = Field(None, alias="ramadanMeal")
    other_info: str | None = Field(None, alias="otherInfo")
    women_space: bool | None = Field(None, alias="womenSpace")
    janaza_prayer: bool | None = Field(None, alias="janazaPrayer")
    aid_prayer: bool | None = Field(None, alias="aidPrayer")
    adult_courses: bool | None = Field(None, alias="adultCourses")
    children_courses: bool | None = Field(None, alias="childrenCourses")
    handicap_accessibility: bool | None = Field(None, alias="handicapAccessibility")
    payment_website: str | None = Field(None, alias="paymentWebsite")
    country_code: str | None = Field(None, alias="countryCode")
    timezone: str | None = None
    image: str | None = None
    interior_picture: str | None = Field(None, alias="interiorPicture")
    exterior_picture: str | None = Field(None, alias="exteriorPicture")
    calendar_url: str | None = Field(None, alias="calendarUrl")


class Mosque(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        frozen=False,
    )

    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    name: str = Field(..., min_length=1, description="Mosque name")
    url: str = Field(..., description="Mosque website URL")
    label: str | None = None
    logo: str | None = None
    site: str | None = None
    association: str | None = None
    steam_url: str | None = Field(None, alias="steamUrl")
    scraped_at: datetime | None = Field(None, alias="scrapedAt")  # ISO 8601 format
    prayer_time: PrayerTime | None = Field(None, alias="prayerTime")
    metadata: MosqueMetadata | None = None

    @property
    def id(self) -> str:
        """Retrieve id from URL."""
        url = self.url.rstrip("/")
        if not url:
            raise ValueError("URL is empty, cannot derive ID.")
        return url.split("/")[-1].replace("-", "_")

    @property
    def year(self) -> int:
        """Retrieve year from prayer times if available."""
        if self.prayer_time:
            return self.prayer_time.year
        raise ValueError("No prayer times available")

    @model_validator(mode="after")
    def validate_prayer_time(self) -> "Mosque":
        if self.prayer_time is None:
            raise ValueError("prayer_time must be provided")

        # Validate that all months belong to the same year
        if self.prayer_time.months:
            years = {month.year for month in self.prayer_time.months}
            if len(years) > 1:
                raise ValueError("Prayer times must be within the same year.")

        return self

    def save(self):
        """Save mosque metadata and prayer times to processed data directory."""
        mosque_dir = os.path.join(PROCESSED_DATA_DIR, self.id)
        os.makedirs(mosque_dir, exist_ok=True)

        # Merge metadata and mosque info
        metadata_path = os.path.join(mosque_dir, "mosque_metadata.json")
        mosque_data = self.model_dump(
            by_alias=True, exclude={"prayer_time", "metadata"}, mode="json"
        )
        metadata_to_save = (
            self.metadata.model_dump(by_alias=True, mode="json")
            if self.metadata
            else {}
        )
        merged_data = {**mosque_data, **metadata_to_save}
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        try:
            if os.path.exists(GLOBAL_METADATA_PATH):
                with open(GLOBAL_METADATA_PATH, encoding="utf-8") as f:
                    global_metadata = json.load(f)
            else:
                global_metadata = {}

            global_metadata[self.id] = merged_data

            with open(GLOBAL_METADATA_PATH, "w", encoding="utf-8") as f:
                json.dump(global_metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error updating global metadata: {e}")

        # Save prayer times
        prayer_times_path = os.path.join(mosque_dir, f"prayer_times_{self.year}.json")
        prayer_times_data = self.prayer_time.to_date_dict()
        with open(prayer_times_path, "w", encoding="utf-8") as f:
            json.dump(prayer_times_data, f, ensure_ascii=False, indent=2)
