// Testing Infrastructure - Neo4j Knowledge Graph Initialization
// Creates knowledge graph structure for testing AI recommendations

// Create constraints for unique identifiers
CREATE CONSTRAINT tool_id_unique IF NOT EXISTS FOR (t:Tool) REQUIRE t.tool_id IS UNIQUE;
CREATE CONSTRAINT task_id_unique IF NOT EXISTS FOR (t:Task) REQUIRE t.task_id IS UNIQUE;
CREATE CONSTRAINT skill_id_unique IF NOT EXISTS FOR (s:Skill) REQUIRE s.skill_id IS UNIQUE;
CREATE CONSTRAINT safety_id_unique IF NOT EXISTS FOR (s:SafetyRequirement) REQUIRE s.safety_id IS UNIQUE;
CREATE CONSTRAINT material_id_unique IF NOT EXISTS FOR (m:Material) REQUIRE m.material_id IS UNIQUE;
CREATE CONSTRAINT process_id_unique IF NOT EXISTS FOR (p:Process) REQUIRE p.process_id IS UNIQUE;

// Create indexes for performance
CREATE INDEX tool_category_index IF NOT EXISTS FOR (t:Tool) ON (t.category);
CREATE INDEX task_complexity_index IF NOT EXISTS FOR (t:Task) ON (t.complexity);
CREATE INDEX skill_level_index IF NOT EXISTS FOR (s:Skill) ON (s.level);
CREATE INDEX safety_severity_index IF NOT EXISTS FOR (s:SafetyRequirement) ON (s.severity);

// Sample Tools
CREATE (:Tool {
    tool_id: "TOOL_00001",
    name: "Cordless Drill",
    category: "Power Tools",
    subcategory: "Drilling",
    power_rating: "18V",
    weight: "1.2kg",
    skill_level: "beginner",
    safety_rating: "medium",
    price_range: "budget",
    created_at: datetime()
});

CREATE (:Tool {
    tool_id: "TOOL_00002", 
    name: "Circular Saw",
    category: "Power Tools",
    subcategory: "Cutting",
    power_rating: "1400W",
    weight: "3.8kg",
    skill_level: "intermediate",
    safety_rating: "high",
    price_range: "premium",
    created_at: datetime()
});

CREATE (:Tool {
    tool_id: "TOOL_00003",
    name: "Digital Multimeter",
    category: "Measuring Tools",
    subcategory: "Electrical Testing",
    power_rating: "9V Battery",
    weight: "0.4kg",
    skill_level: "intermediate",
    safety_rating: "low",
    price_range: "mid-range",
    created_at: datetime()
});

CREATE (:Tool {
    tool_id: "TOOL_00004",
    name: "Safety Harness",
    category: "Safety Equipment",
    subcategory: "Fall Protection",
    power_rating: "N/A",
    weight: "1.1kg",
    skill_level: "beginner",
    safety_rating: "critical",
    price_range: "premium",
    created_at: datetime()
});

// Sample Tasks
CREATE (:Task {
    task_id: "TASK_00001",
    name: "Drill Pilot Holes",
    description: "Create precise pilot holes for screws",
    complexity: "beginner",
    estimated_time: "15min",
    environment: "indoor",
    precision_required: "medium",
    created_at: datetime()
});

CREATE (:Task {
    task_id: "TASK_00002",
    name: "Cut 2x4 Lumber",
    description: "Make precise crosscuts in dimensional lumber",
    complexity: "intermediate", 
    estimated_time: "30min",
    environment: "workshop",
    precision_required: "high",
    created_at: datetime()
});

CREATE (:Task {
    task_id: "TASK_00003",
    name: "Test Circuit Continuity",
    description: "Verify electrical circuit integrity",
    complexity: "intermediate",
    estimated_time: "10min", 
    environment: "electrical_panel",
    precision_required: "critical",
    created_at: datetime()
});

CREATE (:Task {
    task_id: "TASK_00004",
    name: "Work at Height",
    description: "Perform tasks above 6 feet elevation",
    complexity: "advanced",
    estimated_time: "varies",
    environment: "outdoor",
    precision_required: "critical",
    created_at: datetime()
});

// Sample Skills
CREATE (:Skill {
    skill_id: "SKILL_00001",
    name: "Basic Drilling",
    level: "beginner",
    category: "Power Tool Operation",
    description: "Understanding drill bits, speed, and pressure",
    certification_required: false,
    created_at: datetime()
});

CREATE (:Skill {
    skill_id: "SKILL_00002",
    name: "Precision Cutting",
    level: "intermediate",
    category: "Woodworking",
    description: "Accurate measurement and cutting techniques",
    certification_required: false,
    created_at: datetime()
});

