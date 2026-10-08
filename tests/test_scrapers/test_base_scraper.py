from src.scrapers.mawaqit_scraper import MawaqitScraper


def test_scraper_requests_encodings_supported_by_requests_runtime():
    scraper = MawaqitScraper(delay_range=(0, 0))

    try:
        encodings = {
            encoding.strip()
            for encoding in scraper.session.headers["Accept-Encoding"].split(",")
        }
        assert "br" not in encodings
        assert {"gzip", "deflate"}.issubset(encodings)
    finally:
        scraper.close()
