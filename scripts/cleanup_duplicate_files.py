"""
Remove Duplicate and Mock Data Files - PRODUCTION CLEANUP
Systematically remove all duplicate implementations to ensure only one working version exists

Author: Horme Production Team
Date: 2025-01-17
"""

import os
import sys
from pathlib import Path
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Files to DELETE (duplicates and mock data)
FILES_TO_DELETE = [
    # ========================================================================
    # DUPLICATE RECOMMENDATION ENGINES (Keep ONLY hybrid_recommendation_engine.py)
    # ========================================================================
    "src/diy_recommendation_engine.py",
    "src/project_recommendation_engine.py",
    "src/standalone_project_recommendation_engine.py",
    "src/simple_work_recommendation_engine.py",
    "src/enhanced_work_recommendation_engine.py",
    "src/intelligent_work_recommendation_engine.py",

    # ========================================================================
    # DUPLICATE API SERVERS (Keep ONLY production_api_server.py)
    # ========================================================================
    "src/simplified_api_server.py",
    "src/simple_recommendation_api_server.py",
    "src/work_recommendation_api.py",
    "src/enhanced_work_recommendation_api.py",
    "src/intelligent_work_recommendation_api.py",

    # ========================================================================
    # DUPLICATE RFP SYSTEMS (Keep ONLY production modules)
    # ========================================================================
    "src/simple_rfp_api.py",
    "src/simple_rfp_system.py",
    "src/rfp_api_server.py",
    "src/advanced_rfp_processing_system.py",
    "src/enhanced_rfp_analysis_system.py",
    "src/enhanced_rfp_api_server.py",
    "src/professional_rfp_processor.py",
    "src/rfp_analysis_system.py",
    "src/improved_rfp_matcher.py",
    "src/rfp_database_integration.py",
    "src/rfp_mcp_server.py",

    # ========================================================================
    # DUPLICATE NEXUS PLATFORMS (Keep ONLY nexus_production_api.py)
    # ========================================================================
    "src/production_nexus_diy_platform.py",
    "src/production_nexus_diy_platform_fixes.py",
    "src/production_nexus_diy_platform_safety_fix.py",
    "src/diy_nexus_platform.py",

    # ========================================================================
    # DUPLICATE WORKFLOWS (Keep ONLY product_matching.py - will be cleaned)
    # ========================================================================
    "src/workflows/product_matching_fixed.py",

    # ========================================================================
    # DUPLICATE/STANDALONE SYSTEMS
    # ========================================================================
    "src/simplified_horme_system.py",
    "src/simplified_standalone_system.py",
    "src/standalone_enrichment_pipeline.py",

    # ========================================================================
    # DEMO/TEST FILES IN SRC (Should be in tests/)
    # ========================================================================
    "src/demo_enrichment_pipeline.py",
    "src/demo_supplier_scraping.py",

    # ========================================================================
    # DUPLICATE ENRICHMENT PIPELINES
    # ========================================================================
    "src/comprehensive_horme_enrichment_pipeline.py",
    "src/data_enrichment_pipeline.py",
    "src/enrichment_pipeline_compatible.py",
    "src/enrichment_pipeline_executor.py",
    "src/enrichment_dashboard.py",
    "src/enrichment_quality_monitor.py",
    "src/fixed_product_enrichment_pipeline.py",
    "src/horme_product_enrichment_pipeline.py",
    "src/product_enrichment_pipeline.py",
    "src/standalone_enrichment_pipeline.py",

    # ========================================================================
    # DUPLICATE SCRAPERS
    # ========================================================================
    "src/horme_scraper.py",
    "src/supplier_scrapers.py",
    "src/supplier_discovery.py",

    # ========================================================================
    # DUPLICATE KNOWLEDGE/DATABASE SYSTEMS
    # ========================================================================
    "src/diy_content_enrichment.py",
    "src/diy_knowledge_graph.py",
    "src/diy_knowledge_models.py",
    "src/diy_project_database.py",
    "src/concurrent_database_manager.py",
    "src/horme_database_setup.py",

    # ========================================================================
    # DUPLICATE DATAFLOW DEMOS
    # ========================================================================
    "src/horme_dataflow_demo.py",
    "src/horme_dataflow_models.py",  # Use src/dataflow_models.py instead

    # ========================================================================
    # MOCK/DEMO INTEGRATION SYSTEMS
    # ========================================================================
    "src/community_knowledge_extractor.py",
    "src/community_product_integration.py",
    "src/enhanced_community_extractor.py",

    # ========================================================================
    # DUPLICATE API INTERFACES
    # ========================================================================
    "src/production_cli_interface.py",  # Use Nexus CLI instead
    "src/start_horme_api.py",  # Use production_api_server.py

    # ========================================================================
    # TEST RESULTS / SAMPLE DATA IN SRC
    # ========================================================================
    "src/final_supplier_test_results_20250805_222528.json",
    "src/supplier_test_results_20250805_222401.json",
    "src/sample_product_data_20250805_222444.json",
    "src/horme_simplified.db",
    "src/products.db",
    "src/quotations.db",

    # ========================================================================
    # STANDALONE MCP SERVERS (Use integrated version)
    # ========================================================================
    "src/production_mcp_server.py",  # Use nexus_production_mcp.py instead

    # ========================================================================
    # MOCK VALIDATION SCRIPTS IN SRC
    # ========================================================================
    "src/sdk_compliance_validation_final.py",
    "src/sdk_compliant_api_endpoints.py",
    "src/sdk_compliant_background_processing.py",
    "src/sdk_compliant_search_workflow.py",
    "src/sdk_compliant_search_workflow_fixed.py",
    "src/sdk_compliant_search_workflow_standalone.py",

    # ========================================================================
    # SEMANTIC/VISUAL MOCK SYSTEMS
    # ========================================================================
    "src/semantic_product_understanding.py",
    "src/visual_understanding.py",

    # ========================================================================
    # HEALTH CHECK DUPLICATES
    # ========================================================================
    "src/health_check_system.py",  # Use production_api_server.py health endpoint

    # ========================================================================
    # IMPORT SCRIPTS IN SRC (Should be in scripts/)
    # ========================================================================
    "src/import_excel_to_database.py",

    # ========================================================================
    # KAILASH MOCK (Not needed)
    # ========================================================================
    "src/kailash_mock.py",

    # ========================================================================
    # DUPLICATE AI SYSTEMS
    # ========================================================================
    "src/ai_quotation_generator.py",  # Use production modules
]

