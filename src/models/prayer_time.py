import logging
from calendar import monthrange
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PrayerName(str, Enum):
    FAJR = "fajr"
    SHURUQ = "shuruq"
    DHUHR = "dhuhr"
    ASR = "asr"
    MAGHRIB = "maghrib"
    ISHA = "isha"


class DailyPrayerTimes(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        frozen=False,
    )

    day: int = Field(..., ge=1, le=31, description="Day of the month (1-31)")
    fajr: str = Field(..., description="Fajr prayer time in HH:MM format")
    shuruq: str = Field(..., description="Sunrise time in HH:MM format")
    dhuhr: str = Field(..., description="Dhuhr prayer time in HH:MM format")
    asr: str = Field(..., description="Asr prayer time in HH:MM format")
    maghrib: str = Field(..., description="Maghrib prayer time in HH:MM format")
    isha: str = Field(..., description="Isha prayer time in HH:MM format")

    @classmethod
    def from_time_list(
        cls, times: list[str], year: int, month: int, day: int
    ) -> "DailyPrayerTimes":
        """Create DailyPrayerTimes from a list of time strings and date info"""
        if len(times) != 6:
            raise ValueError("Must provide exactly 6 times (5 prayers + 1 sunrise)")

        return cls(
            day=day,
            fajr=times[0],
            shuruq=times[1],
            dhuhr=times[2],
            asr=times[3],
            maghrib=times[4],
            isha=times[5],
        )

    def get_datetime(self, prayer_name: PrayerName, year: int, month: int) -> datetime:
        """Get datetime object for a specific prayer"""
        time_str = getattr(self, prayer_name.value)
        date_obj = date(year, month, self.day)
        time_obj = datetime.strptime(time_str, "%H:%M").time()
        return datetime.combine(date_obj, time_obj)

    def get_all_datetimes(self, year: int, month: int) -> dict[str, datetime]:
        """Get all prayer times as datetime objects"""
        return {
            prayer.value: self.get_datetime(prayer, year, month)
            for prayer in PrayerName
        }

    def to_dict(self) -> dict[str, str]:
        """Convert prayer times to dictionary format"""
        return {
            "fajr": self.fajr,
            "shuruq": self.shuruq,
            "dhuhr": self.dhuhr,
            "asr": self.asr,
            "maghrib": self.maghrib,
            "isha": self.isha,
        }


class MonthlyPrayerTimes(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        frozen=False,
    )

    year: int = Field(..., description="Year")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    days: list[DailyPrayerTimes] = Field(
        ..., description="Prayer times for each day of the month"
    )

    @classmethod
    def from_month_dict(
        cls, month_data: dict[str, list[str]], year: int, month: int
    ) -> "MonthlyPrayerTimes":
        """Create MonthlyPrayerTimes from raw month data like {'1': [...]}"""
        days = []
        sorted_days = sorted(month_data.keys(), key=int)

        for day_str in sorted_days:
            day = int(day_str)
            daily_prayer = DailyPrayerTimes.from_time_list(
                month_data[day_str], year, month, day
            )
            days.append(daily_prayer)

        return cls(year=year, month=month, days=days)

    def get_day_prayers(self, day: int) -> DailyPrayerTimes | None:
        """Get prayer times for a specific day of the month"""
        for daily_prayer in self.days:
            if daily_prayer.day == day:
                return daily_prayer
        return None


class PrayerTime(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        frozen=False,
    )

    year: int = Field(..., description="Year of the prayer times")
    months: list[MonthlyPrayerTimes] = Field(
        ..., description="Monthly prayer times for the year"
    )

    @classmethod
    def from_calendar_data(
        cls, calendar_data: list[dict[str, list[str]]]
    ) -> "PrayerTime":
        current_year = datetime.now().year
        months = []

        for month_idx, month_data in enumerate(calendar_data, start=1):
            # Validate days in month
            days_in_month = monthrange(current_year, month_idx)[1]
            filtered_month_data = {}

            for day_str, times in month_data.items():
                day = int(day_str)
                if day <= days_in_month:
                    filtered_month_data[day_str] = times
                else:
                    logging.debug(
                        f"Skipping invalid day {day} for month {month_idx} and year {current_year}"  # noqa E501
                    )

            monthly_prayers = MonthlyPrayerTimes.from_month_dict(
                filtered_month_data, current_year, month_idx
            )
            months.append(monthly_prayers)

        return cls(year=current_year, months=months)

    @classmethod
    def from_monthly_data(cls, months: list[MonthlyPrayerTimes]) -> "PrayerTime":
        if not months:
            raise ValueError("Must provide at least one month")

        year = months[0].year
        # Validate all months are from the same year
        for month in months:
            if month.year != year:
                raise ValueError("All months must be from the same year")

        return cls(year=year, months=months)

    def get_month(self, month: int) -> MonthlyPrayerTimes | None:
        """Get prayer times for a specific month"""
        for monthly_prayer in self.months:
            if monthly_prayer.month == month:
                return monthly_prayer
        return None

    def get_prayer_time(self, month: int, day: int) -> DailyPrayerTimes | None:
        """Get prayer times for a specific date"""
        monthly_prayer = self.get_month(month)
        if monthly_prayer:
            return monthly_prayer.get_day_prayers(day)
        return None

    def get_all_daily_prayers(self) -> list[DailyPrayerTimes]:
        """Get flattened list of all daily prayer times for the year"""
        all_days = []
        for month in self.months:
            all_days.extend(month.days)
        return all_days

    def to_date_dict(self) -> dict[str, dict[str, str]]:
        """Export prayer times as a dictionary with date keys in YYYY-MM-DD format"""
        result = {}

        for month in self.months:
            for daily_prayer in month.days:
                date_key = f"{self.year:04d}-{month.month:02d}-{daily_prayer.day:02d}"

                # Create prayer times dict (excluding shuruq as it's not a prayer)
                result[date_key] = {
                    "fajr": daily_prayer.fajr,
                    "shuruq": daily_prayer.shuruq,
                    "dhuhr": daily_prayer.dhuhr,
                    "asr": daily_prayer.asr,
                    "maghrib": daily_prayer.maghrib,
                    "isha": daily_prayer.isha,
                }

        return result


if __name__ == "__main__":
    from tests.utils.data import calendar_data

    prayer_time = PrayerTime.from_calendar_data(calendar_data)

    # Test the model
    print("Prayer times model created successfully!")
    print(f"Year: {prayer_time.year}")
    print(f"Number of months: {len(prayer_time.months)}")

    # Get specific day
    jan_1 = prayer_time.get_prayer_time(1, 1)
    if jan_1:
        print("January 1st prayer times:")
        print(f"  Day: {jan_1.day}")
        print(f"  Fajr: {jan_1.fajr}")
        print(f"  Shuruq: {jan_1.shuruq}")

        # Get as datetime objects
        datetimes = jan_1.get_all_datetimes(prayer_time.year, 1)
        print(f"  Fajr datetime: {datetimes['fajr']}")
        print(f"  Isha datetime: {datetimes['isha']}")

    # Test month access
    january = prayer_time.get_month(1)
    if january:
        print(f"\nJanuary has {len(january.days)} days")
