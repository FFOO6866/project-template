# AI-001: Custom Classification Workflows

**Created:** 2025-08-02  
**Assigned:** Pattern Expert + Core SDK Specialist  
**Priority:** 🚀 P1 - HIGH  
**Status:** PENDING  
**Estimated Effort:** 16 hours  
**Due Date:** 2025-08-09 (Week 3 - Platform Integration Phase)

## Description

Implement Core SDK workflows for specialized HVAC, electrical, and tool classification that go beyond standard UNSPSC/ETIM categorization. These custom workflows leverage domain-specific knowledge, safety requirements, and compatibility matrices to provide intelligent classification for complex hardware scenarios.

## Strategic Context

While UNSPSC/ETIM provides standardized classification, many industrial applications require specialized workflows that understand:
- **HVAC Systems**: Compatibility matrices, efficiency ratings, sizing requirements
- **Electrical Components**: Voltage compatibility, safety ratings, code compliance
- **Tool Classification**: Project suitability, skill level requirements, safety considerations

These custom workflows use the Core SDK's flexible node system to create domain-specific classification logic.

## Acceptance Criteria

- [ ] HVAC classification workflow with compatibility and sizing logic
- [ ] Electrical component classification with safety and code compliance checking
- [ ] Tool classification workflow with project suitability and skill level analysis
- [ ] Safety compliance integration across all classification workflows
- [ ] Custom node implementations for domain-specific logic
- [ ] Workflow composition and orchestration using WorkflowBuilder
- [ ] Integration with Nexus platform for multi-channel access
- [ ] Performance optimization for <2s classification response times
- [ ] Comprehensive testing with real product data

## Subtasks

- [ ] HVAC Classification Workflow Implementation (Est: 5h)
  - Verification: HVAC products correctly classified with compatibility and sizing data
  - Output: Complete HVAC workflow with efficiency ratings and system integration logic

- [ ] Electrical Classification Workflow Implementation (Est: 5h)
  - Verification: Electrical components classified with safety ratings and code compliance
  - Output: Electrical workflow with voltage compatibility and safety validation

- [ ] Tool Classification Workflow Implementation (Est: 3h)
  - Verification: Tools classified by project type, skill level, and safety requirements
  - Output: Tool workflow with project suitability scoring and safety analysis

- [ ] Custom Node Development (Est: 2h)
  - Verification: Domain-specific nodes registered and working in workflow system
  - Output: Reusable nodes for specialized classification logic

- [ ] Workflow Integration and Testing (Est: 1h)
  - Verification: All workflows accessible through Nexus platform and performing optimally
  - Output: Integrated classification system with comprehensive test coverage

## Dependencies

- **FOUND-001**: SDK Compliance Foundation (workflow execution patterns)
- **DATA-001**: UNSPSC/ETIM Integration (base classification data)
- **NEXUS-001**: Multi-Channel Platform Setup (workflow deployment platform)

## Risk Assessment

- **HIGH**: Complex domain logic may require extensive validation and testing
- **MEDIUM**: Performance requirements may conflict with comprehensive analysis depth
- **MEDIUM**: Integration with existing UNSPSC/ETIM data may require careful coordination
- **LOW**: Custom node registration may need refinement for optimal workflow composition

## Technical Implementation Plan

