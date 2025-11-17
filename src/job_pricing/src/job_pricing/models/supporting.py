"""
Supporting Tables Models

Stores locations, location indexes, currency exchange rates, and audit logs.
Corresponds to: locations, location_index, currency_exchange_rates, audit_log tables
"""

from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    BigInteger,
    Numeric,
    Date,
    DateTime,
    Boolean,
    Index,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, INET

from .base import Base


class Location(Base):
    """
    Location Model

    Stores global location database for job market data.
    Used for location-based job pricing and market analysis.

    Attributes:
        id: Unique identifier (SERIAL)
        country_code: ISO 3166-1 alpha-2 country code
        country_name: Country name
        city: City name
        region: Geographic region/state
        latitude: Geographic latitude
        longitude: Geographic longitude
        timezone: IANA timezone identifier
        is_active: Whether location is active
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "locations"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier"
    )

    # Location Data
    country_code = Column(
        String(2),
        nullable=False,
        comment="ISO 3166-1 alpha-2 country code"
    )

    country_name = Column(
        String(100),
        nullable=False,
        comment="Country name"
    )

    city = Column(
        String(100),
        nullable=False,
        comment="City name"
    )

    region = Column(
        String(100),
        nullable=True,
        comment="Geographic region/state"
    )

    # Geographic Coordinates
    latitude = Column(
        Numeric(10, 7),
        nullable=True,
        comment="Latitude coordinate"
    )

    longitude = Column(
        Numeric(10, 7),
        nullable=True,
        comment="Longitude coordinate"
    )

    # Timezone
    timezone = Column(
        String(50),
        nullable=True,
        comment="IANA timezone identifier"
    )

    # Status
    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
        comment="Whether location is active"
    )

    # Audit Fields
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Creation timestamp"
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Last update timestamp"
    )

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint("country_code", "city", name="uq_location"),
        Index("idx_locations_country", "country_code"),
        Index("idx_locations_city", "city"),
    )

    def __repr__(self) -> str:
        return f"<Location(id={self.id}, city='{self.city}', country='{self.country_code}')>"


class LocationIndex(Base):
    """
    Location Index Model

    Stores location-specific cost-of-living adjustments.
    Used for location-based salary adjustments.

    Attributes:
        id: Unique identifier (SERIAL)
        location_name: Location name (unique)
        cost_of_living_index: Cost of living index (Singapore CBD = 1.0)
        region: Geographic region
        postal_code_prefix: Postal code prefix
        effective_date: Effective date for this index
        last_updated: Last update timestamp
    """

    __tablename__ = "location_index"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier"
    )

    # Location
    location_name = Column(
        String(100),
        unique=True,
        nullable=False,
        comment="Location name (unique)"
    )

    # Cost of Living Index (Singapore CBD = 1.0)
    cost_of_living_index = Column(
        Numeric(5, 2),
        nullable=False,
        comment="Cost of living index (Singapore CBD = 1.0)"
    )

    # Geographic Details
    region = Column(
        String(50),
        nullable=True,
        comment="Geographic region (e.g., 'Central', 'East', 'West')"
    )

    postal_code_prefix = Column(
        String(10),
        nullable=True,
        comment="Postal code prefix for this location"
    )

    # Metadata
    effective_date = Column(
        Date,
        nullable=False,
        comment="Effective date for this cost of living index"
    )

    last_updated = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Last update timestamp"
    )

    # Constraints and Indexes
    __table_args__ = (
        Index("idx_location_name", "location_name"),
    )

    def __repr__(self) -> str:
        return f"<LocationIndex(id={self.id}, location='{self.location_name}', index={self.cost_of_living_index})>"


class CurrencyExchangeRate(Base):
    """
    Currency Exchange Rate Model

    Stores historical exchange rates for currency conversion.
    Used to normalize salaries to a common currency (SGD).

    Attributes:
        id: Unique identifier (SERIAL)
        from_currency: Source currency code
        to_currency: Target currency code
        exchange_rate: Exchange rate
        effective_date: Effective date for this exchange rate
        source: Data source (e.g., 'MAS', 'XE', 'ECB')
        created_at: Creation timestamp
    """

    __tablename__ = "currency_exchange_rates"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier"
    )

    # Currency Pair
    from_currency = Column(
        String(3),
        nullable=False,
        comment="Source currency code (ISO 4217)"
    )

    to_currency = Column(
        String(3),
        nullable=False,
        comment="Target currency code (ISO 4217)"
    )

    # Exchange Rate
    exchange_rate = Column(
        Numeric(15, 6),
        nullable=False,
        comment="Exchange rate (1 FROM = X TO)"
    )

    # Effective Date
    effective_date = Column(
        Date,
        nullable=False,
        comment="Effective date for this exchange rate"
    )

    # Source
    source = Column(
        String(100),
        nullable=True,
        comment="Data source (e.g., 'MAS', 'XE', 'ECB')"
    )

    # Audit
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Timestamp when rate was created"
    )

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint("from_currency", "to_currency", "effective_date", name="uq_exchange_rate"),
        Index("idx_currency_from_to", "from_currency", "to_currency"),
    )

    def __repr__(self) -> str:
        return f"<CurrencyExchangeRate(id={self.id}, {self.from_currency}->{self.to_currency}, rate={self.exchange_rate})>"


class AuditLog(Base):
    """
    Audit Log Model

    Comprehensive audit trail for all system actions.
    Tracks who did what, when, and what changed.

    Attributes:
        id: Unique identifier (BIGSERIAL)
        action_type: Action type (e.g., 'job_request', 'pricing_result')
        entity_type: Entity type (e.g., 'JobPricingRequest', 'MercerJobMapping')
        entity_id: Entity ID (as string for flexibility)
        performed_by: User who performed the action
        ip_address: IP address of the user
        user_agent: User agent string
        action_description: Human-readable description
        old_values: Old values (JSONB)
        new_values: New values (JSONB)
        performed_at: Timestamp when action was performed
    """

    __tablename__ = "audit_log"

    # Primary Key (BIGSERIAL for high-volume logging)
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier"
    )

    # Action Details
    action_type = Column(
        String(50),
        nullable=False,
        comment="Action type (e.g., 'job_request', 'pricing_result', 'data_update')"
    )

    entity_type = Column(
        String(50),
        nullable=False,
        comment="Entity type (e.g., 'JobPricingRequest', 'MercerJobMapping')"
    )

    entity_id = Column(
        String(255),
        nullable=True,
        comment="Entity ID (as string for flexibility)"
    )

    # User Context
    performed_by = Column(
        String(100),
        nullable=False,
        comment="User who performed the action"
    )

    ip_address = Column(
        INET,
        nullable=True,
        comment="IP address of the user"
    )

    user_agent = Column(
        Text,
        nullable=True,
        comment="User agent string"
    )

    # Change Details
    action_description = Column(
        Text,
        nullable=True,
        comment="Human-readable description of the action"
    )

    old_values = Column(
        JSONB,
        nullable=True,
        comment="Old values before the change (JSONB)"
    )

    new_values = Column(
        JSONB,
        nullable=True,
        comment="New values after the change (JSONB)"
    )

    # Temporal
    performed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        comment="Timestamp when action was performed"
    )

    # Constraints and Indexes
    __table_args__ = (
        Index("idx_audit_action_type", "action_type"),
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_user", "performed_by"),
        Index("idx_audit_time", "performed_at", postgresql_ops={"performed_at": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action_type}', entity='{self.entity_type}', by='{self.performed_by}')>"
