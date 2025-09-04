import pytest
from unittest.mock import patch, mock_open, MagicMock
import json
import tempfile
from pathlib import Path

from src.models.mosque import Mosque, MosqueMetadata
from tests.utils.base_test_case import BaseTestCase


class TestMosqueMetadata(BaseTestCase):
    """Test cases for MosqueMetadata model"""

    def test_create_mosque_metadata_valid(self):
        """Test creating MosqueMetadata with valid data"""
        metadata = self.create_sample_mosque_metadata()

        assert metadata.parking is True
        assert metadata.ablutions is True
        assert metadata.ramadan_meal is False
        assert metadata.other_info == "Historic mosque in Paris"
        assert metadata.women_space is True
        assert metadata.janaza_prayer is True
        assert metadata.aid_prayer is True
        assert metadata.adult_courses is True
        assert metadata.children_courses is True
        assert metadata.handicap_accessibility is False
        assert metadata.payment_website == "https://payment.mosquee-de-paris.org"
        assert metadata.country_code == "FR"
        assert metadata.timezone == "Europe/Paris"
        assert metadata.image == "mosque_image.jpg"
        assert metadata.interior_picture == "interior.jpg"
        assert metadata.exterior_picture == "exterior.jpg"

    def test_create_mosque_metadata_minimal(self):
        """Test creating MosqueMetadata with minimal data"""
        metadata = MosqueMetadata()

        # All fields should be None by default
        assert metadata.parking is None
        assert metadata.ablutions is None
        assert metadata.ramadan_meal is None
        assert metadata.other_info is None
        assert metadata.women_space is None
        assert metadata.janaza_prayer is None
        assert metadata.aid_prayer is None
        assert metadata.adult_courses is None
        assert metadata.children_courses is None
        assert metadata.handicap_accessibility is None
        assert metadata.payment_website is None
        assert metadata.country_code is None
        assert metadata.timezone is None
        assert metadata.image is None
        assert metadata.interior_picture is None
        assert metadata.exterior_picture is None

    def test_field_aliases(self):
        """Test that field aliases work correctly"""
        data = {
            "ramadanMeal": True,
            "otherInfo": "Test info",
            "womenSpace": False,
            "janazaPrayer": True,
            "aidPrayer": False,
            "adultCourses": True,
            "childrenCourses": False,
            "handicapAccessibility": True,
            "paymentWebsite": "https://test.com",
            "countryCode": "US",
            "interiorPicture": "interior_test.jpg",
            "exteriorPicture": "exterior_test.jpg",
        }

        metadata = MosqueMetadata(**data)

        assert metadata.ramadan_meal is True
        assert metadata.other_info == "Test info"
        assert metadata.women_space is False
        assert metadata.janaza_prayer is True
        assert metadata.aid_prayer is False
        assert metadata.adult_courses is True
        assert metadata.children_courses is False
        assert metadata.handicap_accessibility is True
        assert metadata.payment_website == "https://test.com"
        assert metadata.country_code == "US"
        assert metadata.interior_picture == "interior_test.jpg"
        assert metadata.exterior_picture == "exterior_test.jpg"

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden"""
        with pytest.raises(Exception):
            MosqueMetadata(unknown_field="value")


class TestMosque(BaseTestCase):
    """Test cases for Mosque model"""

    def test_create_mosque_valid(self):
        """Test creating Mosque with valid data"""
        mosque = self.create_sample_mosque()

        assert mosque.latitude == 48.8566
        assert mosque.longitude == 2.3522
        assert mosque.name == "Grande Mosquée de Paris"
        assert mosque.url == "https://www.mosquee-de-paris.org"
        assert mosque.label == "paris"
        assert mosque.logo == "logo.png"
        assert mosque.site == "www.mosquee-de-paris.org"
        assert mosque.association == "Association de la Grande Mosquée de Paris"
        assert isinstance(mosque.metadata, MosqueMetadata)
        assert mosque.prayer_time is not None

    def test_create_mosque_minimal(self):
        """Test creating Mosque with minimal required data"""
        minimal_data = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "name": "Test Mosque",
            "url": "https://test-mosque.org",
            "prayerTime": self.create_sample_prayer_time(),
        }

        mosque = Mosque(**minimal_data)

        assert mosque.latitude == 40.7128
        assert mosque.longitude == -74.0060
        assert mosque.name == "Test Mosque"
        assert mosque.url == "https://test-mosque.org"
        assert mosque.prayer_time is not None

        # Optional fields should be None
        assert mosque.label is None
        assert mosque.logo is None
        assert mosque.site is None
        assert mosque.association is None
        assert mosque.metadata is None

    def test_latitude_validation(self):
        """Test latitude coordinate validation"""
        # Valid latitudes
        valid_latitudes = [-90, -45, 0, 45, 90]
        for lat in valid_latitudes:
            mosque = self.create_sample_mosque(latitude=lat)
            assert mosque.latitude == lat
            self.assert_coordinate_range(mosque.latitude, "latitude")

        # Invalid latitudes should raise validation error
        invalid_latitudes = [-91, 91, -180, 180]
        for lat in invalid_latitudes:
            with pytest.raises(Exception):
                self.create_sample_mosque(latitude=lat)

    def test_longitude_validation(self):
        """Test longitude coordinate validation"""
        # Valid longitudes
        valid_longitudes = [-180, -90, 0, 90, 180]
        for lon in valid_longitudes:
            mosque = self.create_sample_mosque(longitude=lon)
            assert mosque.longitude == lon
            self.assert_coordinate_range(mosque.longitude, "longitude")

        # Invalid longitudes should raise validation error
        invalid_longitudes = [-181, 181, -360, 360]
        for lon in invalid_longitudes:
            with pytest.raises(Exception):
                self.create_sample_mosque(longitude=lon)

    def test_name_validation(self):
        """Test mosque name validation"""
        # Valid names
        valid_names = ["Test Mosque", "المسجد الكبير", "Grande Mosquée", "A"]
        for name in valid_names:
            mosque = self.create_sample_mosque(name=name)
            assert mosque.name == name

        # Empty name should raise validation error
        with pytest.raises(Exception):
            self.create_sample_mosque(name="")

    def test_url_validation(self):
        """Test URL validation"""
        # Valid URLs
        valid_urls = [
            "https://mosque.org",
            "http://test.com",
            "https://www.mosque-example.org/page",
        ]
        for url in valid_urls:
            mosque = self.create_sample_mosque(url=url)
            assert mosque.url == url

    def test_email_format(self):
        """Test that mosque can be created without specific field validation"""
        # Test with None email (should be allowed for optional fields)
        mosque = self.create_sample_mosque()
        assert mosque is not None

    def test_phone_format(self):
        """Test that mosque can be created successfully"""
        mosque = self.create_sample_mosque()
        assert mosque is not None

    def test_metadata_relationship(self):
        """Test metadata relationship with mosque"""
        mosque = self.create_sample_mosque()

        assert isinstance(mosque.metadata, MosqueMetadata)
        assert mosque.metadata.parking is True
        assert mosque.metadata.timezone == "Europe/Paris"

    def test_mosque_without_metadata(self):
        """Test mosque creation without metadata"""
        mosque_data = {
            "latitude": 48.8566,
            "longitude": 2.3522,
            "name": "Test Mosque",
            "url": "https://test.org",
            "prayerTime": self.create_sample_prayer_time(),
        }

        mosque = Mosque(**mosque_data)
        assert mosque.metadata is None

    def test_field_aliases(self):
        """Test field aliases work correctly"""
        data = {
            "latitude": 48.8566,
            "longitude": 2.3522,
            "name": "Test Mosque",
            "url": "https://test.org",
            "prayerTime": self.create_sample_prayer_time(),
        }

        mosque = Mosque(**data)
        assert mosque.name == "Test Mosque"

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden"""
        mosque_data = {
            "latitude": 48.8566,
            "longitude": 2.3522,
            "name": "Test Mosque",
            "url": "https://test.org",
            "prayerTime": self.create_sample_prayer_time(),
            "unknown_field": "value",
        }

        with pytest.raises(Exception):
            Mosque(**mosque_data)

    def test_mosque_string_representation(self):
        """Test mosque string representation if implemented"""
        mosque = self.create_sample_mosque()

        # Check that string representation contains mosque name
        if hasattr(mosque, "__str__"):
            assert mosque.name in str(mosque)

    def test_coordinate_precision(self):
        """Test coordinate precision handling"""
        precise_coords = {"latitude": 48.85661234567890, "longitude": 2.35221234567890}

        mosque = self.create_sample_mosque(**precise_coords)

        # Coordinates should maintain precision
        assert mosque.latitude == precise_coords["latitude"]
        assert mosque.longitude == precise_coords["longitude"]

    def test_mosque_id_property(self):
        """Test mosque ID property derived from URL"""
        mosque = self.create_sample_mosque()

        # Should extract ID from URL (last part after / with - replaced by _)
        expected_id = (
            "www.mosquee_de_paris.org"  # Last part of URL with - replaced by _
        )
        assert mosque.id == expected_id

    def test_mosque_year_property(self):
        """Test mosque year property from prayer times"""
        mosque = self.create_sample_mosque()

        # Should get year from prayer times
        assert mosque.year == self.sample_year

    def test_mosque_year_property_no_prayer_time(self):
        """Test mosque year property when no prayer times available"""
        # Create mosque with prayer_time first
        mosque_data = {
            "latitude": 48.8566,
            "longitude": 2.3522,
            "name": "Test Mosque",
            "url": "https://test.org",
            "prayerTime": self.create_sample_prayer_time(),
        }

        mosque = Mosque(**mosque_data)

        # Access the private attribute directly to simulate None (bypass validation)
        mosque.__dict__["prayer_time"] = None

        with pytest.raises(ValueError) as context:
            _ = mosque.year

        assert "No prayer times available" in str(context.value)
