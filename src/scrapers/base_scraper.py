import requests
from bs4 import BeautifulSoup
import time
import random
from abc import ABC, abstractmethod
from typing import Optional, Any
import logging


class BaseScraper(ABC):
    def __init__(self, delay_range: tuple = (1, 3), timeout: int = 30):
        """
        Initialize the base scraper

        Args:
            delay_range: Tuple of (min, max) seconds to wait between requests
            timeout: Request timeout in seconds
        """
        self.delay_range = delay_range
        self.timeout = timeout
        self.session = self._create_session()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _create_session(self) -> requests.Session:
        """Create a requests session with stealth headers"""
        session = requests.Session()

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

        session.headers.update(headers)
        return session

    def _random_delay(self):
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)

    def get_page(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Fetch a page with stealth measures

        Args:
            url: URL to fetch
            **kwargs: Additional arguments for requests.get

        Returns:
            Response object or None if failed
        """
        try:
            self.logger.info("Fetching URL: %s", url)
            self._random_delay()

            # Merge any additional headers
            headers = kwargs.pop("headers", {})
            session_headers = self.session.headers.copy()
            session_headers.update(headers)

            response = self.session.get(
                url, timeout=self.timeout, headers=session_headers, **kwargs
            )
            response.raise_for_status()

            self.logger.info(f"Successfully fetched: {url}")
            return response

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None

    def parse_html(
        self, response: requests.Response, parser: str = "html.parser"
    ) -> Optional[BeautifulSoup]:
        """
        Parse HTML response into BeautifulSoup object

        Args:
            response: Response object
            parser: Parser to use (default: 'html.parser')

        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            soup = BeautifulSoup(response.text, parser)
            return soup
        except Exception as e:
            self.logger.error(f"Error parsing HTML: {e}")
            return None

    def get_and_parse(
        self, url: str, parser: str = "html.parser", **kwargs
    ) -> Optional[BeautifulSoup]:
        response = self.get_page(url, **kwargs)
        if response:
            return self.parse_html(response, parser)
        return None

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @abstractmethod
    def scrape(self, *args, **kwargs) -> Any:
        """
        Abstract method to be implemented by subclasses
        This should contain the main scraping logic
        """
        pass
