-- DataFlow Schema Migration for Horme POV
-- Generated from: src/models/production_models.py
-- Purpose: Create all 21+ DataFlow model tables with proper structure

BEGIN;

-- Ensure dataflow schema exists
CREATE SCHEMA IF NOT EXISTS dataflow;

-- Drop existing incompatible tables (preserves data if needed)
-- Comment out to keep existing data
DROP TABLE IF EXISTS dataflow.product_enrichment CASCADE;
DROP TABLE IF EXISTS dataflow.product_suppliers CASCADE;
DROP TABLE IF EXISTS dataflow.quotations CASCADE;
DROP TABLE IF EXISTS dataflow.products CASCADE;
DROP TABLE IF EXISTS dataflow.suppliers CASCADE;

-- ============================================================================
-- CORE CATALOG MODELS
-- ============================================================================

-- Category Model
CREATE TABLE IF NOT EXISTS dataflow.category (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_category_slug ON dataflow.category(slug);
CREATE INDEX IF NOT EXISTS idx_category_active ON dataflow.category(is_active);

-- Brand Model
CREATE TABLE IF NOT EXISTS dataflow.brand (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT NULL,
    website_url TEXT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_brand_slug ON dataflow.brand(slug);
CREATE INDEX IF NOT EXISTS idx_brand_active ON dataflow.brand(is_active);

-- Supplier Model
CREATE TABLE IF NOT EXISTS dataflow.supplier (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    website TEXT NOT NULL,
    api_endpoint TEXT NULL,
    contact_email TEXT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    scraping_config JSONB NULL,
    last_scraped TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_supplier_active ON dataflow.supplier(is_active);
CREATE UNIQUE INDEX IF NOT EXISTS idx_supplier_website ON dataflow.supplier(website);

-- Product Model (main catalog)
CREATE TABLE IF NOT EXISTS dataflow.product (
    id SERIAL PRIMARY KEY,
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT NULL,
    category_id INTEGER NULL REFERENCES dataflow.category(id),
    brand_id INTEGER NULL REFERENCES dataflow.brand(id),
    supplier_id INTEGER NULL REFERENCES dataflow.supplier(id),
    status TEXT DEFAULT 'active' NOT NULL,
    is_published BOOLEAN DEFAULT true NOT NULL,
    availability TEXT DEFAULT 'in_stock' NOT NULL,
    currency TEXT DEFAULT 'USD' NOT NULL,
    base_price NUMERIC(12,2) NULL,
    catalogue_item_id INTEGER NULL,
    source_url TEXT NULL,
    images_url TEXT NULL,
    -- Enrichment fields
    enriched_description TEXT NULL,
    technical_specs JSONB NULL,
    supplier_info JSONB NULL,
    competitor_data JSONB NULL,
    enrichment_status TEXT DEFAULT 'pending' NOT NULL,
    enrichment_source TEXT NULL,
    last_enriched TIMESTAMP WITH TIME ZONE NULL,
    -- Import tracking
    import_metadata JSONB NULL,
    -- Enterprise features
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    version INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_product_sku ON dataflow.product(sku);
CREATE UNIQUE INDEX IF NOT EXISTS idx_product_slug ON dataflow.product(slug);
CREATE INDEX IF NOT EXISTS idx_product_category ON dataflow.product(category_id, status);
CREATE INDEX IF NOT EXISTS idx_product_brand ON dataflow.product(brand_id, status);
CREATE INDEX IF NOT EXISTS idx_product_supplier ON dataflow.product(supplier_id, status);
CREATE INDEX IF NOT EXISTS idx_product_status ON dataflow.product(status, is_published);
CREATE INDEX IF NOT EXISTS idx_product_enrichment ON dataflow.product(enrichment_status);
CREATE INDEX IF NOT EXISTS idx_product_fulltext ON dataflow.product USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));

-- ProductPricing Model
CREATE TABLE IF NOT EXISTS dataflow.productpricing (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES dataflow.product(id),
    price_type TEXT DEFAULT 'base' NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    currency TEXT DEFAULT 'USD' NOT NULL,
    effective_from TIMESTAMP WITH TIME ZONE NOT NULL,
    effective_to TIMESTAMP WITH TIME ZONE NULL,
    supplier_id INTEGER NULL REFERENCES dataflow.supplier(id),
    minimum_quantity INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pricing_product ON dataflow.productpricing(product_id, price_type);
CREATE INDEX IF NOT EXISTS idx_pricing_effective ON dataflow.productpricing(effective_from, effective_to);
CREATE INDEX IF NOT EXISTS idx_pricing_supplier ON dataflow.productpricing(supplier_id, product_id);

-- ProductSpecification Model
CREATE TABLE IF NOT EXISTS dataflow.productspecification (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES dataflow.product(id),
    spec_name TEXT NOT NULL,
    spec_value TEXT NOT NULL,
    spec_category TEXT NULL,
    unit TEXT NULL,
    is_searchable BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_spec_product ON dataflow.productspecification(product_id);
CREATE INDEX IF NOT EXISTS idx_spec_name_value ON dataflow.productspecification(spec_name, spec_value);
CREATE INDEX IF NOT EXISTS idx_spec_searchable ON dataflow.productspecification(is_searchable, spec_name);

-- ProductInventory Model
CREATE TABLE IF NOT EXISTS dataflow.productinventory (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES dataflow.product(id),
    supplier_id INTEGER NOT NULL REFERENCES dataflow.supplier(id),
    quantity_available INTEGER DEFAULT 0 NOT NULL,
    quantity_reserved INTEGER DEFAULT 0 NOT NULL,
    reorder_level INTEGER DEFAULT 10 NOT NULL,
    reorder_quantity INTEGER DEFAULT 100 NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL,
    warehouse_location TEXT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_inventory_product ON dataflow.productinventory(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_supplier ON dataflow.productinventory(supplier_id);
CREATE INDEX IF NOT EXISTS idx_inventory_reorder ON dataflow.productinventory(quantity_available, reorder_level);

-- ============================================================================
-- WORKFLOW & QUOTATION MODELS
-- ============================================================================

-- WorkRecommendation Model
CREATE TABLE IF NOT EXISTS dataflow.workrecommendation (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    priority TEXT DEFAULT 'medium' NOT NULL,
    status TEXT DEFAULT 'open' NOT NULL,
    estimated_hours INTEGER NULL,
    estimated_value NUMERIC(12,2) NULL,
    related_products JSONB NULL,
    client_requirements JSONB NULL,
    recommendation_source TEXT NOT NULL,
    confidence_score DOUBLE PRECISION NULL,
    assigned_to TEXT NULL,
    due_date TIMESTAMP WITH TIME ZONE NULL,
    version INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_workrec_status ON dataflow.workrecommendation(status, priority);
CREATE INDEX IF NOT EXISTS idx_workrec_category ON dataflow.workrecommendation(category, status);
CREATE INDEX IF NOT EXISTS idx_workrec_assigned ON dataflow.workrecommendation(assigned_to, status);
CREATE INDEX IF NOT EXISTS idx_workrec_due ON dataflow.workrecommendation(due_date, status);
CREATE INDEX IF NOT EXISTS idx_workrec_confidence ON dataflow.workrecommendation(confidence_score);

-- RFPDocument Model
CREATE TABLE IF NOT EXISTS dataflow.rfpdocument (
    id SERIAL PRIMARY KEY,
    document_name TEXT NOT NULL,
    document_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_type TEXT NOT NULL,
    upload_date TIMESTAMP WITH TIME ZONE NOT NULL,
    parsed_content TEXT NULL,
    parsed_requirements JSONB NULL,
    analysis_status TEXT DEFAULT 'pending' NOT NULL,
    analysis_results JSONB NULL,
    client_name TEXT NULL,
    project_value NUMERIC(12,2) NULL,
    deadline TIMESTAMP WITH TIME ZONE NULL,
    version INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rfp_status ON dataflow.rfpdocument(analysis_status);
CREATE INDEX IF NOT EXISTS idx_rfp_client ON dataflow.rfpdocument(client_name, upload_date);
CREATE INDEX IF NOT EXISTS idx_rfp_deadline ON dataflow.rfpdocument(deadline);
CREATE INDEX IF NOT EXISTS idx_rfp_value ON dataflow.rfpdocument(project_value);

-- Quotation Model
CREATE TABLE IF NOT EXISTS dataflow.quotation (
    id SERIAL PRIMARY KEY,
    rfp_id INTEGER NULL REFERENCES dataflow.rfpdocument(id),
    quotation_number TEXT NOT NULL,
    client_name TEXT NOT NULL,
    client_email TEXT NULL,
    project_title TEXT NOT NULL,
    total_amount NUMERIC(12,2) NOT NULL,
    currency TEXT DEFAULT 'USD' NOT NULL,
    status TEXT DEFAULT 'draft' NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    line_items JSONB NOT NULL,
    terms_conditions TEXT NULL,
    notes TEXT NULL,
    created_by TEXT NULL,
    sent_date TIMESTAMP WITH TIME ZONE NULL,
    response_date TIMESTAMP WITH TIME ZONE NULL,
    version INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_quotation_number ON dataflow.quotation(quotation_number);
CREATE INDEX IF NOT EXISTS idx_quotation_status ON dataflow.quotation(status, valid_until);
CREATE INDEX IF NOT EXISTS idx_quotation_client ON dataflow.quotation(client_name, created_at);
CREATE INDEX IF NOT EXISTS idx_quotation_rfp ON dataflow.quotation(rfp_id);
CREATE INDEX IF NOT EXISTS idx_quotation_amount ON dataflow.quotation(total_amount, status);

-- QuotationItem Model
CREATE TABLE IF NOT EXISTS dataflow.quotationitem (
    id SERIAL PRIMARY KEY,
    quotation_id INTEGER NOT NULL REFERENCES dataflow.quotation(id),
    product_id INTEGER NULL REFERENCES dataflow.product(id),
    item_description TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,
    line_total NUMERIC(12,2) NOT NULL,
    item_category TEXT NULL,
    supplier_id INTEGER NULL REFERENCES dataflow.supplier(id),
    delivery_days INTEGER NULL,
    notes TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quotitem_quotation ON dataflow.quotationitem(quotation_id);
CREATE INDEX IF NOT EXISTS idx_quotitem_product ON dataflow.quotationitem(product_id);
CREATE INDEX IF NOT EXISTS idx_quotitem_supplier ON dataflow.quotationitem(supplier_id);

-- Customer Model
CREATE TABLE IF NOT EXISTS dataflow.customer (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    company_name TEXT NULL,
    email TEXT NOT NULL,
    phone TEXT NULL,
    address TEXT NULL,
    industry TEXT NULL,
    customer_type TEXT DEFAULT 'prospect' NOT NULL,
    credit_limit NUMERIC(12,2) NULL,
    payment_terms TEXT DEFAULT 'net_30' NOT NULL,
    preferred_contact TEXT DEFAULT 'email' NOT NULL,
    notes TEXT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_customer_email ON dataflow.customer(email);
CREATE INDEX IF NOT EXISTS idx_customer_company ON dataflow.customer(company_name);
CREATE INDEX IF NOT EXISTS idx_customer_type ON dataflow.customer(customer_type);
CREATE INDEX IF NOT EXISTS idx_customer_industry ON dataflow.customer(industry);

-- ActivityLog Model
CREATE TABLE IF NOT EXISTS dataflow.activitylog (
    id SERIAL PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    user_id TEXT NULL,
    details JSONB NULL,
    ip_address TEXT NULL,
    user_agent TEXT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_activity_entity ON dataflow.activitylog(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_activity_user ON dataflow.activitylog(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON dataflow.activitylog(timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_action ON dataflow.activitylog(action, entity_type);

-- ============================================================================
-- SAFETY & COMPLIANCE MODELS
-- ============================================================================

-- OSHAStandard Model
CREATE TABLE IF NOT EXISTS dataflow.oshastandard (
    id SERIAL PRIMARY KEY,
    cfr TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT NOT NULL,
    applies_to JSONB DEFAULT '[]'::jsonb NOT NULL,
    required_ppe JSONB DEFAULT '[]'::jsonb NOT NULL,
    mandatory BOOLEAN DEFAULT true NOT NULL,
    risk_level TEXT DEFAULT 'medium' NOT NULL,
    penalties TEXT NULL,
    legal_reference_url TEXT NOT NULL,
    version INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_osha_cfr ON dataflow.oshastandard(cfr);
CREATE INDEX IF NOT EXISTS idx_osha_risk_level ON dataflow.oshastandard(risk_level);
CREATE INDEX IF NOT EXISTS idx_osha_applies_to ON dataflow.oshastandard USING gin(applies_to);

-- ANSIStandard Model
CREATE TABLE IF NOT EXISTS dataflow.ansistandard (
    id SERIAL PRIMARY KEY,
    standard TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    standard_type TEXT NOT NULL,
    specifications JSONB DEFAULT '{}'::jsonb NOT NULL,
    markings JSONB DEFAULT '{}'::jsonb NOT NULL,
    test_requirements JSONB DEFAULT '{}'::jsonb NOT NULL,
    product_types JSONB DEFAULT '[]'::jsonb NOT NULL,
    reference_url TEXT NULL,
    industries JSONB DEFAULT '[]'::jsonb NOT NULL,
    version INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_ansi_standard ON dataflow.ansistandard(standard);
CREATE INDEX IF NOT EXISTS idx_ansi_type ON dataflow.ansistandard(standard_type);
CREATE INDEX IF NOT EXISTS idx_ansi_product_types ON dataflow.ansistandard USING gin(product_types);

-- ToolRiskClassification Model
CREATE TABLE IF NOT EXISTS dataflow.toolriskclassification (
    id SERIAL PRIMARY KEY,
    tool_name TEXT NOT NULL,
    category TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    hazards JSONB NOT NULL,
    osha_standards JSONB DEFAULT '[]'::jsonb NOT NULL,
    mandatory_ppe JSONB NOT NULL,
    recommended_ppe JSONB DEFAULT '[]'::jsonb NOT NULL,
    training_required BOOLEAN DEFAULT false NOT NULL,
    certification_required BOOLEAN DEFAULT false NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_tool_name ON dataflow.toolriskclassification(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_category ON dataflow.toolriskclassification(category);
CREATE INDEX IF NOT EXISTS idx_tool_risk_level ON dataflow.toolriskclassification(risk_level);
CREATE INDEX IF NOT EXISTS idx_tool_hazards ON dataflow.toolriskclassification USING gin(hazards);

-- TaskHazardMapping Model
CREATE TABLE IF NOT EXISTS dataflow.taskhazardmapping (
    id SERIAL PRIMARY KEY,
    task_id TEXT NOT NULL,
    task_name TEXT NOT NULL,
    hazards JSONB NOT NULL,
    risk_level TEXT NOT NULL,
    osha_standards JSONB DEFAULT '[]'::jsonb NOT NULL,
    mandatory_ppe JSONB NOT NULL,
    recommended_ppe JSONB DEFAULT '[]'::jsonb NOT NULL,
    safety_notes TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_task_id ON dataflow.taskhazardmapping(task_id);
CREATE INDEX IF NOT EXISTS idx_task_risk_level ON dataflow.taskhazardmapping(risk_level);
CREATE INDEX IF NOT EXISTS idx_task_hazards ON dataflow.taskhazardmapping USING gin(hazards);

-- ANSIEquipmentSpecification Model
CREATE TABLE IF NOT EXISTS dataflow.ansiequipmentspecification (
    id SERIAL PRIMARY KEY,
    equipment_type TEXT NOT NULL,
    ansi_standard TEXT NOT NULL,
    required_marking TEXT NULL,
    protection_level TEXT NOT NULL,
    specifications JSONB DEFAULT '{}'::jsonb NOT NULL,
    suitable_for JSONB DEFAULT '[]'::jsonb NOT NULL,
    not_suitable_for JSONB DEFAULT '[]'::jsonb NOT NULL,
    test_specifications JSONB DEFAULT '{}'::jsonb NOT NULL,
    notes TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_equipment_type ON dataflow.ansiequipmentspecification(equipment_type);
CREATE INDEX IF NOT EXISTS idx_equipment_standard ON dataflow.ansiequipmentspecification(ansi_standard);
CREATE INDEX IF NOT EXISTS idx_equipment_protection ON dataflow.ansiequipmentspecification(protection_level);

-- ============================================================================
-- PRODUCT CLASSIFICATION MODELS
-- ============================================================================

-- UNSPSCCode Model
CREATE TABLE IF NOT EXISTS dataflow.unspsccode (
    id SERIAL PRIMARY KEY,
    code TEXT NOT NULL,
    segment TEXT NOT NULL,
    family TEXT NOT NULL,
    class_ TEXT NOT NULL,
    commodity TEXT NOT NULL,
    title TEXT NOT NULL,
    definition TEXT NULL,
    level INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_unspsc_code ON dataflow.unspsccode(code);
CREATE INDEX IF NOT EXISTS idx_unspsc_level ON dataflow.unspsccode(level);
CREATE INDEX IF NOT EXISTS idx_unspsc_title ON dataflow.unspsccode USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_unspsc_segment ON dataflow.unspsccode(segment);
CREATE INDEX IF NOT EXISTS idx_unspsc_family ON dataflow.unspsccode(family);

-- ETIMClass Model
CREATE TABLE IF NOT EXISTS dataflow.etimclass (
    id SERIAL PRIMARY KEY,
    class_code TEXT NOT NULL,
    version TEXT NOT NULL,
    description_en TEXT NOT NULL,
    description_de TEXT NULL,
    description_fr TEXT NULL,
    description_nl TEXT NULL,
    parent_class TEXT NULL,
    features JSONB NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_etim_class_code ON dataflow.etimclass(class_code);
CREATE INDEX IF NOT EXISTS idx_etim_version ON dataflow.etimclass(version);
CREATE INDEX IF NOT EXISTS idx_etim_parent ON dataflow.etimclass(parent_class);
CREATE INDEX IF NOT EXISTS idx_etim_description_en ON dataflow.etimclass USING gin(to_tsvector('english', description_en));
CREATE INDEX IF NOT EXISTS idx_etim_features ON dataflow.etimclass USING gin(features);

-- ProductClassification Model
CREATE TABLE IF NOT EXISTS dataflow.productclassification (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES dataflow.product(id),
    unspsc_code TEXT NULL,
    etim_class TEXT NULL,
    confidence NUMERIC(3,2) NOT NULL,
    classification_method TEXT NOT NULL,
    classified_at TIMESTAMP WITH TIME ZONE NOT NULL,
    classified_by TEXT NULL,
    notes TEXT NULL,
    CONSTRAINT at_least_one_classification CHECK (unspsc_code IS NOT NULL OR etim_class IS NOT NULL),
    CONSTRAINT confidence_range CHECK (confidence >= 0 AND confidence <= 1)
);

CREATE INDEX IF NOT EXISTS idx_product_classifications_product ON dataflow.productclassification(product_id);
CREATE INDEX IF NOT EXISTS idx_product_classifications_unspsc ON dataflow.productclassification(unspsc_code);
CREATE INDEX IF NOT EXISTS idx_product_classifications_etim ON dataflow.productclassification(etim_class);
CREATE INDEX IF NOT EXISTS idx_product_classifications_method ON dataflow.productclassification(classification_method);
CREATE INDEX IF NOT EXISTS idx_product_classifications_confidence ON dataflow.productclassification(confidence);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================================

CREATE OR REPLACE FUNCTION dataflow.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to all tables with updated_at
DROP TRIGGER IF EXISTS update_category_updated_at ON dataflow.category;
CREATE TRIGGER update_category_updated_at BEFORE UPDATE ON dataflow.category FOR EACH ROW EXECUTE FUNCTION dataflow.update_updated_at_column();

DROP TRIGGER IF EXISTS update_brand_updated_at ON dataflow.brand;
CREATE TRIGGER update_brand_updated_at BEFORE UPDATE ON dataflow.brand FOR EACH ROW EXECUTE FUNCTION dataflow.update_updated_at_column();

DROP TRIGGER IF EXISTS update_supplier_updated_at ON dataflow.supplier;
CREATE TRIGGER update_supplier_updated_at BEFORE UPDATE ON dataflow.supplier FOR EACH ROW EXECUTE FUNCTION dataflow.update_updated_at_column();

DROP TRIGGER IF EXISTS update_product_updated_at ON dataflow.product;
CREATE TRIGGER update_product_updated_at BEFORE UPDATE ON dataflow.product FOR EACH ROW EXECUTE FUNCTION dataflow.update_updated_at_column();

DROP TRIGGER IF EXISTS update_workrecommendation_updated_at ON dataflow.workrecommendation;
CREATE TRIGGER update_workrecommendation_updated_at BEFORE UPDATE ON dataflow.workrecommendation FOR EACH ROW EXECUTE FUNCTION dataflow.update_updated_at_column();

DROP TRIGGER IF EXISTS update_rfpdocument_updated_at ON dataflow.rfpdocument;
CREATE TRIGGER update_rfpdocument_updated_at BEFORE UPDATE ON dataflow.rfpdocument FOR EACH ROW EXECUTE FUNCTION dataflow.update_updated_at_column();

DROP TRIGGER IF EXISTS update_quotation_updated_at ON dataflow.quotation;
CREATE TRIGGER update_quotation_updated_at BEFORE UPDATE ON dataflow.quotation FOR EACH ROW EXECUTE FUNCTION dataflow.update_updated_at_column();

DROP TRIGGER IF EXISTS update_customer_updated_at ON dataflow.customer;
CREATE TRIGGER update_customer_updated_at BEFORE UPDATE ON dataflow.customer FOR EACH ROW EXECUTE FUNCTION dataflow.update_updated_at_column();

DROP TRIGGER IF EXISTS update_oshastandard_updated_at ON dataflow.oshastandard;
CREATE TRIGGER update_oshastandard_updated_at BEFORE UPDATE ON dataflow.oshastandard FOR EACH ROW EXECUTE FUNCTION dataflow.update_updated_at_column();

DROP TRIGGER IF EXISTS update_ansistandard_updated_at ON dataflow.ansistandard;
CREATE TRIGGER update_ansistandard_updated_at BEFORE UPDATE ON dataflow.ansistandard FOR EACH ROW EXECUTE FUNCTION dataflow.update_updated_at_column();

DROP TRIGGER IF EXISTS update_toolriskclassification_updated_at ON dataflow.toolriskclassification;
CREATE TRIGGER update_toolriskclassification_updated_at BEFORE UPDATE ON dataflow.toolriskclassification FOR EACH ROW EXECUTE FUNCTION dataflow.update_updated_at_column();

DROP TRIGGER IF EXISTS update_taskhazardmapping_updated_at ON dataflow.taskhazardmapping;
CREATE TRIGGER update_taskhazardmapping_updated_at BEFORE UPDATE ON dataflow.taskhazardmapping FOR EACH ROW EXECUTE FUNCTION dataflow.update_updated_at_column();

DROP TRIGGER IF EXISTS update_ansiequipmentspecification_updated_at ON dataflow.ansiequipmentspecification;
CREATE TRIGGER update_ansiequipmentspecification_updated_at BEFORE UPDATE ON dataflow.ansiequipmentspecification FOR EACH ROW EXECUTE FUNCTION dataflow.update_updated_at_column();

DROP TRIGGER IF EXISTS update_unspsccode_updated_at ON dataflow.unspsccode;
CREATE TRIGGER update_unspsccode_updated_at BEFORE UPDATE ON dataflow.unspsccode FOR EACH ROW EXECUTE FUNCTION dataflow.update_updated_at_column();

DROP TRIGGER IF EXISTS update_etimclass_updated_at ON dataflow.etimclass;
CREATE TRIGGER update_etimclass_updated_at BEFORE UPDATE ON dataflow.etimclass FOR EACH ROW EXECUTE FUNCTION dataflow.update_updated_at_column();

COMMIT;

-- ============================================================================
-- MIGRATION SUMMARY
-- ============================================================================
-- Total Models: 21
-- Tables Created: 21
-- Indexes Created: 70+
-- Triggers Created: 15
-- Enterprise Features: Soft delete, Versioning, Audit logging
-- Status: Complete
-- ============================================================================
