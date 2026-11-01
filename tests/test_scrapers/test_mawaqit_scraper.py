from bs4 import BeautifulSoup

from src.scrapers.mawaqit_scraper import MawaqitScraper


def test_extract_conf_data_accepts_let_declaration(monkeypatch):
    html = '<script>let confData = {"name":"Ivry","calendar":[]};</script>'
    scraper = MawaqitScraper(delay_range=(0, 0))
    monkeypatch.setattr(
        scraper,
        "get_and_parse",
        lambda url: BeautifulSoup(html, "html.parser"),
    )

    assert scraper.extract_conf_data("https://mawaqit.net/fr/ivry") == {
        "name": "Ivry",
        "calendar": [],
    }


def test_create_mosque_metadata_extracts_shuruq():
    scraper = MawaqitScraper(delay_range=(0, 0))
    conf_data = {"parking": True, "shuruq": "07:37", "countryCode": "FR"}
    metadata = scraper.create_mosque_metadata(conf_data)
    assert metadata.shuruq == "07:37"
    assert metadata.parking is True
    assert metadata.country_code == "FR"
