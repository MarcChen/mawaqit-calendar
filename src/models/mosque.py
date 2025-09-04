from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from src.models.prayer_time import PrayerTime
import os
import json
from src.config.settings import PROCESSED_DATA_DIR
from datetime import datetime


class MosqueMetadata(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        frozen=False,
    )

    parking: Optional[bool] = None
    ablutions: Optional[bool] = None
    ramadan_meal: Optional[bool] = Field(None, alias="ramadanMeal")
    other_info: Optional[str] = Field(None, alias="otherInfo")
    women_space: Optional[bool] = Field(None, alias="womenSpace")
    janaza_prayer: Optional[bool] = Field(None, alias="janazaPrayer")
    aid_prayer: Optional[bool] = Field(None, alias="aidPrayer")
    adult_courses: Optional[bool] = Field(None, alias="adultCourses")
    children_courses: Optional[bool] = Field(None, alias="childrenCourses")
    handicap_accessibility: Optional[bool] = Field(None, alias="handicapAccessibility")
    payment_website: Optional[str] = Field(None, alias="paymentWebsite")
    country_code: Optional[str] = Field(None, alias="countryCode")
    timezone: Optional[str] = None
    image: Optional[str] = None
    interior_picture: Optional[str] = Field(None, alias="interiorPicture")
    exterior_picture: Optional[str] = Field(None, alias="exteriorPicture")


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
    label: Optional[str] = None
    logo: Optional[str] = None
    site: Optional[str] = None
    association: Optional[str] = None
    steam_url: Optional[str] = Field(None, alias="steamUrl")
    scraped_at: Optional[datetime] = Field(None, alias="scrapedAt")  # ISO 8601 format
    prayer_time: Optional[PrayerTime] = Field(None, alias="prayerTime")
    metadata: Optional[MosqueMetadata] = None

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

        # Save prayer times
        prayer_times_path = os.path.join(mosque_dir, f"prayer_times_{self.year}.json")
        prayer_times_data = self.prayer_time.to_date_dict()
        with open(prayer_times_path, "w", encoding="utf-8") as f:
            json.dump(prayer_times_data, f, ensure_ascii=False, indent=2)
