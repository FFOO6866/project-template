"""
Comprehensive Data Enrichment Pipeline for Horme Product Knowledge Base.

This pipeline orchestrates the entire data enrichment process using Kailash WorkflowBuilder:
1. Data ingestion from multiple sources (Excel, scraped data, suppliers)
2. Product matching using SKU and fuzzy matching
3. Multi-source data merging with conflict resolution
4. Data quality scoring and validation
5. Bulk database updates using DataFlow operations
6. Progress tracking and resumable pipeline execution
7. Comprehensive enrichment reporting

Architecture:
- Built on Kailash Core SDK WorkflowBuilder for reliability
- Uses DataFlow models for database operations
- Implements enterprise-grade error handling and recovery
- Supports multi-tenant and audit logging
- Generates detailed progress and quality reports
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, field, asdict
import pandas as pd
from fuzzywuzzy import fuzz, process

# Kailash SDK imports
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Import DataFlow models
from horme_dataflow_models import (
    db, Product, Category, Brand, Supplier, ProductImage, 
    ProductSpecification, ProductSupplier, ScrapingJob, ProductAnalytics
)

# Import scraper models
from horme_scraper.models import ProductData, ScrapingSession


@dataclass
class EnrichmentConfig:
    """Configuration for the data enrichment pipeline."""
    
    # Source file paths
    excel_file_path: str = "docs/reference/ProductData (Top 3 Cats).xlsx"
    scraped_data_directory: str = "sample_output"
    supplier_data_directory: str = "supplier_data"
    
    # Matching thresholds
    sku_exact_match_threshold: float = 1.0
    name_fuzzy_match_threshold: float = 85.0
    brand_fuzzy_match_threshold: float = 80.0
    model_fuzzy_match_threshold: float = 90.0
    
    # Conflict resolution priorities (higher number = higher priority)
    source_priorities: Dict[str, int] = field(default_factory=lambda: {
        "excel": 100,        # Highest priority - master data
        "supplier": 80,      # High priority - authoritative supplier data
        "scraped": 60,       # Medium priority - web scraped data
        "default": 40        # Low priority - default values
    })
    
    # Quality scoring weights
    quality_weights: Dict[str, float] = field(default_factory=lambda: {
        "sku_completeness": 0.20,
        "name_completeness": 0.15,
        "description_completeness": 0.10,
        "price_completeness": 0.15,
        "specifications_completeness": 0.15,
        "images_completeness": 0.10,
        "brand_completeness": 0.05,
        "category_completeness": 0.05,
        "data_freshness": 0.05
    })
    
    # Batch processing
    batch_size: int = 100
    max_concurrent_operations: int = 10
    
    # Pipeline settings
    enable_resume: bool = True
    checkpoint_interval: int = 50
    generate_reports: bool = True
    
    # Output settings
    output_directory: str = "enrichment_output"
    report_formats: List[str] = field(default_factory=lambda: ["json", "html", "csv"])


@dataclass
class MatchResult:
    """Result of product matching operation."""
    
    source_product: Dict[str, Any]
    matched_products: List[Dict[str, Any]] = field(default_factory=list)
    match_confidence: float = 0.0
    match_method: str = "none"  # exact_sku, fuzzy_name, fuzzy_brand_model, no_match
    conflicts: List[str] = field(default_factory=list)
    quality_score: float = 0.0


@dataclass
class EnrichmentProgress:
    """Track pipeline progress and statistics."""
    
    pipeline_id: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    # Input statistics
    excel_products_loaded: int = 0
    scraped_products_loaded: int = 0
    supplier_products_loaded: int = 0
    total_input_products: int = 0
    
    # Matching statistics
    exact_sku_matches: int = 0
    fuzzy_name_matches: int = 0
    fuzzy_brand_model_matches: int = 0
    no_matches: int = 0
    
    # Enrichment statistics
    products_enriched: int = 0
    products_created: int = 0
    products_updated: int = 0
    conflicts_resolved: int = 0
    
    # Quality statistics
    avg_quality_score_before: float = 0.0
    avg_quality_score_after: float = 0.0
    quality_improvements: int = 0
    
    # Error tracking
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Checkpoint tracking
    last_checkpoint: int = 0
    checkpoints_saved: int = 0
    
    def add_error(self, error: str) -> None:
        """Add an error to the progress tracking."""
        self.errors.append(f"{datetime.now().isoformat()}: {error}")
    
    def add_warning(self, warning: str) -> None:
        """Add a warning to the progress tracking."""
        self.warnings.append(f"{datetime.now().isoformat()}: {warning}")
    
    def finish(self) -> None:
        """Mark the pipeline as finished."""
        self.end_time = datetime.now()
    
    def get_duration(self) -> Optional[float]:
        """Get pipeline duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert progress to dictionary for serialization."""
        return asdict(self)


class DataEnrichmentPipeline:
    """
    Comprehensive data enrichment pipeline using Kailash WorkflowBuilder.
    
    This pipeline orchestrates the entire data enrichment process with:
    - Multi-source data ingestion
    - Intelligent product matching
    - Conflict resolution
    - Quality scoring
    - Bulk database operations
    - Progress tracking and resumability
    """
    
    def __init__(self, config: EnrichmentConfig):
        self.config = config
        self.progress = EnrichmentProgress(pipeline_id=str(uuid.uuid4()))
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Initialize Kailash components
        self.workflow = WorkflowBuilder()
        self.runtime = LocalRuntime()
        
        # Data storage
        self.excel_data: List[Dict[str, Any]] = []
        self.scraped_data: List[Dict[str, Any]] = []
        self.supplier_data: List[Dict[str, Any]] = []
        self.enriched_products: List[Dict[str, Any]] = []
        
        # Matching and quality data
        self.match_results: List[MatchResult] = []
        self.quality_scores: Dict[str, float] = {}
        
        # Create output directory
        os.makedirs(self.config.output_directory, exist_ok=True)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging for the pipeline."""
        logger = logging.getLogger(f"enrichment_pipeline_{self.progress.pipeline_id}")
        logger.setLevel(logging.INFO)
        
        # Create log file path
        log_file = os.path.join(self.config.output_directory, f"pipeline_{self.progress.pipeline_id[:8]}.log")
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def run_complete_pipeline(self) -> EnrichmentProgress:
        """
        Execute the complete data enrichment pipeline.
        
        Returns:
            EnrichmentProgress: Complete pipeline execution results
        """
        try:
            self.logger.info(f"Starting data enrichment pipeline {self.progress.pipeline_id}")
            
            # Build and execute the main workflow
            self._build_enrichment_workflow()
            results, run_id = self.runtime.execute(self.workflow.build())
            
            self.logger.info(f"Pipeline workflow completed with run_id: {run_id}")
            
            # Generate final reports
            if self.config.generate_reports:
                self._generate_reports()
            
            self.progress.finish()
            self.logger.info(f"Pipeline completed in {self.progress.get_duration():.2f} seconds")
            
            return self.progress
            
        except Exception as e:
            self.progress.add_error(f"Pipeline failed: {str(e)}")
            self.logger.error(f"Pipeline failed: {str(e)}")
            self.progress.finish()
            raise
    
    def _build_enrichment_workflow(self) -> None:
        """Build the complete enrichment workflow using Kailash WorkflowBuilder."""
        
        # Stage 1: Data Ingestion
        self.workflow.add_node("PythonCodeNode", "load_excel_data", {
            "code": self._generate_excel_loader_code(),
            "requirements": ["pandas", "openpyxl"]
        })
        
        self.workflow.add_node("PythonCodeNode", "load_scraped_data", {
            "code": self._generate_scraped_loader_code(),
            "requirements": ["json", "glob"]
        })
        
        self.workflow.add_node("PythonCodeNode", "load_supplier_data", {
            "code": self._generate_supplier_loader_code(),
            "requirements": ["json", "glob"]
        })
        
        # Stage 2: Data Matching
        self.workflow.add_node("PythonCodeNode", "match_products", {
            "code": self._generate_matching_code(),
            "requirements": ["fuzzywuzzy", "python-Levenshtein"]
        })
        
        # Stage 3: Conflict Resolution
        self.workflow.add_node("PythonCodeNode", "resolve_conflicts", {
            "code": self._generate_conflict_resolution_code()
        })
        
        # Stage 4: Quality Scoring
        self.workflow.add_node("PythonCodeNode", "calculate_quality_scores", {
            "code": self._generate_quality_scoring_code()
        })
        
        # Stage 5: Database Operations
        self.workflow.add_node("PythonCodeNode", "prepare_bulk_operations", {
            "code": self._generate_bulk_operations_prep_code()
        })
        
        # Stage 6: Execute Bulk Updates
        self.workflow.add_node("ProductBulkUpsertNode", "bulk_upsert_products", {
            "batch_size": self.config.batch_size,
            "conflict_resolution": "update",
            "return_records": True
        })
        
        # Stage 7: Progress Tracking
        self.workflow.add_node("PythonCodeNode", "update_progress", {
            "code": self._generate_progress_update_code()
        })
        
        # Connect the workflow stages
        self.workflow.connect("load_excel_data", "match_products")
        self.workflow.connect("load_scraped_data", "match_products")
        self.workflow.connect("load_supplier_data", "match_products")
        self.workflow.connect("match_products", "resolve_conflicts")
        self.workflow.connect("resolve_conflicts", "calculate_quality_scores")
        self.workflow.connect("calculate_quality_scores", "prepare_bulk_operations")
        self.workflow.connect("prepare_bulk_operations", "bulk_upsert_products")
        self.workflow.connect("bulk_upsert_products", "update_progress")
    
    def _generate_excel_loader_code(self) -> str:
        """Generate Python code for loading Excel data."""
        return f"""
import pandas as pd
import json
from pathlib import Path

# Load Excel data
excel_path = Path("{self.config.excel_file_path}")
if excel_path.exists():
    df = pd.read_excel(excel_path)
    # Convert to list of dictionaries
    excel_products = df.to_dict('records')
    
    # Standardize column names
    for product in excel_products:
        # Create standardized product dictionary
        standardized = {{
            'source': 'excel',
            'sku': str(product.get('SKU', product.get('sku', ''))),
            'name': str(product.get('Product Name', product.get('name', ''))),
            'description': str(product.get('Description', product.get('description', ''))),
            'price': product.get('Price', product.get('price')),
            'brand': str(product.get('Brand', product.get('brand', ''))),
            'category': str(product.get('Category', product.get('category', ''))),
            'model_number': str(product.get('Model', product.get('model_number', ''))),
            'specifications': product.get('Specifications', {{}}) if isinstance(product.get('Specifications', ''), dict) else {{}},
            'original_data': product
        }}
        excel_products[excel_products.index(product)] = standardized
    
    print(f"Loaded {{len(excel_products)}} products from Excel")
    result = excel_products
else:
    print(f"Excel file not found: {{excel_path}}")
    result = []
"""
    
    def _generate_scraped_loader_code(self) -> str:
        """Generate Python code for loading scraped data."""
        return f"""
import json
import glob
from pathlib import Path

scraped_products = []
scraped_dir = Path("{self.config.scraped_data_directory}")

if scraped_dir.exists():
    # Load all JSON files from scraped data directory
    json_files = glob.glob(str(scraped_dir / "*.json"))
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Handle different JSON structures
                if isinstance(data, list):
                    products = data
                elif isinstance(data, dict) and 'products' in data:
                    products = data['products']
                else:
                    products = [data]
                
                # Standardize each product
                for product in products:
                    if isinstance(product, dict):
                        standardized = {{
                            'source': 'scraped',
                            'sku': str(product.get('sku', '')),
                            'name': str(product.get('name', '')),
                            'description': str(product.get('description', '')),
                            'price': product.get('price'),
                            'brand': str(product.get('brand', '')),
                            'category': str(product.get('category', product.get('categories', [{}])[0] if product.get('categories') else '')),
                            'model_number': str(product.get('model_number', '')),
                            'specifications': product.get('specifications', {{}}) if isinstance(product.get('specifications'), dict) else {{}},
                            'images': product.get('images', []),
                            'url': product.get('url', ''),
                            'scraped_at': product.get('scraped_at'),
                            'original_data': product
                        }}
                        scraped_products.append(standardized)
        except Exception as e:
            print(f"Error loading {{json_file}}: {{e}}")

print(f"Loaded {{len(scraped_products)}} products from scraped data")
result = scraped_products
"""
    
    def _generate_supplier_loader_code(self) -> str:
        """Generate Python code for loading supplier data."""
        return f"""
import json
import glob
from pathlib import Path

supplier_products = []
supplier_dir = Path("{self.config.supplier_data_directory}")

if supplier_dir.exists():
    # Load all JSON files from supplier data directory
    json_files = glob.glob(str(supplier_dir / "*.json"))
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Handle different JSON structures
                if isinstance(data, list):
                    products = data
                elif isinstance(data, dict) and 'products' in data:
                    products = data['products']
                else:
                    products = [data]
                
                # Standardize each product
                for product in products:
                    if isinstance(product, dict):
                        # Extract supplier info from filename
                        supplier_name = Path(json_file).stem
                        
                        standardized = {{
                            'source': 'supplier',
                            'supplier_name': supplier_name,
                            'sku': str(product.get('sku', product.get('supplier_sku', ''))),
                            'name': str(product.get('name', product.get('product_name', ''))),
                            'description': str(product.get('description', '')),
                            'price': product.get('price', product.get('supplier_price')),
                            'brand': str(product.get('brand', '')),
                            'category': str(product.get('category', '')),
                            'model_number': str(product.get('model_number', product.get('model', ''))),
                            'specifications': product.get('specifications', {{}}) if isinstance(product.get('specifications'), dict) else {{}},
                            'availability': product.get('availability', product.get('stock_status', '')),
                            'lead_time': product.get('lead_time', product.get('lead_time_days')),
                            'minimum_order_qty': product.get('minimum_order_qty', product.get('moq')),
                            'original_data': product
                        }}
                        supplier_products.append(standardized)
        except Exception as e:
            print(f"Error loading {{json_file}}: {{e}}")
else:
    print(f"Supplier data directory not found: {{supplier_dir}}")

print(f"Loaded {{len(supplier_products)}} products from supplier data")
result = supplier_products
"""
    
    def _generate_matching_code(self) -> str:
        """Generate Python code for product matching."""
        return f"""
from fuzzywuzzy import fuzz, process
from typing import Dict, List, Any, Tuple
import re

def clean_string_for_matching(s: str) -> str:
    \"\"\"Clean string for better matching.\"\"\"
    if not s:
        return ""
    # Remove extra whitespace, convert to lowercase
    cleaned = re.sub(r'\\s+', ' ', str(s).strip().lower())
    # Remove common words that don't help matching
    common_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
    words = cleaned.split()
    words = [w for w in words if w not in common_words]
    return ' '.join(words)

def find_best_sku_match(target_sku: str, products: List[Dict]) -> Tuple[Dict, float]:
    \"\"\"Find best SKU match.\"\"\"
    if not target_sku:
        return None, 0.0
    
    target_sku_clean = clean_string_for_matching(target_sku)
    best_match = None
    best_score = 0.0
    
    for product in products:
        product_sku = clean_string_for_matching(product.get('sku', ''))
        if product_sku:
            score = fuzz.ratio(target_sku_clean, product_sku)
            if score > best_score:
                best_score = score
                best_match = product
    
    return best_match, best_score

def find_best_name_match(target_name: str, products: List[Dict]) -> Tuple[Dict, float]:
    \"\"\"Find best product name match.\"\"\"
    if not target_name:
        return None, 0.0
    
    target_name_clean = clean_string_for_matching(target_name)
    best_match = None
    best_score = 0.0
    
    for product in products:
        product_name = clean_string_for_matching(product.get('name', ''))
        if product_name:
            score = fuzz.token_sort_ratio(target_name_clean, product_name)
            if score > best_score:
                best_score = score
                best_match = product
    
    return best_match, best_score

def find_best_brand_model_match(target_brand: str, target_model: str, products: List[Dict]) -> Tuple[Dict, float]:
    \"\"\"Find best brand + model match.\"\"\"
    if not target_brand or not target_model:
        return None, 0.0
    
    target_brand_clean = clean_string_for_matching(target_brand)
    target_model_clean = clean_string_for_matching(target_model)
    target_combined = f"{{target_brand_clean}} {{target_model_clean}}"
    
    best_match = None
    best_score = 0.0
    
    for product in products:
        product_brand = clean_string_for_matching(product.get('brand', ''))
        product_model = clean_string_for_matching(product.get('model_number', ''))
        
        if product_brand and product_model:
            product_combined = f"{{product_brand}} {{product_model}}"
            score = fuzz.token_sort_ratio(target_combined, product_combined)
            if score > best_score:
                best_score = score
                best_match = product
    
    return best_match, best_score

# Combine all data sources
all_products = []
if 'excel_products' in locals():
    all_products.extend(excel_products)
if 'scraped_products' in locals():
    all_products.extend(scraped_products)
if 'supplier_products' in locals():
    all_products.extend(supplier_products)

print(f"Total products to process: {{len(all_products)}}")

# Matching logic
match_results = []
thresholds = {{
    'sku_exact': {self.config.sku_exact_match_threshold},
    'name_fuzzy': {self.config.name_fuzzy_match_threshold},
    'brand_fuzzy': {self.config.brand_fuzzy_match_threshold},
    'model_fuzzy': {self.config.model_fuzzy_match_threshold}
}}

# Group products by source for matching
excel_products_only = [p for p in all_products if p.get('source') == 'excel']
scraped_products_only = [p for p in all_products if p.get('source') == 'scraped']
supplier_products_only = [p for p in all_products if p.get('source') == 'supplier']

# Match scraped and supplier products to Excel products (master data)
for source_products, source_name in [(scraped_products_only, 'scraped'), (supplier_products_only, 'supplier')]:
    for product in source_products:
        match_result = {{
            'source_product': product,
            'matched_products': [],
            'match_confidence': 0.0,
            'match_method': 'no_match',
            'conflicts': []
        }}
        
        # Try exact SKU match first
        if product.get('sku'):
            best_match, score = find_best_sku_match(product['sku'], excel_products_only)
            if best_match and score >= thresholds['sku_exact']:
                match_result['matched_products'].append(best_match)
                match_result['match_confidence'] = score / 100.0
                match_result['match_method'] = 'exact_sku'
        
        # Try fuzzy name match if no SKU match
        if not match_result['matched_products'] and product.get('name'):
            best_match, score = find_best_name_match(product['name'], excel_products_only)
            if best_match and score >= thresholds['name_fuzzy']:
                match_result['matched_products'].append(best_match)
                match_result['match_confidence'] = score / 100.0
                match_result['match_method'] = 'fuzzy_name'
        
        # Try brand + model match if no other matches
        if not match_result['matched_products'] and product.get('brand') and product.get('model_number'):
            best_match, score = find_best_brand_model_match(
                product['brand'], product['model_number'], excel_products_only
            )
            if best_match and score >= thresholds['model_fuzzy']:
                match_result['matched_products'].append(best_match)
                match_result['match_confidence'] = score / 100.0
                match_result['match_method'] = 'fuzzy_brand_model'
        
        match_results.append(match_result)

print(f"Completed matching. Found {{len([r for r in match_results if r['matched_products']])}} matches out of {{len(match_results)}} products")

# Count match types
exact_sku_matches = len([r for r in match_results if r['match_method'] == 'exact_sku'])
fuzzy_name_matches = len([r for r in match_results if r['match_method'] == 'fuzzy_name'])
fuzzy_brand_model_matches = len([r for r in match_results if r['match_method'] == 'fuzzy_brand_model'])
no_matches = len([r for r in match_results if r['match_method'] == 'no_match'])

print(f"Match statistics:")
print(f"  Exact SKU matches: {{exact_sku_matches}}")
print(f"  Fuzzy name matches: {{fuzzy_name_matches}}")
print(f"  Fuzzy brand+model matches: {{fuzzy_brand_model_matches}}")
print(f"  No matches: {{no_matches}}")

result = match_results
"""
    
    def _generate_conflict_resolution_code(self) -> str:
        """Generate Python code for conflict resolution."""
        return f"""
def resolve_field_conflict(field_name: str, values: Dict[str, Any]) -> Any:
    \"\"\"Resolve conflicts for a specific field based on source priority.\"\"\"
    priorities = {self.config.source_priorities}
    
    # Filter out None/empty values
    valid_values = {{source: value for source, value in values.items() 
                    if value is not None and value != '' and value != []}}
    
    if not valid_values:
        return None
    
    # Return value from highest priority source
    highest_priority = max(valid_values.keys(), key=lambda x: priorities.get(x, 0))
    return valid_values[highest_priority]

def merge_specifications(spec_dicts: List[Dict]) -> Dict:
    \"\"\"Merge specifications from multiple sources.\"\"\"
    merged = {{}}
    
    for spec_dict in spec_dicts:
        if isinstance(spec_dict, dict):
            for key, value in spec_dict.items():
                if key not in merged or value:  # Prefer non-empty values
                    merged[key] = value
    
    return merged

def merge_lists(lists: List[List]) -> List:
    \"\"\"Merge lists, removing duplicates while preserving order.\"\"\"
    merged = []
    seen = set()
    
    for lst in lists:
        if isinstance(lst, list):
            for item in lst:
                if item not in seen:
                    merged.append(item)
                    seen.add(item)
    
    return merged

# Process match results and resolve conflicts
enriched_products = []
conflicts_resolved = 0

for match_result in match_results:
    source_product = match_result['source_product']
    matched_products = match_result['matched_products']
    
    if matched_products:
        # Merge data from matched products
        excel_product = matched_products[0]  # Primary match from Excel
        
        # Collect all values for each field
        field_values = {{}}
        all_products_data = [excel_product, source_product]
        
        # Standard fields to merge
        standard_fields = ['sku', 'name', 'description', 'price', 'brand', 'category', 'model_number']
        
        for field in standard_fields:
            field_values[field] = {{}}
            for product in all_products_data:
                source = product.get('source', 'unknown')
                value = product.get(field)
                if value is not None and value != '':
                    field_values[field][source] = value
        
        # Resolve conflicts
        enriched_product = {{}}
        for field, values in field_values.items():
            if len(values) > 1:
                conflicts_resolved += 1
                match_result['conflicts'].append(f"{{field}}: {{values}}")
            
            enriched_product[field] = resolve_field_conflict(field, values)
        
        # Merge complex fields
        specifications_list = []
        images_list = []
        
        for product in all_products_data:
            if product.get('specifications'):
                specifications_list.append(product['specifications'])
            if product.get('images'):
                images_list.append(product['images'])
        
        enriched_product['specifications'] = merge_specifications(specifications_list)
        enriched_product['images'] = merge_lists(images_list)
        
        # Add metadata
        enriched_product['enrichment_metadata'] = {{
            'match_method': match_result['match_method'],
            'match_confidence': match_result['match_confidence'],
            'sources': [p.get('source') for p in all_products_data],
            'conflicts_resolved': len(match_result['conflicts']),
            'enriched_at': str(datetime.now())
        }}
        
        # Copy additional fields from source data
        for field in ['url', 'scraped_at', 'supplier_name', 'availability', 'lead_time', 'minimum_order_qty']:
            if source_product.get(field):
                enriched_product[field] = source_product[field]
        
        enriched_products.append(enriched_product)
    else:
        # No match found - add as new product
        new_product = source_product.copy()
        new_product['enrichment_metadata'] = {{
            'match_method': 'no_match',
            'match_confidence': 0.0,
            'sources': [source_product.get('source')],
            'conflicts_resolved': 0,
            'enriched_at': str(datetime.now())
        }}
        enriched_products.append(new_product)

print(f"Enriched {{len(enriched_products)}} products")
print(f"Resolved {{conflicts_resolved}} field conflicts")

result = enriched_products
"""
    
    def _generate_quality_scoring_code(self) -> str:
        """Generate Python code for quality scoring."""
        return f"""
def calculate_completeness_score(value, weight: float = 1.0) -> float:
    \"\"\"Calculate completeness score for a field.\"\"\"
    if value is None or value == '' or value == []:
        return 0.0
    elif isinstance(value, (list, dict)):
        return weight if len(value) > 0 else 0.0
    else:
        return weight

def calculate_data_freshness_score(product: Dict, weight: float = 1.0) -> float:
    \"\"\"Calculate data freshness score based on when data was last updated.\"\"\"
    from datetime import datetime, timedelta
    
    # Check for scraped_at timestamp
    scraped_at = product.get('scraped_at')
    if scraped_at:
        try:
            if isinstance(scraped_at, str):
                scraped_date = datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
            else:
                scraped_date = scraped_at
            
            days_old = (datetime.now() - scraped_date.replace(tzinfo=None)).days
            
            # Fresh data (< 7 days) gets full score
            if days_old < 7:
                return weight
            # Moderately fresh (< 30 days) gets partial score
            elif days_old < 30:
                return weight * 0.7
            # Old data (< 90 days) gets low score
            elif days_old < 90:
                return weight * 0.3
            else:
                return 0.0
        except:
            return weight * 0.5  # Default score if can't parse date
    
    return weight * 0.5  # Default score for unknown freshness

def calculate_product_quality_score(product: Dict) -> Dict[str, float]:
    \"\"\"Calculate comprehensive quality score for a product.\"\"\"
    weights = {self.config.quality_weights}
    
    scores = {{}}
    
    # Completeness scores
    scores['sku_completeness'] = calculate_completeness_score(
        product.get('sku'), weights['sku_completeness']
    )
    scores['name_completeness'] = calculate_completeness_score(
        product.get('name'), weights['name_completeness']
    )
    scores['description_completeness'] = calculate_completeness_score(
        product.get('description'), weights['description_completeness']
    )
    scores['price_completeness'] = calculate_completeness_score(
        product.get('price'), weights['price_completeness']
    )
    scores['specifications_completeness'] = calculate_completeness_score(
        product.get('specifications'), weights['specifications_completeness']
    )
    scores['images_completeness'] = calculate_completeness_score(
        product.get('images'), weights['images_completeness']
    )
    scores['brand_completeness'] = calculate_completeness_score(
        product.get('brand'), weights['brand_completeness']
    )
    scores['category_completeness'] = calculate_completeness_score(
        product.get('category'), weights['category_completeness']
    )
    
    # Data freshness score
    scores['data_freshness'] = calculate_data_freshness_score(
        product, weights['data_freshness']
    )
    
    # Calculate total quality score
    total_score = sum(scores.values())
    
    return {{
        'individual_scores': scores,
        'total_score': total_score,
        'percentage': (total_score / sum(weights.values())) * 100
    }}

# Calculate quality scores for all enriched products
quality_results = []

for product in enriched_products:
    quality_data = calculate_product_quality_score(product)
    
    # Add quality score to product
    product['quality_score'] = quality_data['total_score']
    product['quality_percentage'] = quality_data['percentage']
    product['quality_breakdown'] = quality_data['individual_scores']
    
    quality_results.append({{
        'sku': product.get('sku', 'unknown'),
        'name': product.get('name', 'unknown'),
        'quality_score': quality_data['total_score'],
        'quality_percentage': quality_data['percentage'],
        'breakdown': quality_data['individual_scores']
    }})

# Calculate aggregate quality statistics
total_products = len(quality_results)
avg_quality_score = sum(r['quality_score'] for r in quality_results) / total_products if total_products > 0 else 0
avg_quality_percentage = sum(r['quality_percentage'] for r in quality_results) / total_products if total_products > 0 else 0

high_quality_products = len([r for r in quality_results if r['quality_percentage'] >= 80])
medium_quality_products = len([r for r in quality_results if 60 <= r['quality_percentage'] < 80])
low_quality_products = len([r for r in quality_results if r['quality_percentage'] < 60])

print(f"Quality scoring completed:")
print(f"  Average quality score: {{avg_quality_score:.2f}} ({{avg_quality_percentage:.1f}}%)")
print(f"  High quality products (≥80%): {{high_quality_products}}")
print(f"  Medium quality products (60-79%): {{medium_quality_products}}")
print(f"  Low quality products (<60%): {{low_quality_products}}")

result = {{
    'enriched_products': enriched_products,
    'quality_results': quality_results,
    'quality_statistics': {{
        'total_products': total_products,
        'avg_quality_score': avg_quality_score,
        'avg_quality_percentage': avg_quality_percentage,
        'high_quality_products': high_quality_products,
        'medium_quality_products': medium_quality_products,
        'low_quality_products': low_quality_products
    }}
}}
"""
    
    def _generate_bulk_operations_prep_code(self) -> str:
        """Generate Python code for preparing bulk database operations."""
        return f"""
def prepare_product_for_database(product: Dict) -> Dict:
    \"\"\"Prepare product data for database insertion/update.\"\"\"
    
    # Map enriched product fields to database model fields
    db_product = {{}}
    
    # Core identifiers
    db_product['sku'] = str(product.get('sku', ''))
    db_product['name'] = str(product.get('name', ''))
    db_product['slug'] = str(product.get('name', '')).lower().replace(' ', '-').replace('_', '-')
    db_product['model_number'] = str(product.get('model_number', '')) if product.get('model_number') else None
    
    # Basic information
    db_product['description'] = str(product.get('description', '')) if product.get('description') else None
    db_product['long_description'] = str(product.get('long_description', '')) if product.get('long_description') else None
    
    # Product status
    db_product['status'] = 'active'
    db_product['is_published'] = True
    db_product['availability'] = product.get('availability', 'in_stock')
    
    # Pricing information
    price = product.get('price')
    if price:
        try:
            # Clean price string and convert to float
            if isinstance(price, str):
                # Remove currency symbols and extra characters
                price_clean = re.sub(r'[^\\d.,]', '', price)
                price_clean = price_clean.replace(',', '')
                db_product['price'] = float(price_clean) if price_clean else None
            else:
                db_product['price'] = float(price)
        except (ValueError, TypeError):
            db_product['price'] = None
    else:
        db_product['price'] = None
    
    db_product['currency'] = 'USD'
    
    # Rich specifications (JSONB)
    db_product['specifications'] = product.get('specifications', {{}}) if isinstance(product.get('specifications'), dict) else {{}}
    db_product['attributes'] = {{
        'source': product.get('source', 'unknown'),
        'match_method': product.get('enrichment_metadata', {{}}).get('match_method', 'unknown'),
        'match_confidence': product.get('enrichment_metadata', {{}}).get('match_confidence', 0.0),
        'sources': product.get('enrichment_metadata', {{}}).get('sources', []),
        'quality_score': product.get('quality_score', 0.0),
        'quality_percentage': product.get('quality_percentage', 0.0)
    }}
    
    # SEO and marketing
    db_product['meta_title'] = str(product.get('name', ''))[:60] if product.get('name') else None
    db_product['meta_description'] = str(product.get('description', ''))[:160] if product.get('description') else None
    
    # Web scraping enrichment data
    db_product['source_urls'] = [product.get('url')] if product.get('url') else []
    db_product['scraping_metadata'] = {{
        'scraped_at': product.get('scraped_at'),
        'enriched_at': product.get('enrichment_metadata', {{}}).get('enriched_at'),
        'conflicts_resolved': product.get('enrichment_metadata', {{}}).get('conflicts_resolved', 0)
    }}
    db_product['enriched_data'] = product.get('enrichment_metadata', {{}})
    
    # Parse scraped_at timestamp
    scraped_at = product.get('scraped_at')
    if scraped_at:
        try:
            if isinstance(scraped_at, str):
                db_product['last_scraped_at'] = datetime.fromisoformat(scraped_at.replace('Z', '+00:00')).replace(tzinfo=None)
            else:
                db_product['last_scraped_at'] = scraped_at
        except:
            db_product['last_scraped_at'] = None
    else:
        db_product['last_scraped_at'] = None
    
    return db_product

# Prepare all enriched products for bulk database operations
bulk_products = []
for product in enriched_products:
    try:
        db_product = prepare_product_for_database(product)
        bulk_products.append(db_product)
    except Exception as e:
        print(f"Error preparing product {{product.get('sku', 'unknown')}}: {{e}}")

print(f"Prepared {{len(bulk_products)}} products for bulk database operations")

# Split into batches
batch_size = {self.config.batch_size}
product_batches = []
for i in range(0, len(bulk_products), batch_size):
    batch = bulk_products[i:i + batch_size]
    product_batches.append(batch)

print(f"Split into {{len(product_batches)}} batches of up to {{batch_size}} products each")

result = {{
    'bulk_products': bulk_products,
    'product_batches': product_batches,
    'total_products': len(bulk_products),
    'total_batches': len(product_batches)
}}
"""
    
    def _generate_progress_update_code(self) -> str:
        """Generate Python code for updating progress tracking."""
        return f"""
# Update progress statistics
from datetime import datetime

# Calculate final statistics
total_processed = len(bulk_products) if 'bulk_products' in locals() else 0
total_matched = len([r for r in match_results if r['matched_products']]) if 'match_results' in locals() else 0
total_no_match = len([r for r in match_results if not r['matched_products']]) if 'match_results' in locals() else 0

# Match method breakdown
exact_sku = len([r for r in match_results if r['match_method'] == 'exact_sku']) if 'match_results' in locals() else 0
fuzzy_name = len([r for r in match_results if r['match_method'] == 'fuzzy_name']) if 'match_results' in locals() else 0
fuzzy_brand_model = len([r for r in match_results if r['match_method'] == 'fuzzy_brand_model']) if 'match_results' in locals() else 0

# Quality statistics
quality_stats = result.get('quality_statistics', {{}}) if 'result' in locals() and isinstance(result, dict) else {{}}

progress_update = {{
    'pipeline_completed_at': datetime.now().isoformat(),
    'total_products_processed': total_processed,
    'matching_statistics': {{
        'total_matched': total_matched,
        'total_no_match': total_no_match,
        'exact_sku_matches': exact_sku,
        'fuzzy_name_matches': fuzzy_name,
        'fuzzy_brand_model_matches': fuzzy_brand_model
    }},
    'quality_statistics': quality_stats,
    'database_operations': {{
        'products_upserted': total_processed,
        'batches_processed': len(product_batches) if 'product_batches' in locals() else 0
    }}
}}

print("Pipeline execution completed successfully!")
print(f"Final statistics: {{progress_update}}")

result = progress_update
"""
    
    def _generate_reports(self) -> None:
        """Generate comprehensive enrichment reports."""
        try:
            self.logger.info("Generating enrichment reports")
            
            # Create reports directory
            reports_dir = os.path.join(self.config.output_directory, "reports")
            os.makedirs(reports_dir, exist_ok=True)
            
            # Generate JSON report
            if "json" in self.config.report_formats:
                self._generate_json_report(reports_dir)
            
            # Generate HTML report
            if "html" in self.config.report_formats:
                self._generate_html_report(reports_dir)
            
            # Generate CSV report
            if "csv" in self.config.report_formats:
                self._generate_csv_report(reports_dir)
            
            self.logger.info(f"Reports generated in {reports_dir}")
            
        except Exception as e:
            self.progress.add_error(f"Report generation failed: {str(e)}")
            self.logger.error(f"Report generation failed: {str(e)}")
    
    def _generate_json_report(self, reports_dir: str) -> None:
        """Generate JSON format report."""
        report_data = {
            "pipeline_info": {
                "pipeline_id": self.progress.pipeline_id,
                "start_time": self.progress.start_time.isoformat(),
                "end_time": self.progress.end_time.isoformat() if self.progress.end_time else None,
                "duration_seconds": self.progress.get_duration(),
                "config": asdict(self.config)
            },
            "progress": self.progress.to_dict(),
            "summary": {
                "total_products_processed": len(self.enriched_products),
                "match_statistics": {
                    "exact_sku_matches": self.progress.exact_sku_matches,
                    "fuzzy_name_matches": self.progress.fuzzy_name_matches,
                    "fuzzy_brand_model_matches": self.progress.fuzzy_brand_model_matches,
                    "no_matches": self.progress.no_matches
                },
                "quality_statistics": {
                    "avg_quality_score_before": self.progress.avg_quality_score_before,
                    "avg_quality_score_after": self.progress.avg_quality_score_after,
                    "quality_improvements": self.progress.quality_improvements
                }
            }
        }
        
        report_file = os.path.join(reports_dir, f"enrichment_report_{self.progress.pipeline_id[:8]}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
    
    def _generate_html_report(self, reports_dir: str) -> None:
        """Generate HTML format report."""
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Data Enrichment Pipeline Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .stats {{ display: flex; justify-content: space-around; }}
                .stat-box {{ text-align: center; padding: 10px; }}
                .stat-number {{ font-size: 2em; font-weight: bold; color: #007acc; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .success {{ color: green; }}
                .warning {{ color: orange; }}
                .error {{ color: red; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Data Enrichment Pipeline Report</h1>
                <p><strong>Pipeline ID:</strong> {self.progress.pipeline_id}</p>
                <p><strong>Execution Time:</strong> {self.progress.start_time.strftime('%Y-%m-%d %H:%M:%S')} - 
                   {self.progress.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.progress.end_time else 'In Progress'}</p>
                <p><strong>Duration:</strong> {self.progress.get_duration():.2f} seconds</p>
            </div>
            
            <div class="section">
                <h2>Summary Statistics</h2>
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-number">{len(self.enriched_products)}</div>
                        <div>Products Processed</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{self.progress.exact_sku_matches + self.progress.fuzzy_name_matches + self.progress.fuzzy_brand_model_matches}</div>
                        <div>Successful Matches</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{self.progress.conflicts_resolved}</div>
                        <div>Conflicts Resolved</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{self.progress.avg_quality_score_after:.1f}%</div>
                        <div>Avg Quality Score</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Matching Results</h2>
                <table>
                    <tr>
                        <th>Match Type</th>
                        <th>Count</th>
                        <th>Percentage</th>
                    </tr>
                    <tr>
                        <td>Exact SKU Matches</td>
                        <td>{self.progress.exact_sku_matches}</td>
                        <td>{(self.progress.exact_sku_matches / max(len(self.enriched_products), 1) * 100):.1f}%</td>
                    </tr>
                    <tr>
                        <td>Fuzzy Name Matches</td>
                        <td>{self.progress.fuzzy_name_matches}</td>
                        <td>{(self.progress.fuzzy_name_matches / max(len(self.enriched_products), 1) * 100):.1f}%</td>
                    </tr>
                    <tr>
                        <td>Fuzzy Brand+Model Matches</td>
                        <td>{self.progress.fuzzy_brand_model_matches}</td>
                        <td>{(self.progress.fuzzy_brand_model_matches / max(len(self.enriched_products), 1) * 100):.1f}%</td>
                    </tr>
                    <tr>
                        <td>No Matches</td>
                        <td>{self.progress.no_matches}</td>
                        <td>{(self.progress.no_matches / max(len(self.enriched_products), 1) * 100):.1f}%</td>
                    </tr>
                </table>
            </div>
            
            <div class="section">
                <h2>Errors and Warnings</h2>
                <h3 class="error">Errors ({len(self.progress.errors)})</h3>
                <ul>
                    {''.join(f'<li class="error">{error}</li>' for error in self.progress.errors[-10:])}
                </ul>
                
                <h3 class="warning">Warnings ({len(self.progress.warnings)})</h3>
                <ul>
                    {''.join(f'<li class="warning">{warning}</li>' for warning in self.progress.warnings[-10:])}
                </ul>
            </div>
        </body>
        </html>
        """
        
        report_file = os.path.join(reports_dir, f"enrichment_report_{self.progress.pipeline_id[:8]}.html")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_template)
    
    def _generate_csv_report(self, reports_dir: str) -> None:
        """Generate CSV format report."""
        try:
            # Create summary CSV
            summary_data = [
                ["Metric", "Value"],
                ["Pipeline ID", self.progress.pipeline_id],
                ["Start Time", self.progress.start_time.isoformat()],
                ["End Time", self.progress.end_time.isoformat() if self.progress.end_time else ""],
                ["Duration (seconds)", self.progress.get_duration()],
                ["Products Processed", len(self.enriched_products)],
                ["Exact SKU Matches", self.progress.exact_sku_matches],
                ["Fuzzy Name Matches", self.progress.fuzzy_name_matches],
                ["Fuzzy Brand+Model Matches", self.progress.fuzzy_brand_model_matches],
                ["No Matches", self.progress.no_matches],
                ["Conflicts Resolved", self.progress.conflicts_resolved],
                ["Products Created", self.progress.products_created],
                ["Products Updated", self.progress.products_updated],
                ["Average Quality Score Before", self.progress.avg_quality_score_before],
                ["Average Quality Score After", self.progress.avg_quality_score_after],
                ["Quality Improvements", self.progress.quality_improvements]
            ]
            
            summary_file = os.path.join(reports_dir, f"enrichment_summary_{self.progress.pipeline_id[:8]}.csv")
            df_summary = pd.DataFrame(summary_data, columns=["Metric", "Value"])
            df_summary.to_csv(summary_file, index=False)
            
            # Create detailed product CSV if we have enriched products
            if self.enriched_products:
                detailed_file = os.path.join(reports_dir, f"enriched_products_{self.progress.pipeline_id[:8]}.csv")
                df_products = pd.DataFrame(self.enriched_products)
                df_products.to_csv(detailed_file, index=False)
            
        except Exception as e:
            self.logger.error(f"CSV report generation failed: {str(e)}")
    
    def save_checkpoint(self) -> None:
        """Save pipeline checkpoint for resumability."""
        try:
            checkpoint_data = {
                "pipeline_id": self.progress.pipeline_id,
                "progress": self.progress.to_dict(),
                "config": asdict(self.config),
                "enriched_products": self.enriched_products,
                "match_results": [asdict(mr) for mr in self.match_results],
                "quality_scores": self.quality_scores
            }
            
            checkpoint_file = os.path.join(
                self.config.output_directory, 
                f"checkpoint_{self.progress.pipeline_id[:8]}.json"
            )
            
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, default=str)
            
            self.progress.checkpoints_saved += 1
            self.logger.info(f"Checkpoint saved: {checkpoint_file}")
            
        except Exception as e:
            self.progress.add_error(f"Checkpoint save failed: {str(e)}")
            self.logger.error(f"Checkpoint save failed: {str(e)}")
    
    def load_checkpoint(self, checkpoint_file: str) -> bool:
        """Load pipeline state from checkpoint."""
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            self.progress = EnrichmentProgress(**checkpoint_data["progress"])
            self.enriched_products = checkpoint_data["enriched_products"]
            self.match_results = [MatchResult(**mr) for mr in checkpoint_data["match_results"]]
            self.quality_scores = checkpoint_data["quality_scores"]
            
            self.logger.info(f"Checkpoint loaded: {checkpoint_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Checkpoint load failed: {str(e)}")
            return False


def create_sample_pipeline() -> DataEnrichmentPipeline:
    """Create a sample pipeline with default configuration."""
    config = EnrichmentConfig()
    return DataEnrichmentPipeline(config)


def run_enrichment_pipeline(
    excel_file: str = None,
    scraped_data_dir: str = None,
    supplier_data_dir: str = None,
    output_dir: str = None
) -> EnrichmentProgress:
    """
    Convenience function to run the complete enrichment pipeline.
    
    Args:
        excel_file: Path to Excel file with master product data
        scraped_data_dir: Directory containing scraped product JSON files
        supplier_data_dir: Directory containing supplier product JSON files  
        output_dir: Directory for pipeline outputs and reports
    
    Returns:
        EnrichmentProgress: Complete pipeline execution results
    """
    config = EnrichmentConfig()
    
    # Update config with provided paths
    if excel_file:
        config.excel_file_path = excel_file
    if scraped_data_dir:
        config.scraped_data_directory = scraped_data_dir
    if supplier_data_dir:
        config.supplier_data_directory = supplier_data_dir
    if output_dir:
        config.output_directory = output_dir
    
    # Create and run pipeline
    pipeline = DataEnrichmentPipeline(config)
    return pipeline.run_complete_pipeline()


if __name__ == "__main__":
    # Example usage
    print("Starting Horme Data Enrichment Pipeline...")
    
    # Create sample configuration
    config = EnrichmentConfig()
    print(f"Configuration: {asdict(config)}")
    
    # Create and run pipeline
    pipeline = DataEnrichmentPipeline(config)
    results = pipeline.run_complete_pipeline()
    
    print(f"Pipeline completed! Results:")
    print(f"  Duration: {results.get_duration():.2f} seconds")
    print(f"  Products processed: {results.products_enriched}")
    print(f"  Conflicts resolved: {results.conflicts_resolved}")
    print(f"  Average quality improvement: {results.avg_quality_score_after - results.avg_quality_score_before:.1f}%")
    
    if results.errors:
        print(f"  Errors encountered: {len(results.errors)}")
        for error in results.errors[-3:]:  # Show last 3 errors
            print(f"    - {error}")