### Phase 3C-1: HVAC Classification Workflow (Hours 1-5)
```python
# hvac_classification_workflow.py
from kailash.workflow.builder import WorkflowBuilder
from kailash.nodes.base import BaseNode
from kailash.nodes.core import DataProcessingNode, ValidationNode
from typing import Dict, List, Any

class HVACCompatibilityNode(BaseNode):
    """Custom node for HVAC system compatibility analysis"""
    
    def __init__(self, node_id: str):
        super().__init__(node_id)
        self.required_inputs = ["product_data", "system_requirements"]
        self.outputs = ["compatibility_score", "compatibility_issues", "recommendations"]
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze HVAC compatibility and sizing requirements"""
        
        product_data = inputs["product_data"]
        system_requirements = inputs.get("system_requirements", {})
        
        # Analyze BTU capacity compatibility
        btu_compatibility = self._analyze_btu_compatibility(
            product_data, system_requirements
        )
        
        # Check refrigerant compatibility
        refrigerant_compatibility = self._check_refrigerant_compatibility(
            product_data, system_requirements
        )
        
        # Evaluate efficiency ratings
        efficiency_analysis = self._evaluate_efficiency_ratings(
            product_data, system_requirements
        )
        
        # Check dimensional constraints
        dimensional_fit = self._check_dimensional_constraints(
            product_data, system_requirements
        )
        
        compatibility_score = self._calculate_compatibility_score([
            btu_compatibility, refrigerant_compatibility,
            efficiency_analysis, dimensional_fit
        ])
        
        return {
            "compatibility_score": compatibility_score,
            "compatibility_issues": self._identify_issues([
                btu_compatibility, refrigerant_compatibility,
                efficiency_analysis, dimensional_fit
            ]),
            "recommendations": self._generate_recommendations(
                product_data, system_requirements, compatibility_score
            )
        }
    
    def _analyze_btu_compatibility(self, product_data: Dict, requirements: Dict) -> Dict:
        """Analyze BTU capacity requirements"""
        product_btu = product_data.get("btu_capacity", 0)
        required_btu = requirements.get("btu_requirement", 0)
        
        if required_btu == 0:
            return {"status": "no_requirement", "score": 0.5}
        
        ratio = product_btu / required_btu
        
        if 0.95 <= ratio <= 1.15:  # Within 15% is good
            return {"status": "excellent", "score": 1.0, "ratio": ratio}
        elif 0.85 <= ratio <= 1.25:  # Within 25% is acceptable
            return {"status": "acceptable", "score": 0.7, "ratio": ratio}
        else:
            return {"status": "poor", "score": 0.2, "ratio": ratio}
    
    def _check_refrigerant_compatibility(self, product_data: Dict, requirements: Dict) -> Dict:
        """Check refrigerant type compatibility"""
        product_refrigerant = product_data.get("refrigerant_type", "").upper()
        required_refrigerant = requirements.get("refrigerant_type", "").upper()
        
        if not required_refrigerant:
            return {"status": "no_requirement", "score": 0.5}
        
        if product_refrigerant == required_refrigerant:
            return {"status": "compatible", "score": 1.0}
        
        # Check for compatible alternatives
        compatible_alternatives = {
            "R-410A": ["R-32", "R-454B"],
            "R-22": ["R-407C", "R-422D"],
            "R-134A": ["R-1234YF", "R-513A"]
        }
        
        if product_refrigerant in compatible_alternatives.get(required_refrigerant, []):
            return {"status": "alternative_compatible", "score": 0.8}
        
        return {"status": "incompatible", "score": 0.0}

class HVACEfficiencyNode(BaseNode):
    """Custom node for HVAC efficiency analysis"""
    
    def __init__(self, node_id: str):
        super().__init__(node_id)
        self.required_inputs = ["product_data", "efficiency_requirements"]
        self.outputs = ["efficiency_rating", "energy_savings", "compliance_status"]
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze HVAC efficiency ratings and compliance"""
        
        product_data = inputs["product_data"]
        requirements = inputs.get("efficiency_requirements", {})
        
        # Analyze SEER ratings
        seer_analysis = self._analyze_seer_rating(product_data, requirements)
        
        # Calculate energy savings
        energy_savings = self._calculate_energy_savings(product_data, requirements)
        
        # Check compliance with standards
        compliance_status = self._check_efficiency_compliance(product_data)
        
        return {
            "efficiency_rating": seer_analysis,
            "energy_savings": energy_savings,
            "compliance_status": compliance_status
        }

class HVACClassificationWorkflow:
    """Complete HVAC classification workflow implementation"""
    
    def __init__(self):
        self.workflow = WorkflowBuilder()
        self._setup_workflow()
    
    def _setup_workflow(self):
        """Setup HVAC classification workflow"""
        
        # Standard UNSPSC classification
        self.workflow.add_node(
            "UNSPSCClassificationNode", "unspsc_classify",
            {"classification_system": "UNSPSC", "domain": "HVAC"}
        )
        
        # ETIM classification
        self.workflow.add_node(
            "ETIMClassificationNode", "etim_classify", 
            {"classification_system": "ETIM", "domain": "HVAC"}
        )
        
        # Custom HVAC compatibility analysis
        self.workflow.add_node(
            HVACCompatibilityNode, "hvac_compatibility", {}
        )
        
        # HVAC efficiency analysis
        self.workflow.add_node(
            HVACEfficiencyNode, "hvac_efficiency", {}
        )
        
        # Safety compliance checking
        self.workflow.add_node(
            "SafetyComplianceNode", "safety_check",
            {"standards": ["OSHA", "NFPA", "UL"], "domain": "HVAC"}
        )
        
        # Results aggregation
        self.workflow.add_node(
            "ResultsAggregationNode", "aggregate_results",
            {"output_format": "comprehensive_hvac_classification"}
        )
        
        # Setup workflow connections
        self._setup_workflow_connections()
    
    def _setup_workflow_connections(self):
        """Setup data flow between workflow nodes"""
        
        # Input data flows to all classification nodes
        self.workflow.connect("INPUT", "unspsc_classify", "product_data")
        self.workflow.connect("INPUT", "etim_classify", "product_data")
        self.workflow.connect("INPUT", "hvac_compatibility", "product_data")
        self.workflow.connect("INPUT", "hvac_efficiency", "product_data")
        self.workflow.connect("INPUT", "safety_check", "product_data")
        
        # All results flow to aggregation
        self.workflow.connect("unspsc_classify", "aggregate_results", "unspsc_classification")
        self.workflow.connect("etim_classify", "aggregate_results", "etim_classification")
        self.workflow.connect("hvac_compatibility", "aggregate_results", "compatibility_analysis")
        self.workflow.connect("hvac_efficiency", "aggregate_results", "efficiency_analysis")
        self.workflow.connect("safety_check", "aggregate_results", "safety_compliance")
    
    def classify_hvac_product(self, product_data: Dict[str, Any], 
                            system_requirements: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute HVAC classification workflow"""
        
        from kailash.runtime.local import LocalRuntime
        
        runtime = LocalRuntime()
        
        workflow_input = {
            "product_data": product_data,
            "system_requirements": system_requirements or {},
            "efficiency_requirements": system_requirements.get("efficiency_requirements", {}) if system_requirements else {}
        }
        
        results, run_id = runtime.execute(self.workflow.build(), workflow_input)
        
        return {
            "run_id": run_id,
            "classification_results": results,
            "workflow_type": "hvac_classification"
        }
```