# Directories to DELETE (duplicates/obsolete)
DIRECTORIES_TO_DELETE = [
    "src/horme_scraper/",  # Duplicate scraper directory
    "src/test_output/",  # Test output in src/ (should be in tests/)
]


def delete_file(filepath: Path) -> bool:
    """Delete a single file"""
    if filepath.exists():
        try:
            filepath.unlink()
            logger.info(f"  DELETED: {filepath.relative_to(PROJECT_ROOT)}")
            return True
        except Exception as e:
            logger.error(f"  FAILED to delete {filepath.relative_to(PROJECT_ROOT)}: {e}")
            return False
    else:
        logger.debug(f"  SKIP (not found): {filepath.relative_to(PROJECT_ROOT)}")
        return False


def delete_directory(dirpath: Path) -> bool:
    """Delete an entire directory"""
    if dirpath.exists() and dirpath.is_dir():
        try:
            shutil.rmtree(dirpath)
            logger.info(f"  DELETED DIR: {dirpath.relative_to(PROJECT_ROOT)}")
            return True
        except Exception as e:
            logger.error(f"  FAILED to delete directory {dirpath.relative_to(PROJECT_ROOT)}: {e}")
            return False
    else:
        logger.debug(f"  SKIP (not found): {dirpath.relative_to(PROJECT_ROOT)}")
        return False


def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("HORME POV - DUPLICATE FILE CLEANUP")
    logger.info("="*80)
    logger.info(f"Project Root: {PROJECT_ROOT}")
    logger.info("="*80)

    # Confirm with user
    logger.warning("\nWARNING: This will permanently delete duplicate files.")
    logger.warning(f"Files to delete: {len(FILES_TO_DELETE)}")
    logger.warning(f"Directories to delete: {len(DIRECTORIES_TO_DELETE)}")

    response = input("\nProceed with cleanup? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        logger.info("Cleanup cancelled by user.")
        sys.exit(0)

    # Delete files
    logger.info("\nDeleting Files...")
    files_deleted = 0
    for file_path in FILES_TO_DELETE:
        full_path = PROJECT_ROOT / file_path
        if delete_file(full_path):
            files_deleted += 1

    # Delete directories
    logger.info("\nDeleting Directories...")
    dirs_deleted = 0
    for dir_path in DIRECTORIES_TO_DELETE:
        full_path = PROJECT_ROOT / dir_path
        if delete_directory(full_path):
            dirs_deleted += 1

    # Summary
    logger.info("\n" + "="*80)
    logger.info("CLEANUP COMPLETE")
    logger.info("="*80)
    logger.info(f"Files deleted: {files_deleted}/{len(FILES_TO_DELETE)}")
    logger.info(f"Directories deleted: {dirs_deleted}/{len(DIRECTORIES_TO_DELETE)}")
    logger.info("="*80)

    # List remaining production files
    logger.info("\nPRODUCTION FILES (Retained):")
    production_files = [
        "src/ai/hybrid_recommendation_engine.py",
        "src/production_api_server.py",
        "src/production_api_endpoints.py",
        "src/nexus_production_api.py",
        "src/nexus_production_mcp.py",
        "src/nexus_backend_api.py",
        "src/models/production_models.py",
        "src/dataflow_models.py",
        "src/core/neo4j_knowledge_graph.py",
        "src/core/postgresql_database.py",
        "src/core/auth.py",
        "src/core/config.py",
        "src/workflows/product_matching.py",
    ]

    for file_path in production_files:
        full_path = PROJECT_ROOT / file_path
        status = "EXISTS" if full_path.exists() else "MISSING"
        logger.info(f"  [{status}] {file_path}")

    logger.info("\n" + "="*80)
    logger.info("Next Steps:")
    logger.info("1. Clean mock data from src/workflows/product_matching.py")
    logger.info("2. Review logs for any errors")
    logger.info("3. Run tests to ensure system still works")
    logger.info("="*80)


if __name__ == "__main__":
    main()
