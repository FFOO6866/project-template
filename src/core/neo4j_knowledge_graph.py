"""
Neo4j Knowledge Graph Service
Phase 1: Enterprise AI Recommendation System
Integrates with existing PostgreSQL database for product-task-project relationships
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from contextlib import contextmanager

try:
    from neo4j import GraphDatabase, Driver, Session
    from neo4j.exceptions import ServiceUnavailable, AuthError
except ImportError:
    raise ImportError(
        "neo4j driver is required. Install with: pip install neo4j"
    )

logger = logging.getLogger(__name__)


class Neo4jKnowledgeGraph:
    """
    Neo4j Knowledge Graph Service for product-task-project relationships

    Features:
    - Tool-to-task relationship management
    - Product compatibility rules
    - Safety equipment requirements (OSHA/ANSI)
    - Skill level mapping
    - UNSPSC/ETIM classification integration
    - High-performance graph queries (<500ms requirement)

    Integration:
    - Reads product data from PostgreSQL
    - Creates graph relationships in Neo4j
    - Provides recommendation queries for hybrid AI engine
    """

    def __init__(
        self,
        uri: str = None,
        user: str = None,
        password: str = None,
        database: str = "neo4j"
    ):
        """
        Initialize Neo4j connection

        PRODUCTION REQUIREMENT:
        - NEO4J_URI must be set in environment (NO localhost defaults)
        - Use Docker service name 'neo4j' in production
        - Example: bolt://neo4j:7687 or neo4j://neo4j:7687

        Args:
            uri: Neo4j bolt URI (default: from NEO4J_URI env)
            user: Neo4j username (default: from NEO4J_USER env)
            password: Neo4j password (default: from NEO4J_PASSWORD env)
            database: Neo4j database name (default: 'neo4j')

        Raises:
            ValueError: If required configuration is missing or invalid
        """
        # Get environment to determine if this is production
        environment = os.getenv('ENVIRONMENT', 'development').lower()

        # Get configuration from environment or parameters
        self.uri = uri or os.getenv('NEO4J_URI')
        self.user = user or os.getenv('NEO4J_USER', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD')
        self.database = database

        # CRITICAL: Fail fast if NEO4J_URI not configured
        if not self.uri:
            raise ValueError(
                "NEO4J_URI environment variable is required. "
                "Set NEO4J_URI=bolt://neo4j:7687 (use Docker service name 'neo4j' in production)"
            )

        # CRITICAL: Block localhost in production
        if environment == 'production' and 'localhost' in self.uri.lower():
            raise ValueError(
                "NEO4J_URI cannot contain 'localhost' in production environment. "
                "Use Docker service name 'neo4j' instead: bolt://neo4j:7687"
            )

        if not self.password:
            raise ValueError(
                "Neo4j password is required. Set NEO4J_PASSWORD environment variable "
                "or provide password parameter."
            )

        self.driver: Optional[Driver] = None
        self._connect()

    def _connect(self):
        """Establish Neo4j driver connection with retry logic"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )

            # Test connection
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 AS test")
                result.single()

            logger.info(f"✅ Connected to Neo4j at {self.uri}")

        except AuthError as e:
            logger.error(f"❌ Neo4j authentication failed: {e}")
            raise
        except ServiceUnavailable as e:
            logger.error(f"❌ Neo4j service unavailable at {self.uri}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            raise

    @contextmanager
    def get_session(self) -> Session:
        """Get Neo4j session with context manager"""
        session = None
        try:
            session = self.driver.session(database=self.database)
            yield session
        finally:
            if session:
                session.close()

    def test_connection(self) -> bool:
        """Test Neo4j connection"""
        try:
            with self.get_session() as session:
                result = session.run("RETURN 1 AS test")
                test_value = result.single()["test"]
                logger.info(f"✅ Neo4j connection test passed: {test_value}")
                return True
        except Exception as e:
            logger.error(f"❌ Neo4j connection test failed: {e}")
            raise RuntimeError(f"Neo4j connection test failed: {str(e)}") from e

    def verify_schema(self) -> Dict[str, Any]:
        """
        Verify Neo4j schema initialization
        Returns constraints, indexes, and node counts
        """
        try:
            with self.get_session() as session:
                # Get constraints
                constraints_result = session.run("SHOW CONSTRAINTS")
                constraints = [dict(record) for record in constraints_result]

                # Get indexes
                indexes_result = session.run("SHOW INDEXES")
                indexes = [dict(record) for record in indexes_result]

                # Get node counts by label
                counts_query = """
                MATCH (n)
                RETURN labels(n)[0] as NodeType, count(n) as Count
                ORDER BY Count DESC
                """
                counts_result = session.run(counts_query)
                node_counts = {record["NodeType"]: record["Count"] for record in counts_result}

                schema_info = {
                    "status": "initialized",
                    "constraints": len(constraints),
                    "indexes": len(indexes),
                    "node_counts": node_counts,
                    "total_nodes": sum(node_counts.values())
                }

                logger.info(f"✅ Neo4j schema verified: {schema_info}")
                return schema_info

        except Exception as e:
            logger.error(f"❌ Failed to verify schema: {e}")
            raise RuntimeError(f"Schema verification failed: {str(e)}") from e

    # =========================================================================
    # Product Node Operations
    # =========================================================================

    def create_product_node(
        self,
        product_id: int,
        sku: str,
        name: str,
        category: str,
        brand: str,
        description: str = None,
        keywords: List[str] = None
    ) -> bool:
        """
        Create product node in Neo4j knowledge graph

        Args:
            product_id: Unique product ID from PostgreSQL
            sku: Product SKU
            name: Product name
            category: Product category
            brand: Product brand
            description: Product description (optional)
            keywords: Search keywords (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
            MERGE (p:Product {id: $product_id})
            SET p.sku = $sku,
                p.name = $name,
                p.category = $category,
                p.brand = $brand,
                p.description = $description,
                p.keywords = $keywords,
                p.updated_at = datetime()
            RETURN p.id as id
            """

            with self.get_session() as session:
                result = session.run(
                    query,
                    product_id=product_id,
                    sku=sku,
                    name=name,
                    category=category,
                    brand=brand,
                    description=description or "",
                    keywords=",".join(keywords or [])
                )
                created_id = result.single()["id"]
                logger.debug(f"Created product node: {created_id} - {name}")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to create product node {product_id}: {e}")
            raise RuntimeError(f"Failed to create product node {product_id}: {str(e)}") from e

    def bulk_create_products(self, products: List[Dict]) -> Tuple[int, int]:
        """
        Bulk create product nodes from PostgreSQL products

        Args:
            products: List of product dictionaries from PostgreSQL

        Returns:
            Tuple of (successful_count, failed_count)
        """
        successful = 0
        failed = 0

        try:
            query = """
            UNWIND $products AS product
            MERGE (p:Product {id: product.id})
            SET p.sku = product.sku,
                p.name = product.name,
                p.category = product.category,
                p.brand = product.brand,
                p.description = product.description,
                p.keywords = product.keywords,
                p.updated_at = datetime()
            RETURN count(p) as created
            """

            # Process in batches of 500 for performance
            batch_size = 500
            for i in range(0, len(products), batch_size):
                batch = products[i:i + batch_size]

                with self.get_session() as session:
                    result = session.run(query, products=batch)
                    created_count = result.single()["created"]
                    successful += created_count

            logger.info(f"✅ Bulk created {successful} product nodes")
            return successful, failed

        except Exception as e:
            logger.error(f"❌ Bulk product creation failed: {e}")
            raise RuntimeError(f"Bulk product creation failed after {successful} successes and {failed} failures: {str(e)}") from e

    # =========================================================================
    # Task Node Operations
    # =========================================================================

    def create_task_node(
        self,
        task_id: str,
        name: str,
        description: str,
        category: str,
        skill_level: str = "beginner",
        estimated_time_minutes: int = None
    ) -> bool:
        """
        Create task node in Neo4j knowledge graph

        Args:
            task_id: Unique task identifier (e.g., 'task_drill_hole')
            name: Task name (e.g., 'Drill Hole in Concrete')
            description: Detailed task description
            category: Task category (e.g., 'drilling', 'painting', 'installation')
            skill_level: Required skill level ('beginner', 'intermediate', 'advanced', 'expert')
            estimated_time_minutes: Estimated time to complete (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
            MERGE (t:Task {id: $task_id})
            SET t.name = $name,
                t.description = $description,
                t.category = $category,
                t.skill_level = $skill_level,
                t.estimated_time_minutes = $estimated_time_minutes,
                t.updated_at = datetime()
            RETURN t.id as id
            """

            with self.get_session() as session:
                result = session.run(
                    query,
                    task_id=task_id,
                    name=name,
                    description=description,
                    category=category,
                    skill_level=skill_level,
                    estimated_time_minutes=estimated_time_minutes
                )
                created_id = result.single()["id"]
                logger.debug(f"Created task node: {created_id} - {name}")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to create task node {task_id}: {e}")
            raise RuntimeError(f"Failed to create task node {task_id}: {str(e)}") from e

    # =========================================================================
    # Relationship Operations (Product-Task Mapping)
    # =========================================================================

    def create_product_used_for_task(
        self,
        product_id: int,
        task_id: str,
        necessity: str = "required",
        usage_notes: str = None
    ) -> bool:
        """
        Create USED_FOR relationship between product and task

        Args:
            product_id: Product node ID
            task_id: Task node ID
            necessity: 'required', 'recommended', or 'optional'
            usage_notes: Additional usage information (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
            MATCH (p:Product {id: $product_id})
            MATCH (t:Task {id: $task_id})
            MERGE (p)-[r:USED_FOR]->(t)
            SET r.necessity = $necessity,
                r.usage_notes = $usage_notes,
                r.created_at = datetime()
            RETURN p.name as product, t.name as task
            """

            with self.get_session() as session:
                result = session.run(
                    query,
                    product_id=product_id,
                    task_id=task_id,
                    necessity=necessity,
                    usage_notes=usage_notes or ""
                )
                record = result.single()
                logger.debug(
                    f"Created USED_FOR: {record['product']} -> {record['task']}"
                )
                return True

        except Exception as e:
            logger.error(
                f"❌ Failed to create USED_FOR relationship "
                f"(product={product_id}, task={task_id}): {e}"
            )
            raise RuntimeError(f"Failed to create USED_FOR relationship between product {product_id} and task {task_id}: {str(e)}") from e

    def create_product_requires_safety_equipment(
        self,
        product_id: int,
        safety_equipment_id: str,
        risk_level: str = "medium"
    ) -> bool:
        """
        Create REQUIRES_SAFETY relationship between product and safety equipment

        Args:
            product_id: Product node ID
            safety_equipment_id: Safety equipment ID (e.g., 'ppe_safety_glasses')
            risk_level: 'low', 'medium', 'high', or 'critical'

        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
            MATCH (p:Product {id: $product_id})
            MATCH (se:SafetyEquipment {id: $safety_equipment_id})
            MERGE (p)-[r:REQUIRES_SAFETY]->(se)
            SET r.risk_level = $risk_level,
                r.created_at = datetime()
            RETURN p.name as product, se.name as safety_equipment
            """

            with self.get_session() as session:
                result = session.run(
                    query,
                    product_id=product_id,
                    safety_equipment_id=safety_equipment_id,
                    risk_level=risk_level
                )
                record = result.single()
                logger.debug(
                    f"Created REQUIRES_SAFETY: {record['product']} -> {record['safety_equipment']}"
                )
                return True

        except Exception as e:
            logger.error(
                f"❌ Failed to create REQUIRES_SAFETY relationship "
                f"(product={product_id}, safety={safety_equipment_id}): {e}"
            )
            raise RuntimeError(f"Failed to create REQUIRES_SAFETY relationship between product {product_id} and safety equipment {safety_equipment_id}: {str(e)}") from e

    # =========================================================================
    # Recommendation Queries (For Hybrid AI Engine)
    # =========================================================================

    def get_products_for_task(
        self,
        task_id: str,
        necessity_filter: List[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get products recommended for a specific task

        Args:
            task_id: Task identifier
            necessity_filter: Filter by necessity ('required', 'recommended', 'optional')
            limit: Maximum number of results

        Returns:
            List of product dictionaries with recommendation details
        """
        try:
            necessity_clause = ""
            if necessity_filter:
                necessity_list = ", ".join([f"'{n}'" for n in necessity_filter])
                necessity_clause = f"AND r.necessity IN [{necessity_list}]"

            query = f"""
            MATCH (p:Product)-[r:USED_FOR]->(t:Task {{id: $task_id}})
            WHERE 1=1 {necessity_clause}
            OPTIONAL MATCH (p)-[rs:REQUIRES_SAFETY]->(se:SafetyEquipment)
            WITH p, r, collect({{
                safety_equipment: se.name,
                risk_level: rs.risk_level
            }}) as safety_requirements
            RETURN
                p.id as product_id,
                p.sku as sku,
                p.name as name,
                p.category as category,
                p.brand as brand,
                r.necessity as necessity,
                r.usage_notes as usage_notes,
                safety_requirements
            ORDER BY
                CASE r.necessity
                    WHEN 'required' THEN 1
                    WHEN 'recommended' THEN 2
                    ELSE 3
                END
            LIMIT $limit
            """

            with self.get_session() as session:
                result = session.run(query, task_id=task_id, limit=limit)
                products = [dict(record) for record in result]
                logger.debug(
                    f"Found {len(products)} products for task {task_id}"
                )
                return products

        except Exception as e:
            logger.error(f"❌ Failed to get products for task {task_id}: {e}")
            raise

    def get_compatible_products(
        self,
        product_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get products compatible with given product
        (For "frequently bought together" recommendations)

        Args:
            product_id: Product node ID
            limit: Maximum number of results

        Returns:
            List of compatible products
        """
        try:
            query = """
            MATCH (p1:Product {id: $product_id})-[:COMPATIBLE_WITH]->(p2:Product)
            RETURN
                p2.id as product_id,
                p2.sku as sku,
                p2.name as name,
                p2.category as category,
                p2.brand as brand
            LIMIT $limit
            """

            with self.get_session() as session:
                result = session.run(query, product_id=product_id, limit=limit)
                compatible = [dict(record) for record in result]
                logger.debug(
                    f"Found {len(compatible)} compatible products for {product_id}"
                )
                return compatible

        except Exception as e:
            logger.error(f"❌ Failed to get compatible products for {product_id}: {e}")
            raise

    def get_task_recommendations_for_products(
        self,
        product_ids: List[int],
        limit: int = 20
    ) -> List[Dict]:
        """
        Get task recommendations based on selected products
        (For "what can I do with these products?" feature)

        Args:
            product_ids: List of product IDs from customer cart/RFP
            limit: Maximum number of task recommendations

        Returns:
            List of recommended tasks with completion percentage
        """
        try:
            query = """
            MATCH (p:Product)-[r:USED_FOR]->(t:Task)
            WHERE p.id IN $product_ids
            WITH t,
                 count(DISTINCT p) as matched_products,
                 collect(DISTINCT {
                     product: p.name,
                     necessity: r.necessity
                 }) as products
            MATCH (all_p:Product)-[:USED_FOR]->(t)
            WITH t, matched_products, products, count(DISTINCT all_p) as total_products
            RETURN
                t.id as task_id,
                t.name as task_name,
                t.description as description,
                t.skill_level as skill_level,
                matched_products,
                total_products,
                round(100.0 * matched_products / total_products) as completion_percentage,
                products
            ORDER BY completion_percentage DESC, matched_products DESC
            LIMIT $limit
            """

            with self.get_session() as session:
                result = session.run(query, product_ids=product_ids, limit=limit)
                tasks = [dict(record) for record in result]
                logger.debug(
                    f"Found {len(tasks)} task recommendations for {len(product_ids)} products"
                )
                return tasks

        except Exception as e:
            logger.error(f"❌ Failed to get task recommendations: {e}")
            raise

    # =========================================================================
    # Safety Compliance Queries (OSHA/ANSI)
    # =========================================================================

    def get_safety_requirements_for_task(self, task_id: str) -> Dict[str, Any]:
        """
        Get safety equipment requirements for a task

        Args:
            task_id: Task identifier

        Returns:
            Dictionary with mandatory and recommended safety equipment
        """
        try:
            query = """
            MATCH (t:Task {id: $task_id})-[r:REQUIRES_SAFETY]->(se:SafetyEquipment)
            RETURN
                se.id as id,
                se.name as name,
                se.category as category,
                se.standard as standard,
                se.mandatory as mandatory,
                se.description as description,
                r.risk_level as risk_level
            ORDER BY se.mandatory DESC, r.risk_level DESC
            """

            with self.get_session() as session:
                result = session.run(query, task_id=task_id)
                safety_equipment = [dict(record) for record in result]

                mandatory = [eq for eq in safety_equipment if eq['mandatory']]
                recommended = [eq for eq in safety_equipment if not eq['mandatory']]

                return {
                    "task_id": task_id,
                    "mandatory_equipment": mandatory,
                    "recommended_equipment": recommended,
                    "total_requirements": len(safety_equipment)
                }

        except Exception as e:
            logger.error(f"❌ Failed to get safety requirements for {task_id}: {e}")
            raise RuntimeError(f"Failed to retrieve safety requirements for task {task_id}: {str(e)}") from e

    # =========================================================================
    # UNSPSC/ETIM Classification Integration (Phase 2)
    # =========================================================================

    def create_unspsc_node(
        self,
        unspsc_code: str,
        title: str,
        definition: str,
        segment: str,
        family: str,
        class_code: str,
        commodity: str,
        level: str
    ) -> bool:
        """
        Create UNSPSC classification node in Neo4j

        Args:
            unspsc_code: 8-digit UNSPSC code
            title: UNSPSC title
            definition: UNSPSC definition
            segment: Segment code (2 digits)
            family: Family code (4 digits)
            class_code: Class code (6 digits)
            commodity: Commodity code (8 digits)
            level: Classification level (segment, family, class, commodity)

        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
            MERGE (u:UNSPSCCode {code: $code})
            SET u.title = $title,
                u.definition = $definition,
                u.segment = $segment,
                u.family = $family,
                u.class_code = $class_code,
                u.commodity = $commodity,
                u.level = $level,
                u.updated_at = datetime()
            RETURN u.code as code
            """

            with self.get_session() as session:
                result = session.run(
                    query,
                    code=unspsc_code,
                    title=title,
                    definition=definition,
                    segment=segment,
                    family=family,
                    class_code=class_code,
                    commodity=commodity,
                    level=level
                )
                created_code = result.single()["code"]
                logger.debug(f"Created UNSPSC node: {created_code} - {title}")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to create UNSPSC node {unspsc_code}: {e}")
            raise RuntimeError(f"Failed to create UNSPSC node {unspsc_code}: {str(e)}") from e

    def create_etim_node(
        self,
        etim_class: str,
        etim_version: str,
        description_en: str,
        features: List[Dict[str, Any]] = None,
        parent_class: str = None
    ) -> bool:
        """
        Create ETIM classification node in Neo4j

        Args:
            etim_class: ETIM class code (e.g., "EC000001")
            etim_version: ETIM version (e.g., "9.0")
            description_en: English description
            features: List of feature dictionaries
            parent_class: Parent ETIM class (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
            MERGE (e:ETIMClass {class: $etim_class})
            SET e.version = $etim_version,
                e.description_en = $description_en,
                e.features = $features,
                e.parent_class = $parent_class,
                e.updated_at = datetime()
            RETURN e.class as class
            """

            with self.get_session() as session:
                result = session.run(
                    query,
                    etim_class=etim_class,
                    etim_version=etim_version,
                    description_en=description_en,
                    features=features or [],
                    parent_class=parent_class
                )
                created_class = result.single()["class"]
                logger.debug(f"Created ETIM node: {created_class}")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to create ETIM node {etim_class}: {e}")
            raise RuntimeError(f"Failed to create ETIM node {etim_class}: {str(e)}") from e

    def create_product_classified_as_unspsc(
        self,
        product_id: int,
        unspsc_code: str,
        confidence: float,
        classification_date: str = None
    ) -> bool:
        """
        Create CLASSIFIED_AS relationship between product and UNSPSC code

        Args:
            product_id: Product node ID
            unspsc_code: UNSPSC code
            confidence: Classification confidence score (0.0-1.0)
            classification_date: ISO format date (optional, defaults to now)

        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
            MATCH (p:Product {id: $product_id})
            MATCH (u:UNSPSCCode {code: $unspsc_code})
            MERGE (p)-[r:CLASSIFIED_AS_UNSPSC]->(u)
            SET r.confidence = $confidence,
                r.classification_date = $classification_date,
                r.updated_at = datetime()
            RETURN p.name as product, u.title as unspsc
            """

            if not classification_date:
                from datetime import datetime
                classification_date = datetime.now().isoformat()

            with self.get_session() as session:
                result = session.run(
                    query,
                    product_id=product_id,
                    unspsc_code=unspsc_code,
                    confidence=confidence,
                    classification_date=classification_date
                )
                record = result.single()
                logger.debug(
                    f"Created CLASSIFIED_AS_UNSPSC: {record['product']} -> {record['unspsc']}"
                )
                return True

        except Exception as e:
            logger.error(
                f"❌ Failed to create CLASSIFIED_AS_UNSPSC relationship "
                f"(product={product_id}, unspsc={unspsc_code}): {e}"
            )
            raise RuntimeError(f"Failed to create CLASSIFIED_AS_UNSPSC relationship for product {product_id}: {str(e)}") from e

    def create_product_classified_as_etim(
        self,
        product_id: int,
        etim_class: str,
        confidence: float,
        classification_date: str = None
    ) -> bool:
        """
        Create CLASSIFIED_AS relationship between product and ETIM class

        Args:
            product_id: Product node ID
            etim_class: ETIM class code
            confidence: Classification confidence score (0.0-1.0)
            classification_date: ISO format date (optional, defaults to now)

        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
            MATCH (p:Product {id: $product_id})
            MATCH (e:ETIMClass {class: $etim_class})
            MERGE (p)-[r:CLASSIFIED_AS_ETIM]->(e)
            SET r.confidence = $confidence,
                r.classification_date = $classification_date,
                r.updated_at = datetime()
            RETURN p.name as product, e.description_en as etim
            """

            if not classification_date:
                from datetime import datetime
                classification_date = datetime.now().isoformat()

            with self.get_session() as session:
                result = session.run(
                    query,
                    product_id=product_id,
                    etim_class=etim_class,
                    confidence=confidence,
                    classification_date=classification_date
                )
                record = result.single()
                logger.debug(
                    f"Created CLASSIFIED_AS_ETIM: {record['product']} -> {record['etim']}"
                )
                return True

        except Exception as e:
            logger.error(
                f"❌ Failed to create CLASSIFIED_AS_ETIM relationship "
                f"(product={product_id}, etim={etim_class}): {e}"
            )
            raise RuntimeError(f"Failed to create CLASSIFIED_AS_ETIM relationship for product {product_id}: {str(e)}") from e

    def get_products_by_unspsc_classification(
        self,
        unspsc_code: str,
        min_confidence: float = 0.7,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get products classified under a specific UNSPSC code

        Args:
            unspsc_code: UNSPSC code (full or partial)
            min_confidence: Minimum classification confidence
            limit: Maximum number of results

        Returns:
            List of products with classification details
        """
        try:
            # Use pattern matching for partial codes (e.g., segment or family level)
            query = """
            MATCH (p:Product)-[r:CLASSIFIED_AS_UNSPSC]->(u:UNSPSCCode)
            WHERE u.code STARTS WITH $unspsc_code
              AND r.confidence >= $min_confidence
            RETURN
                p.id as product_id,
                p.sku as sku,
                p.name as name,
                p.category as category,
                u.code as unspsc_code,
                u.title as unspsc_title,
                u.level as unspsc_level,
                r.confidence as classification_confidence,
                r.classification_date as classification_date
            ORDER BY r.confidence DESC
            LIMIT $limit
            """

            with self.get_session() as session:
                result = session.run(
                    query,
                    unspsc_code=unspsc_code,
                    min_confidence=min_confidence,
                    limit=limit
                )
                products = [dict(record) for record in result]
                logger.debug(
                    f"Found {len(products)} products classified under UNSPSC {unspsc_code}"
                )
                return products

        except Exception as e:
            logger.error(f"❌ Failed to get products by UNSPSC {unspsc_code}: {e}")
            raise

    def get_products_by_etim_classification(
        self,
        etim_class: str,
        min_confidence: float = 0.7,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get products classified under a specific ETIM class

        Args:
            etim_class: ETIM class code
            min_confidence: Minimum classification confidence
            limit: Maximum number of results

        Returns:
            List of products with classification details
        """
        try:
            query = """
            MATCH (p:Product)-[r:CLASSIFIED_AS_ETIM]->(e:ETIMClass {class: $etim_class})
            WHERE r.confidence >= $min_confidence
            RETURN
                p.id as product_id,
                p.sku as sku,
                p.name as name,
                p.category as category,
                e.class as etim_class,
                e.description_en as etim_description,
                e.features as etim_features,
                r.confidence as classification_confidence,
                r.classification_date as classification_date
            ORDER BY r.confidence DESC
            LIMIT $limit
            """

            with self.get_session() as session:
                result = session.run(
                    query,
                    etim_class=etim_class,
                    min_confidence=min_confidence,
                    limit=limit
                )
                products = [dict(record) for record in result]
                logger.debug(
                    f"Found {len(products)} products classified under ETIM {etim_class}"
                )
                return products

        except Exception as e:
            logger.error(f"❌ Failed to get products by ETIM {etim_class}: {e}")
            raise

    def sync_product_classifications(
        self,
        classifications: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Bulk sync product classifications to Neo4j knowledge graph

        Args:
            classifications: List of classification dictionaries with
                            product_id, unspsc_code, etim_class, confidence, etc.

        Returns:
            Tuple of (successful_count, failed_count)
        """
        successful = 0
        failed = 0

        try:
            for classification in classifications:
                product_id = classification.get('product_id')

                # Create UNSPSC relationship
                if classification.get('unspsc_code'):
                    success = self.create_product_classified_as_unspsc(
                        product_id=product_id,
                        unspsc_code=classification['unspsc_code'],
                        confidence=classification.get('unspsc_confidence', 0.0),
                        classification_date=classification.get('classification_date')
                    )
                    if success:
                        successful += 1
                    else:
                        failed += 1

                # Create ETIM relationship
                if classification.get('etim_class'):
                    success = self.create_product_classified_as_etim(
                        product_id=product_id,
                        etim_class=classification['etim_class'],
                        confidence=classification.get('etim_confidence', 0.0),
                        classification_date=classification.get('classification_date')
                    )
                    if success:
                        successful += 1
                    else:
                        failed += 1

            logger.info(
                f"✅ Synced {successful} product classifications to Neo4j "
                f"({failed} failed)"
            )
            return successful, failed

        except Exception as e:
            logger.error(f"❌ Bulk classification sync failed: {e}")
            raise RuntimeError(f"Bulk classification sync failed after {successful} successes and {failed} failures: {str(e)}") from e

    # =========================================================================
    # Performance and Utility Methods
    # =========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get knowledge graph statistics

        Returns:
            Dictionary with node counts, relationship counts, and performance metrics
        """
        try:
            with self.get_session() as session:
                # Node counts
                node_query = """
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
                """
                node_result = session.run(node_query)
                node_counts = {record["label"]: record["count"] for record in node_result}

                # Relationship counts
                rel_query = """
                MATCH ()-[r]->()
                RETURN type(r) as relationship, count(r) as count
                ORDER BY count DESC
                """
                rel_result = session.run(rel_query)
                rel_counts = {record["relationship"]: record["count"] for record in rel_result}

                return {
                    "status": "connected",
                    "node_counts": node_counts,
                    "relationship_counts": rel_counts,
                    "total_nodes": sum(node_counts.values()),
                    "total_relationships": sum(rel_counts.values())
                }

        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            raise RuntimeError(f"Failed to retrieve Neo4j statistics: {str(e)}") from e

    def close(self):
        """Close Neo4j driver connection"""
        if self.driver:
            self.driver.close()
            logger.info("✅ Neo4j connection closed")


# ============================================================================
# Global Knowledge Graph Instance
# ============================================================================

_kg_instance = None

def get_knowledge_graph(
    uri: str = None,
    user: str = None,
    password: str = None
) -> Neo4jKnowledgeGraph:
    """Get global Neo4j knowledge graph instance"""
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = Neo4jKnowledgeGraph(uri, user, password)
    return _kg_instance

def close_knowledge_graph():
    """Close global knowledge graph instance"""
    global _kg_instance
    if _kg_instance:
        _kg_instance.close()
        _kg_instance = None