### Phase 3C-2: Electrical Classification Workflow (Hours 6-10)
```python
# electrical_classification_workflow.py
from kailash.workflow.builder import WorkflowBuilder
from kailash.nodes.base import BaseNode
from typing import Dict, List, Any

class ElectricalSafetyNode(BaseNode):
    """Custom node for electrical safety and code compliance analysis"""
    
    def __init__(self, node_id: str):
        super().__init__(node_id)
        self.required_inputs = ["product_data", "installation_context"]
        self.outputs = ["safety_rating", "code_compliance", "voltage_compatibility"]
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze electrical safety and compliance requirements"""
        
        product_data = inputs["product_data"]
        installation_context = inputs.get("installation_context", {})
        
        # Analyze voltage compatibility
        voltage_analysis = self._analyze_voltage_compatibility(
            product_data, installation_context
        )
        
        # Check amperage requirements
        amperage_analysis = self._check_amperage_requirements(
            product_data, installation_context
        )
        
        # Validate safety ratings
        safety_rating = self._validate_safety_ratings(product_data)
        
        # Check code compliance
        code_compliance = self._check_electrical_code_compliance(
            product_data, installation_context
        )
        
        return {
            "safety_rating": safety_rating,
            "code_compliance": code_compliance,
            "voltage_compatibility": voltage_analysis,
            "amperage_analysis": amperage_analysis
        }
    
    def _analyze_voltage_compatibility(self, product_data: Dict, context: Dict) -> Dict:
        """Analyze voltage compatibility for installation"""
        product_voltage = product_data.get("voltage_rating", {})
        required_voltage = context.get("supply_voltage", {})
        
        if not required_voltage:
            return {"status": "no_requirement", "compatibility": True}
        
        # Check voltage range compatibility
        product_min = product_voltage.get("min", 0)
        product_max = product_voltage.get("max", 0)
        supply_voltage = required_voltage.get("nominal", 0)
        
        if product_min <= supply_voltage <= product_max:
            return {
                "status": "compatible",
                "compatibility": True,
                "voltage_margin": min(supply_voltage - product_min, product_max - supply_voltage)
            }
        
        return {
            "status": "incompatible",
            "compatibility": False,
            "required_voltage": supply_voltage,
            "product_range": f"{product_min}-{product_max}V"
        }

class ElectricalClassificationWorkflow:
    """Complete electrical component classification workflow"""
    
    def __init__(self):
        self.workflow = WorkflowBuilder()
        self._setup_workflow()
    
    def _setup_workflow(self):
        """Setup electrical classification workflow"""
        
        # Standard classifications
        self.workflow.add_node(
            "UNSPSCClassificationNode", "unspsc_classify",
            {"classification_system": "UNSPSC", "domain": "Electrical"}
        )
        
        self.workflow.add_node(
            "ETIMClassificationNode", "etim_classify",
            {"classification_system": "ETIM", "domain": "Electrical"}
        )
        
        # Custom electrical safety analysis
        self.workflow.add_node(
            ElectricalSafetyNode, "electrical_safety", {}
        )
        
        # Electrical code compliance
        self.workflow.add_node(
            "CodeComplianceNode", "code_compliance",
            {"codes": ["NEC", "IEC", "UL"], "domain": "Electrical"}
        )
        
        # Results aggregation
        self.workflow.add_node(
            "ResultsAggregationNode", "aggregate_results",
            {"output_format": "comprehensive_electrical_classification"}
        )
        
        self._setup_workflow_connections()
    
    def classify_electrical_component(self, product_data: Dict[str, Any],
                                    installation_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute electrical classification workflow"""
        
        from kailash.runtime.local import LocalRuntime
        
        runtime = LocalRuntime()
        
        workflow_input = {
            "product_data": product_data,
            "installation_context": installation_context or {}
        }
        
        results, run_id = runtime.execute(self.workflow.build(), workflow_input)
        
        return {
            "run_id": run_id,
            "classification_results": results,
            "workflow_type": "electrical_classification"
        }
```