CREATE (:Skill {
    skill_id: "SKILL_00003",
    name: "Electrical Testing",
    level: "intermediate",
    category: "Electrical Work",
    description: "Safe use of electrical testing equipment",
    certification_required: true,
    created_at: datetime()
});

CREATE (:Skill {
    skill_id: "SKILL_00004",
    name: "Fall Protection",
    level: "advanced",
    category: "Safety",
    description: "Proper use of fall protection equipment",
    certification_required: true,
    created_at: datetime()
});

// Sample Safety Requirements
CREATE (:SafetyRequirement {
    safety_id: "SAFETY_00001",
    name: "Eye Protection Required",
    standard: "ANSI Z87.1",
    severity: "high",
    description: "Safety glasses or goggles must be worn",
    mandatory: true,
    applicable_environments: ["workshop", "construction"],
    created_at: datetime()
});

CREATE (:SafetyRequirement {
    safety_id: "SAFETY_00002", 
    name: "Electrical Lockout/Tagout",
    standard: "OSHA 1910.147",
    severity: "critical",
    description: "Power must be locked out before electrical work",
    mandatory: true,
    applicable_environments: ["electrical_panel", "industrial"],
    created_at: datetime()
});

CREATE (:SafetyRequirement {
    safety_id: "SAFETY_00003",
    name: "Fall Protection System",
    standard: "OSHA 1926.501",
    severity: "critical", 
    description: "Fall protection required above 6 feet",
    mandatory: true,
    applicable_environments: ["outdoor", "construction", "roofing"],
    created_at: datetime()
});

// Sample Materials
CREATE (:Material {
    material_id: "MATERIAL_00001",
    name: "Pine 2x4 Lumber",
    category: "Wood",
    properties: {
        density: "medium",
        hardness: "soft",
        moisture_content: "kiln_dried"
    },
    common_applications: ["framing", "construction", "furniture"],
    created_at: datetime()
});

CREATE (:Material {
    material_id: "MATERIAL_00002",
    name: "12 AWG Copper Wire",
    category: "Electrical",
    properties: {
        conductivity: "high",
        ampacity: "20A",
        insulation: "THHN"
    },
    common_applications: ["residential_wiring", "appliance_circuits"],
    created_at: datetime()
});

// Sample Processes
CREATE (:Process {
    process_id: "PROCESS_00001",
    name: "Cabinet Installation",
    category: "Installation",
    steps: [
        "Measure and mark positions",
        "Drill pilot holes", 
        "Mount brackets",
        "Hang cabinets",
        "Adjust and level"
    ],
    estimated_duration: "4 hours",
    skill_level_required: "intermediate",
    created_at: datetime()
});

// Create relationships between entities

// Tool-Task relationships (USED_FOR)
MATCH (t:Tool {tool_id: "TOOL_00001"}), (task:Task {task_id: "TASK_00001"})
CREATE (t)-[:USED_FOR {confidence: 0.95, primary_use: true}]->(task);

MATCH (t:Tool {tool_id: "TOOL_00002"}), (task:Task {task_id: "TASK_00002"})
CREATE (t)-[:USED_FOR {confidence: 0.98, primary_use: true}]->(task);

MATCH (t:Tool {tool_id: "TOOL_00003"}), (task:Task {task_id: "TASK_00003"})
CREATE (t)-[:USED_FOR {confidence: 0.99, primary_use: true}]->(task);

MATCH (t:Tool {tool_id: "TOOL_00004"}), (task:Task {task_id: "TASK_00004"})
CREATE (t)-[:USED_FOR {confidence: 1.0, primary_use: true}]->(task);

// Task-Skill relationships (REQUIRES)
MATCH (task:Task {task_id: "TASK_00001"}), (s:Skill {skill_id: "SKILL_00001"})
CREATE (task)-[:REQUIRES {proficiency_level: "basic", mandatory: true}]->(s);

MATCH (task:Task {task_id: "TASK_00002"}), (s:Skill {skill_id: "SKILL_00002"})
CREATE (task)-[:REQUIRES {proficiency_level: "intermediate", mandatory: true}]->(s);

MATCH (task:Task {task_id: "TASK_00003"}), (s:Skill {skill_id: "SKILL_00003"})
CREATE (task)-[:REQUIRES {proficiency_level: "intermediate", mandatory: true}]->(s);

MATCH (task:Task {task_id: "TASK_00004"}), (s:Skill {skill_id: "SKILL_00004"})
CREATE (task)-[:REQUIRES {proficiency_level: "advanced", mandatory: true}]->(s);

