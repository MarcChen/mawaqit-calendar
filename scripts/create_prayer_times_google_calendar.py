import json
import logging
from pathlib import Path
from time import sleep

from googleapiclient.errors import HttpError  # Add this import at the top
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress

from src.calendar.google_calendar import GoogleCalendarClient
from src.calendar.ics_generator import generate_prayer_calendar
from src.models.country_enum import CountrySelector
from src.models.google_calendar_config import GoogleCalendarConfig
from src.scrapers.mawaqit_scraper import MawaqitScraper

console = Console()


def main(country: CountrySelector, verbose: int):
    # Setup logger with RichHandler
    logging.basicConfig(
        level=verbose,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console)],
    )
    logger = logging.getLogger("PrayerTimesGoogleCalendar")

    urls_path = Path(f"data/mawaqit_url_{country.value}.json")
    with open(urls_path, encoding="utf-8") as f:
        mosque_urls = json.load(f)

    config = GoogleCalendarConfig(
        credentials_path="client_secret.json",
        token_path="token.json",
        scopes=["https://www.googleapis.com/auth/calendar"],
    )
    calendar_client = GoogleCalendarClient(config)

    scraper = MawaqitScraper()

    with Progress(console=console) as progress:
        task = progress.add_task("[green]Processing mosques...", total=len(mosque_urls))
        for mosque_obj in mosque_urls:
            if mosque_obj.get("processed"):
                progress.advance(task)
                continue

            slug = mosque_obj["slug"]
            url = f"https://mawaqit.net/fr/{slug}"
            logger.debug(f"Scraping mosque: {url}")
            mosque = scraper.scrape(url)
            if not mosque:
                logger.error(f"Failed to scrape mosque: {url}")
                progress.advance(task)
                continue

            calendar_id = None
            try:
                mosque.save()

                generator = generate_prayer_calendar(mosque)
                generator.save_calendar()
                ics_path = Path(f"data/calendars/{mosque.year}/{mosque.id}.ics")

                cal_name = f"{mosque.name} - Prayer Times"
                timezone = mosque.metadata.timezone if mosque.metadata else "UTC"
                try:
                    calendar_id = calendar_client.create_calendar(cal_name, timezone)
                except ValueError:
                    calendar_id = calendar_client.get_calendar_id_by_name(cal_name)
                    logger.warning(f"Using existing calendar: {calendar_id}")
                except HttpError as http_err:
                    if http_err.resp.status == 403 and "quotaExceeded" in str(http_err):
                        logger.error(
                            f"Reached Google Calendar creation rate limit: {http_err}"
                        )
                        logger.error(
                            f"Stopping processing at mosque '{slug}' due to quota exceeded."  # noqa: E501
                        )
                        break
                    else:
                        raise

                calendar_client.make_calendar_public(calendar_id)

                calendar_client.add_events_from_ics_batch(calendar_id, str(ics_path))

                public_ics_url = calendar_client.get_public_ics_url(calendar_id)
                mosque.metadata.calendar_url = public_ics_url
                mosque.save()

                mosque_obj["processed"] = True

            except Exception as e:
                logger.error(f"Error processing mosque '{slug}': {e}")
                # Fallback: delete calendar if it was created
                if calendar_id:
                    try:
                        calendar_client.delete_calendar(calendar_id)
                        logger.warning(
                            f"Deleted calendar for mosque '{slug}' due to error."
                        )
                    except Exception as del_e:
                        logger.error(
                            f"Failed to delete calendar for mosque '{slug}': {del_e}"
                        )
                mosque_obj["processed"] = False

            with open(urls_path, "w", encoding="utf-8") as f:
                json.dump(mosque_urls, f, ensure_ascii=False, indent=2)
            progress.advance(task)

            sleep(120)  # To respect Google Calendar API rate limits

    logger.info("All mosques processed and calendars created.")


if __name__ == "__main__":
    main(CountrySelector.FRANCE, verbose=logging.INFO)