### Phase 3C-3: Tool Classification Workflow (Hours 11-13)
```python
# tool_classification_workflow.py
from kailash.workflow.builder import WorkflowBuilder
from kailash.nodes.base import BaseNode
from typing import Dict, List, Any

class ToolSuitabilityNode(BaseNode):
    """Custom node for tool project suitability analysis"""
    
    def __init__(self, node_id: str):
        super().__init__(node_id)
        self.required_inputs = ["product_data", "project_context"]
        self.outputs = ["project_suitability", "skill_level_requirements", "safety_considerations"]
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze tool suitability for specific projects"""
        
        product_data = inputs["product_data"]
        project_context = inputs.get("project_context", {})
        
        # Analyze project suitability
        project_suitability = self._analyze_project_suitability(
            product_data, project_context
        )
        
        # Determine skill level requirements
        skill_requirements = self._determine_skill_level_requirements(product_data)
        
        # Assess safety considerations
        safety_considerations = self._assess_safety_considerations(
            product_data, project_context
        )
        
        return {
            "project_suitability": project_suitability,
            "skill_level_requirements": skill_requirements,
            "safety_considerations": safety_considerations
        }

class ToolClassificationWorkflow:
    """Complete tool classification workflow implementation"""
    
    def __init__(self):
        self.workflow = WorkflowBuilder()
        self._setup_workflow()
    
    def _setup_workflow(self):
        """Setup tool classification workflow"""
        
        # Standard classifications
        self.workflow.add_node(
            "UNSPSCClassificationNode", "unspsc_classify",
            {"classification_system": "UNSPSC", "domain": "Tools"}
        )
        
        self.workflow.add_node(
            "ETIMClassificationNode", "etim_classify",
            {"classification_system": "ETIM", "domain": "Tools"}
        )
        
        # Custom tool suitability analysis
        self.workflow.add_node(
            ToolSuitabilityNode, "tool_suitability", {}
        )
        
        # Safety analysis
        self.workflow.add_node(
            "SafetyComplianceNode", "safety_analysis",
            {"standards": ["OSHA", "ANSI"], "domain": "Tools"}
        )
        
        # Results aggregation
        self.workflow.add_node(
            "ResultsAggregationNode", "aggregate_results",
            {"output_format": "comprehensive_tool_classification"}
        )
        
        self._setup_workflow_connections()
    
    def classify_tool(self, product_data: Dict[str, Any],
                     project_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute tool classification workflow"""
        
        from kailash.runtime.local import LocalRuntime
        
        runtime = LocalRuntime()
        
        workflow_input = {
            "product_data": product_data,
            "project_context": project_context or {}
        }
        
        results, run_id = runtime.execute(self.workflow.build(), workflow_input)
        
        return {
            "run_id": run_id,
            "classification_results": results,
            "workflow_type": "tool_classification"
        }
```

