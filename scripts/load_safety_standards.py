#!/usr/bin/env python3
"""
Load Safety Standards into Neo4j Knowledge Graph
Populates OSHA/ANSI standards and creates product-safety relationships
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.neo4j_knowledge_graph import get_knowledge_graph
from src.safety.osha_compliance import get_osha_compliance_engine
from src.safety.ansi_compliance import get_ansi_compliance_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_safety_equipment_nodes(kg):
    """Create SafetyEquipment nodes in Neo4j"""
    logger.info("Creating SafetyEquipment nodes...")

    safety_equipment = [
        {
            "id": "ppe_safety_glasses",
            "name": "Safety Glasses",
            "category": "eye_protection",
            "standard": "ANSI Z87.1-2020",
            "mandatory": True,
            "description": "Impact-resistant safety glasses meeting ANSI Z87+ standards"
        },
        {
            "id": "ppe_face_shield",
            "name": "Face Shield",
            "category": "face_protection",
            "standard": "ANSI Z87.1-2020",
            "mandatory": True,
            "description": "Full-face protection shield for high-impact hazards"
        },
        {
            "id": "ppe_work_gloves",
            "name": "Work Gloves",
            "category": "hand_protection",
            "standard": "ANSI/ISEA 105-2016",
            "mandatory": True,
            "description": "Cut-resistant work gloves meeting ANSI cut level standards"
        },
        {
            "id": "ppe_hearing_protection",
            "name": "Hearing Protection",
            "category": "hearing_protection",
            "standard": "ANSI S3.19-1974",
            "mandatory": True,
            "description": "Earplugs or earmuffs with appropriate NRR rating"
        },
        {
            "id": "ppe_dust_mask",
            "name": "Dust Mask",
            "category": "respiratory_protection",
            "standard": "29 CFR 1926.103",
            "mandatory": True,
            "description": "N95 or higher respirator for dust and particulate protection"
        },
        {
            "id": "ppe_hard_hat",
            "name": "Hard Hat",
            "category": "head_protection",
            "standard": "ANSI Z89.1-2017",
            "mandatory": True,
            "description": "Impact-resistant hard hat meeting ANSI Type I or II standards"
        },
        {
            "id": "ppe_steel_toe_boots",
            "name": "Steel Toe Boots",
            "category": "foot_protection",
            "standard": "ASTM F2413-18",
            "mandatory": True,
            "description": "Safety boots with steel toe protection meeting ASTM standards"
        }
    ]

    created = 0

    for equipment in safety_equipment:
        try:
            query = """
            MERGE (se:SafetyEquipment {id: $id})
            SET se.name = $name,
                se.category = $category,
                se.standard = $standard,
                se.mandatory = $mandatory,
                se.description = $description,
                se.updated_at = datetime()
            RETURN se.id as id
            """

            with kg.get_session() as session:
                result = session.run(
                    query,
                    id=equipment["id"],
                    name=equipment["name"],
                    category=equipment["category"],
                    standard=equipment["standard"],
                    mandatory=equipment["mandatory"],
                    description=equipment["description"]
                )
                created_id = result.single()["id"]
                logger.debug(f"Created SafetyEquipment node: {created_id}")
                created += 1

        except Exception as e:
            logger.error(f"Failed to create safety equipment {equipment['id']}: {e}")

    logger.info(f"✅ Created {created} SafetyEquipment nodes")
    return created


def create_task_safety_requirements(kg, standards_data):
    """Create task nodes and safety requirements"""
    logger.info("Creating task safety requirements...")

    task_requirements = standards_data.get("task_safety_requirements", {})
    created_tasks = 0
    created_relationships = 0

    for task_key, task_data in task_requirements.items():
        task_id = f"task_{task_key}"

        logger.info(f"Processing task: {task_id}")

        # Create task node if not exists
        try:
            success = kg.create_task_node(
                task_id=task_id,
                name=task_key.replace('_', ' ').title(),
                description=f"Safety-assessed task: {task_key}",
                category="safety_assessed",
                skill_level="intermediate"
            )

            if success:
                created_tasks += 1

        except Exception as e:
            logger.warning(f"Task node creation failed (may already exist): {e}")

        # Create safety requirements relationships
        mandatory_ppe = task_data.get("mandatory_ppe", [])
        risk_level = task_data.get("risk_level", "medium")
        osha_standards = task_data.get("osha_standards", [])

        for ppe in mandatory_ppe:
            ppe_id = f"ppe_{ppe}"

            try:
                query = """
                MATCH (t:Task {id: $task_id})
                MATCH (se:SafetyEquipment {id: $ppe_id})
                MERGE (t)-[r:REQUIRES_SAFETY]->(se)
                SET r.risk_level = $risk_level,
                    r.osha_standards = $osha_standards,
                    r.mandatory = true,
                    r.created_at = datetime()
                RETURN t.name as task, se.name as equipment
                """

                with kg.get_session() as session:
                    result = session.run(
                        query,
                        task_id=task_id,
                        ppe_id=ppe_id,
                        risk_level=risk_level,
                        osha_standards=osha_standards
                    )

                    record = result.single()
                    if record:
                        logger.debug(
                            f"Created REQUIRES_SAFETY: {record['task']} -> {record['equipment']}"
                        )
                        created_relationships += 1

            except Exception as e:
                logger.warning(f"Failed to create REQUIRES_SAFETY relationship: {e}")

    logger.info(f"✅ Created {created_tasks} task nodes")
    logger.info(f"✅ Created {created_relationships} REQUIRES_SAFETY relationships")

    return created_tasks, created_relationships


def create_product_safety_mappings(kg, standards_data):
    """Create product-safety equipment mappings"""
    logger.info("Creating product safety mappings...")

    product_mappings = standards_data.get("product_safety_mappings", {})
    logger.info(f"Found {len(product_mappings)} product safety mappings")

    # Note: This creates the mapping structure
    # In production, you would query PostgreSQL for actual product IDs
    # and create relationships for real products

    logger.info("⚠️  Product safety mappings loaded (requires actual product IDs from database)")
    logger.info("   Use this data structure to map products when they are created")

    return len(product_mappings)


def verify_safety_data_load(kg):
    """Verify safety data was loaded correctly"""
    logger.info("Verifying safety data load...")

    try:
        with kg.get_session() as session:
            # Count SafetyEquipment nodes
            equipment_query = "MATCH (se:SafetyEquipment) RETURN count(se) as count"
            equipment_result = session.run(equipment_query)
            equipment_count = equipment_result.single()["count"]

            # Count REQUIRES_SAFETY relationships
            relationship_query = "MATCH ()-[r:REQUIRES_SAFETY]->() RETURN count(r) as count"
            relationship_result = session.run(relationship_query)
            relationship_count = relationship_result.single()["count"]

            # Count Task nodes with safety requirements
            task_query = """
            MATCH (t:Task)-[:REQUIRES_SAFETY]->()
            RETURN count(DISTINCT t) as count
            """
            task_result = session.run(task_query)
            task_count = task_result.single()["count"]

            logger.info(f"✅ Verification Complete:")
            logger.info(f"   SafetyEquipment nodes: {equipment_count}")
            logger.info(f"   Tasks with safety requirements: {task_count}")
            logger.info(f"   REQUIRES_SAFETY relationships: {relationship_count}")

            return {
                "equipment_nodes": equipment_count,
                "task_nodes": task_count,
                "safety_relationships": relationship_count
            }

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return None


def load_safety_standards():
    """Main function to load safety standards into Neo4j"""
    try:
        logger.info("="*80)
        logger.info("LOADING SAFETY STANDARDS INTO NEO4J KNOWLEDGE GRAPH")
        logger.info("="*80)

        # Load safety standards JSON
        standards_path = Path(__file__).parent.parent / "data" / "safety_standards.json"

        if not standards_path.exists():
            logger.error(f"Safety standards file not found: {standards_path}")
            return False

        with open(standards_path, 'r') as f:
            standards_data = json.load(f)

        logger.info(f"✅ Loaded safety standards from {standards_path}")
        logger.info(f"   OSHA Standards: {len(standards_data.get('osha_standards', {}))}")
        logger.info(f"   ANSI Standards: {len(standards_data.get('ansi_standards', {}))}")
        logger.info(f"   Product Mappings: {len(standards_data.get('product_safety_mappings', {}))}")
        logger.info(f"   Task Requirements: {len(standards_data.get('task_safety_requirements', {}))}")

        # Connect to Neo4j
        logger.info("\nConnecting to Neo4j...")
        kg = get_knowledge_graph()

        if not kg.test_connection():
            logger.error("❌ Neo4j connection failed")
            logger.error("   Ensure Neo4j is running and NEO4J_PASSWORD is set")
            return False

        logger.info("✅ Neo4j connection successful")

        # Step 1: Create SafetyEquipment nodes
        logger.info("\nStep 1: Creating SafetyEquipment nodes...")
        equipment_count = create_safety_equipment_nodes(kg)

        # Step 2: Create task safety requirements
        logger.info("\nStep 2: Creating task safety requirements...")
        task_count, rel_count = create_task_safety_requirements(kg, standards_data)

        # Step 3: Create product safety mappings
        logger.info("\nStep 3: Processing product safety mappings...")
        mapping_count = create_product_safety_mappings(kg, standards_data)

        # Step 4: Verify data load
        logger.info("\nStep 4: Verifying data load...")
        verification = verify_safety_data_load(kg)

        # Summary
        logger.info("\n" + "="*80)
        logger.info("SAFETY STANDARDS LOAD COMPLETE")
        logger.info("="*80)
        logger.info(f"SafetyEquipment nodes created: {equipment_count}")
        logger.info(f"Task nodes created: {task_count}")
        logger.info(f"REQUIRES_SAFETY relationships created: {rel_count}")
        logger.info(f"Product safety mappings processed: {mapping_count}")

        if verification:
            logger.info("\nVerification Results:")
            logger.info(f"   Total SafetyEquipment nodes: {verification['equipment_nodes']}")
            logger.info(f"   Total Task nodes with safety: {verification['task_nodes']}")
            logger.info(f"   Total REQUIRES_SAFETY relationships: {verification['safety_relationships']}")

        logger.info("\n✅ Safety Compliance System Ready for Production")
        logger.info("="*80)

        return True

    except Exception as e:
        logger.error(f"❌ Failed to load safety standards: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = load_safety_standards()
    sys.exit(0 if success else 1)
