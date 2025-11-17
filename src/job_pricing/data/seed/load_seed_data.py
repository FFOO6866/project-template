"""
Seed Data Loader

Loads initial seed data into the database:
- Locations (Singapore and major cities)
- Currency exchange rates (SGD, USD, EUR, GBP, MYR, CNY)
- Initial salary bands

Usage:
    python -m data.seed.load_seed_data
"""

import sys
from pathlib import Path
from datetime import date
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.job_pricing.core.database import get_session
from src.job_pricing.models.supporting import Location, LocationIndex, CurrencyExchangeRate
from src.job_pricing.models.hris import GradeSalaryBand


def load_locations(session):
    """Load initial location data for global cities"""

    locations = [
        # Singapore
        {
            "country_code": "SG",
            "country_name": "Singapore",
            "city": "Singapore",
            "region": "Central",
            "latitude": Decimal("1.3521"),
            "longitude": Decimal("103.8198"),
            "timezone": "Asia/Singapore",
            "is_active": True,
        },
        # Malaysia
        {
            "country_code": "MY",
            "country_name": "Malaysia",
            "city": "Kuala Lumpur",
            "region": "Federal Territory",
            "latitude": Decimal("3.1390"),
            "longitude": Decimal("101.6869"),
            "timezone": "Asia/Kuala_Lumpur",
            "is_active": True,
        },
        # United States
        {
            "country_code": "US",
            "country_name": "United States",
            "city": "New York",
            "region": "New York",
            "latitude": Decimal("40.7128"),
            "longitude": Decimal("-74.0060"),
            "timezone": "America/New_York",
            "is_active": True,
        },
        {
            "country_code": "US",
            "country_name": "United States",
            "city": "San Francisco",
            "region": "California",
            "latitude": Decimal("37.7749"),
            "longitude": Decimal("-122.4194"),
            "timezone": "America/Los_Angeles",
            "is_active": True,
        },
        # United Kingdom
        {
            "country_code": "GB",
            "country_name": "United Kingdom",
            "city": "London",
            "region": "England",
            "latitude": Decimal("51.5074"),
            "longitude": Decimal("-0.1278"),
            "timezone": "Europe/London",
            "is_active": True,
        },
        # China
        {
            "country_code": "CN",
            "country_name": "China",
            "city": "Shanghai",
            "region": "Shanghai",
            "latitude": Decimal("31.2304"),
            "longitude": Decimal("121.4737"),
            "timezone": "Asia/Shanghai",
            "is_active": True,
        },
        # India
        {
            "country_code": "IN",
            "country_name": "India",
            "city": "Bangalore",
            "region": "Karnataka",
            "latitude": Decimal("12.9716"),
            "longitude": Decimal("77.5946"),
            "timezone": "Asia/Kolkata",
            "is_active": True,
        },
    ]

    loaded = 0
    skipped = 0

    for loc_data in locations:
        # Check if location already exists
        existing = session.query(Location).filter_by(
            country_code=loc_data["country_code"],
            city=loc_data["city"]
        ).first()

        if existing:
            print(f"  ⊗ Skipped: {loc_data['city']}, {loc_data['country_code']} (already exists)")
            skipped += 1
            continue

        location = Location(**loc_data)
        session.add(location)
        print(f"  + Added: {loc_data['city']}, {loc_data['country_code']}")
        loaded += 1

    session.commit()
    return loaded, skipped