// Task-Safety relationships (REQUIRES)
MATCH (task:Task {task_id: "TASK_00001"}), (s:SafetyRequirement {safety_id: "SAFETY_00001"})
CREATE (task)-[:REQUIRES {enforcement_level: "mandatory"}]->(s);

MATCH (task:Task {task_id: "TASK_00002"}), (s:SafetyRequirement {safety_id: "SAFETY_00001"})
CREATE (task)-[:REQUIRES {enforcement_level: "mandatory"}]->(s);

MATCH (task:Task {task_id: "TASK_00003"}), (s:SafetyRequirement {safety_id: "SAFETY_00002"})
CREATE (task)-[:REQUIRES {enforcement_level: "critical"}]->(s);

MATCH (task:Task {task_id: "TASK_00004"}), (s:SafetyRequirement {safety_id: "SAFETY_00003"})
CREATE (task)-[:REQUIRES {enforcement_level: "critical"}]->(s);

// Tool-Material relationships (COMPATIBLE_WITH)
MATCH (t:Tool {tool_id: "TOOL_00001"}), (m:Material {material_id: "MATERIAL_00001"})
CREATE (t)-[:COMPATIBLE_WITH {efficiency: "high", recommended: true}]->(m);

MATCH (t:Tool {tool_id: "TOOL_00002"}), (m:Material {material_id: "MATERIAL_00001"})
CREATE (t)-[:COMPATIBLE_WITH {efficiency: "excellent", recommended: true}]->(m);

MATCH (t:Tool {tool_id: "TOOL_00003"}), (m:Material {material_id: "MATERIAL_00002"})
CREATE (t)-[:COMPATIBLE_WITH {efficiency: "excellent", recommended: true}]->(m);

// Process-Task relationships (INCLUDES)
MATCH (p:Process {process_id: "PROCESS_00001"}), (task:Task {task_id: "TASK_00001"})
CREATE (p)-[:INCLUDES {sequence_order: 2, optional: false}]->(task);

// Create similarity relationships (SIMILAR_TO) for recommendation engine
MATCH (t1:Tool {category: "Power Tools"}), (t2:Tool {category: "Power Tools"})
WHERE t1 <> t2
CREATE (t1)-[:SIMILAR_TO {similarity_score: 0.7, basis: "category"}]->(t2);

// Create procedural functions for testing
// Function to find tools for a task
CREATE OR REPLACE FUNCTION findToolsForTask(taskId: String) {
    MATCH (task:Task {task_id: $taskId})<-[:USED_FOR]-(tool:Tool)
    RETURN tool.name as tool_name, tool.category as category, tool.skill_level as required_skill
}

// Function to get safety requirements for a task  
CREATE OR REPLACE FUNCTION getSafetyRequirements(taskId: String) {
    MATCH (task:Task {task_id: $taskId})-[:REQUIRES]->(safety:SafetyRequirement)
    RETURN safety.name as requirement, safety.standard as standard, safety.severity as severity
}

// Function to recommend similar tools
CREATE OR REPLACE FUNCTION recommendSimilarTools(toolId: String, limit: Integer = 5) {
    MATCH (tool:Tool {tool_id: $toolId})-[:SIMILAR_TO]-(similar:Tool)
    RETURN similar.name as tool_name, similar.category as category, similar.price_range as price
    LIMIT $limit
}

// Create sample data for performance testing
UNWIND range(1, 100) AS i
CREATE (:Tool {
    tool_id: "PERF_TOOL_" + toString(i),
    name: "Performance Test Tool " + toString(i),
    category: ["Power Tools", "Hand Tools", "Measuring Tools"][i % 3],
    skill_level: ["beginner", "intermediate", "advanced"][i % 3],
    safety_rating: ["low", "medium", "high"][i % 3],
    created_at: datetime()
});

UNWIND range(1, 100) AS i  
CREATE (:Task {
    task_id: "PERF_TASK_" + toString(i),
    name: "Performance Test Task " + toString(i),
    complexity: ["beginner", "intermediate", "advanced"][i % 3],
    estimated_time: toString((i % 60) + 10) + "min",
    created_at: datetime()
});

// Create random relationships for performance testing
MATCH (t:Tool), (task:Task)
WHERE t.tool_id STARTS WITH "PERF_TOOL_" AND task.task_id STARTS WITH "PERF_TASK_"
WITH t, task, rand() as r
WHERE r < 0.3
CREATE (t)-[:USED_FOR {confidence: r, test_data: true}]->(task);