## Testing Requirements

### Unit Tests (Critical Priority)
- [ ] Custom node functionality and parameter validation
- [ ] Workflow composition and execution logic
- [ ] Domain-specific classification accuracy
- [ ] Safety compliance validation

### Integration Tests (High Priority)
- [ ] Integration with UNSPSC/ETIM base classification data
- [ ] Nexus platform workflow registration and execution
- [ ] Performance testing with realistic product datasets
- [ ] Cross-workflow compatibility and consistency

### End-to-End Tests (Medium Priority)
- [ ] Complete classification workflows through Nexus platform
- [ ] Multi-channel access testing (API, CLI, MCP)
- [ ] Real-world product classification accuracy validation
- [ ] Performance benchmarking under concurrent load

## Definition of Done

- [ ] All acceptance criteria met and verified
- [ ] HVAC, electrical, and tool classification workflows implemented and tested
- [ ] Custom nodes registered and functioning in workflow system
- [ ] Integration with Nexus platform complete and operational
- [ ] Performance targets met (<2s response time)
- [ ] Comprehensive testing suite passing
- [ ] Documentation updated with workflow usage examples
- [ ] Safety compliance validation integrated across all workflows

## Progress Tracking

**Phase 3C-1 (Hours 1-5):** [ ] HVAC classification workflow implementation  
**Phase 3C-2 (Hours 6-10):** [ ] Electrical classification workflow implementation  
**Phase 3C-3 (Hours 11-13):** [ ] Tool classification workflow implementation  
**Phase 3C-4 (Hours 14-15):** [ ] Custom node development and registration  
**Phase 3C-5 (Hour 16):** [ ] Workflow integration testing and validation  

## Success Metrics

- **Classification Accuracy**: >95% accuracy for domain-specific classifications
- **Performance**: <2s response time for all classification workflows
- **Safety Compliance**: 100% safety standard validation coverage
- **Workflow Reliability**: 99.9% successful workflow execution rate
- **Integration Success**: 100% compatibility with Nexus multi-channel platform

## Next Actions After Completion

1. **AI-002**: Hybrid Recommendation Engine (uses classification results)
2. **FE-006**: Real-Time Chat Interface (integrates classification workflows)
3. **AI-003**: Safety Compliance AI (extends safety analysis capabilities)

These custom workflows provide the specialized intelligence needed for industry-specific hardware classification beyond standard categorization systems.