def load_currency_rates(session):
    """Load current currency exchange rates (to SGD)"""

    today = date.today()

    # Exchange rates as of 2025-01-11 (to SGD)
    rates = [
        {"from_currency": "SGD", "to_currency": "SGD", "rate": Decimal("1.0000"), "source": "Base currency"},
        {"from_currency": "USD", "to_currency": "SGD", "rate": Decimal("1.3500"), "source": "Market rate"},
        {"from_currency": "EUR", "to_currency": "SGD", "rate": Decimal("1.4200"), "source": "Market rate"},
        {"from_currency": "GBP", "to_currency": "SGD", "rate": Decimal("1.6800"), "source": "Market rate"},
        {"from_currency": "MYR", "to_currency": "SGD", "rate": Decimal("0.3000"), "source": "Market rate"},
        {"from_currency": "CNY", "to_currency": "SGD", "rate": Decimal("0.1850"), "source": "Market rate"},
        {"from_currency": "INR", "to_currency": "SGD", "rate": Decimal("0.0160"), "source": "Market rate"},
        # Reverse rates (SGD to other currencies)
        {"from_currency": "SGD", "to_currency": "USD", "rate": Decimal("0.7407"), "source": "Market rate"},
        {"from_currency": "SGD", "to_currency": "EUR", "rate": Decimal("0.7042"), "source": "Market rate"},
        {"from_currency": "SGD", "to_currency": "GBP", "rate": Decimal("0.5952"), "source": "Market rate"},
        {"from_currency": "SGD", "to_currency": "MYR", "rate": Decimal("3.3333"), "source": "Market rate"},
        {"from_currency": "SGD", "to_currency": "CNY", "rate": Decimal("5.4054"), "source": "Market rate"},
        {"from_currency": "SGD", "to_currency": "INR", "rate": Decimal("62.5000"), "source": "Market rate"},
    ]

    loaded = 0
    skipped = 0

    for rate_data in rates:
        # Check if rate already exists for today
        existing = session.query(CurrencyExchangeRate).filter_by(
            from_currency=rate_data["from_currency"],
            to_currency=rate_data["to_currency"],
            effective_date=today
        ).first()

        if existing:
            print(f"  ⊗ Skipped: {rate_data['from_currency']} → {rate_data['to_currency']} (already exists)")
            skipped += 1
            continue

        rate = CurrencyExchangeRate(
            from_currency=rate_data["from_currency"],
            to_currency=rate_data["to_currency"],
            exchange_rate=rate_data["rate"],
            effective_date=today,
            source=rate_data["source"]
        )
        session.add(rate)
        print(f"  + Added: {rate_data['from_currency']} → {rate_data['to_currency']} = {rate_data['rate']}")
        loaded += 1

    session.commit()
    return loaded, skipped


def load_salary_bands(session):
    """Load initial salary band references for Singapore"""

    # Get Singapore location
    singapore = session.query(Location).filter_by(
        country_code="SG",
        city="Singapore"
    ).first()

    if not singapore:
        print("  ⚠ Warning: Singapore location not found, skipping salary bands")
        return 0, 0

    # Sample salary bands for common grades
    bands = [
        {"grade": "Junior", "min": 36000, "max": 60000, "currency": "SGD", "period": "annual"},
        {"grade": "Mid-Level", "min": 60000, "max": 96000, "currency": "SGD", "period": "annual"},
        {"grade": "Senior", "min": 96000, "max": 144000, "currency": "SGD", "period": "annual"},
        {"grade": "Lead", "min": 120000, "max": 180000, "currency": "SGD", "period": "annual"},
        {"grade": "Principal", "min": 150000, "max": 240000, "currency": "SGD", "period": "annual"},
        {"grade": "Director", "min": 180000, "max": 300000, "currency": "SGD", "period": "annual"},
    ]

    loaded = 0
    skipped = 0

    for band_data in bands:
        # Check if band already exists
        existing = session.query(GradeSalaryBand).filter_by(
            internal_grade=band_data["grade"],
            location_id=singapore.id
        ).first()

        if existing:
            print(f"  ⊗ Skipped: {band_data['grade']} (already exists)")
            skipped += 1
            continue

        band = GradeSalaryBand(
            internal_grade=band_data["grade"],
            location_id=singapore.id,
            currency=band_data["currency"],
            period=band_data["period"],
            min_salary=Decimal(str(band_data["min"])),
            max_salary=Decimal(str(band_data["max"])),
            is_active=True
        )
        session.add(band)
        print(f"  + Added: {band_data['grade']}: ${band_data['min']:,} - ${band_data['max']:,}")
        loaded += 1

    session.commit()
    return loaded, skipped


def main():
    """Main entry point"""
    print("=" * 70)
    print("SEED DATA LOADER")
    print("=" * 70)

    session = get_session()

    try:
        # Load locations
        print("\n1. Loading Locations...")
        loc_loaded, loc_skipped = load_locations(session)
        print(f"   → Loaded: {loc_loaded}, Skipped: {loc_skipped}")

        # Load currency rates
        print("\n2. Loading Currency Exchange Rates...")
        rate_loaded, rate_skipped = load_currency_rates(session)
        print(f"   → Loaded: {rate_loaded}, Skipped: {rate_skipped}")

        # Load salary bands
        print("\n3. Loading Salary Bands...")
        band_loaded, band_skipped = load_salary_bands(session)
        print(f"   → Loaded: {band_loaded}, Skipped: {band_skipped}")

        print("\n" + "=" * 70)
        print(f"SEED DATA LOAD COMPLETE")
        print(f"Total loaded: {loc_loaded + rate_loaded + band_loaded}")
        print(f"Total skipped: {loc_skipped + rate_skipped + band_skipped}")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Error loading seed data: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
