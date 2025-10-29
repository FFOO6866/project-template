"""
DIY Project Database Module for Horme Product Knowledge Enhancement.

This module provides comprehensive DIY project knowledge that enriches basic product data with:
1. Common home improvement projects and their requirements
2. Required tools and materials per project
3. Skill levels and time estimates
4. Step-by-step instructions and procedures
5. Common mistakes and expert tips
6. Seasonal considerations and project planning

Architecture:
- Built on Kailash Core SDK for workflow integration
- Structured project taxonomy with hierarchical categories
- Rich metadata for intelligent product recommendations
- Integration with existing product database through SKU matching
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

# Kailash SDK imports
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime


class SkillLevel(Enum):
    """DIY skill level classifications."""
    BEGINNER = "beginner"           # No experience required, basic tools
    INTERMEDIATE = "intermediate"   # Some experience, standard tools
    ADVANCED = "advanced"          # Significant experience, specialized tools
    EXPERT = "expert"              # Professional level, complex tools/techniques


class ProjectCategory(Enum):
    """DIY project categories."""
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    CARPENTRY = "carpentry"
    PAINTING = "painting"
    FLOORING = "flooring"
    ROOFING = "roofing"
    LANDSCAPING = "landscaping"
    HVAC = "hvac"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    OUTDOOR = "outdoor"
    STORAGE = "storage"
    INSULATION = "insulation"
    DRYWALL = "drywall"
    TILING = "tiling"


class ProjectComplexity(Enum):
    """Project complexity levels."""
    SIMPLE = "simple"           # 1-2 hours, few tools
    MODERATE = "moderate"       # Half day, multiple tools
    COMPLEX = "complex"         # Full day or weekend, many tools
    MAJOR = "major"            # Multiple days/weeks, professional tools


class Season(Enum):
    """Seasonal project recommendations."""
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"
    ANY = "any"


@dataclass
class ToolRequirement:
    """Individual tool requirement for a project."""
    name: str
    category: str  # hand_tool, power_tool, specialty_tool, safety_equipment
    required: bool = True  # vs optional/nice-to-have
    rental_option: bool = False
    approximate_cost: Optional[float] = None
    alternatives: List[str] = field(default_factory=list)
    skill_notes: str = ""


@dataclass
class MaterialRequirement:
    """Individual material requirement for a project."""
    name: str
    category: str  # lumber, hardware, consumables, finishing
    quantity: str  # "2x4x8 lumber (6 pieces)", "1 gallon", etc.
    unit_cost_range: Tuple[float, float] = (0.0, 0.0)  # (min, max)
    quality_tiers: List[str] = field(default_factory=list)  # basic, premium, professional
    where_to_buy: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)


@dataclass
class ProjectStep:
    """Individual step in a DIY project."""
    step_number: int
    title: str
    description: str
    estimated_time: str  # "30 minutes", "2 hours"
    tools_needed: List[str]
    materials_needed: List[str]
    safety_notes: List[str] = field(default_factory=list)
    common_mistakes: List[str] = field(default_factory=list)
    pro_tips: List[str] = field(default_factory=list)
    difficulty_within_project: SkillLevel = SkillLevel.BEGINNER
    images_needed: List[str] = field(default_factory=list)  # Types of visual aids needed


@dataclass
class SafetyConsideration:
    """Safety information for DIY projects."""
    hazard_type: str  # electrical, chemical, physical, respiratory
    risk_level: str  # low, medium, high, extreme
    safety_equipment: List[str]
    precautions: List[str]
    when_to_call_professional: List[str]


@dataclass
class CommonMistake:
    """Common mistakes in DIY projects and how to avoid them."""
    mistake: str
    why_it_happens: str
    how_to_avoid: str
    how_to_fix: str
    cost_impact: str  # low, medium, high


@dataclass
class DIYProject:
    """Complete DIY project definition."""
    
    # Basic Information
    project_id: str
    name: str
    category: ProjectCategory
    subcategory: str  # "bathroom faucet", "deck staining", etc.
    description: str
    
    # Project Characteristics
    skill_level: SkillLevel
    complexity: ProjectComplexity
    estimated_time: str  # "2-4 hours", "1-2 days"
    estimated_cost_range: Tuple[float, float]  # (min, max) total project cost
    
    # Requirements
    tools_required: List[ToolRequirement]
    materials_required: List[MaterialRequirement]
    
    # Instructions
    steps: List[ProjectStep]
    
    # Knowledge
    safety_considerations: List[SafetyConsideration]
    common_mistakes: List[CommonMistake]
    pro_tips: List[str]
    
    # Planning
    best_seasons: List[Season]
    prerequisites: List[str]  # Other projects that should be done first
    leads_to: List[str]  # Follow-up projects this enables
    
    # Metadata
    popularity_score: float = 0.0  # 0-100 based on search/forum activity
    success_rate: float = 0.0  # 0-100 typical DIY success rate
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Integration
    related_products: List[str] = field(default_factory=list)  # SKUs of related products
    alternative_approaches: List[str] = field(default_factory=list)
    professional_alternative: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary for serialization."""
        return asdict(self)
    
    def get_total_tool_cost_range(self) -> Tuple[float, float]:
        """Calculate total cost range for all required tools."""
        min_cost = sum(tool.approximate_cost or 0 for tool in self.tools_required if tool.required)
        max_cost = sum(tool.approximate_cost or 0 for tool in self.tools_required if tool.approximate_cost)
        return (min_cost, max_cost)
    
    def get_rental_tools(self) -> List[ToolRequirement]:
        """Get list of tools that can be rented instead of purchased."""
        return [tool for tool in self.tools_required if tool.rental_option]
    
    def get_project_difficulty_breakdown(self) -> Dict[str, int]:
        """Get breakdown of step difficulties within the project."""
        breakdown = {level.value: 0 for level in SkillLevel}
        for step in self.steps:
            breakdown[step.difficulty_within_project.value] += 1
        return breakdown


class DIYProjectDatabase:
    """
    Comprehensive DIY project database for product knowledge enhancement.
    
    This database provides rich project context that enhances basic product information
    with practical application knowledge, tool requirements, and expert guidance.
    """
    
    def __init__(self, data_directory: str = "diy_projects_data"):
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(exist_ok=True)
        
        # Initialize logging
        self.logger = logging.getLogger("diy_project_database")
        self.logger.setLevel(logging.INFO)
        
        # Initialize Kailash components for workflow integration
        self.workflow = WorkflowBuilder()
        self.runtime = LocalRuntime()
        
        # Project storage
        self.projects: Dict[str, DIYProject] = {}
        self.project_index: Dict[str, Set[str]] = {
            "by_category": {},
            "by_skill_level": {},
            "by_tools": {},
            "by_materials": {},
            "by_season": {}
        }
        
        # Initialize with sample projects
        self._initialize_sample_projects()
    
    def _initialize_sample_projects(self) -> None:
        """Initialize database with comprehensive sample DIY projects."""
        
        # Sample Project 1: Installing a Bathroom Faucet
        faucet_project = DIYProject(
            project_id="plumbing_001",
            name="Replace Bathroom Faucet",
            category=ProjectCategory.PLUMBING,
            subcategory="bathroom fixtures",
            description="Replace an old bathroom faucet with a new single-handle or widespread faucet. Includes removing old fixture, installing new supply lines, and testing for leaks.",
            
            skill_level=SkillLevel.INTERMEDIATE,
            complexity=ProjectComplexity.MODERATE,
            estimated_time="2-4 hours",
            estimated_cost_range=(50.0, 300.0),
            
            tools_required=[
                ToolRequirement(
                    name="Adjustable Wrench Set",
                    category="hand_tool",
                    required=True,
                    approximate_cost=25.0,
                    alternatives=["Channel Lock Pliers"],
                    skill_notes="Essential for water supply connections"
                ),
                ToolRequirement(
                    name="Basin Wrench",
                    category="specialty_tool",
                    required=True,
                    rental_option=True,
                    approximate_cost=35.0,
                    alternatives=["Long-reach pliers"],
                    skill_notes="Required to reach tight spaces under sink"
                ),
                ToolRequirement(
                    name="Plumber's Putty or Silicone Caulk",
                    category="consumables",
                    required=True,
                    approximate_cost=8.0,
                    skill_notes="For sealing connections"
                ),
                ToolRequirement(
                    name="Flashlight or Headlamp",
                    category="utility",
                    required=True,
                    approximate_cost=15.0,
                    skill_notes="Essential for working in dark spaces under sink"
                ),
                ToolRequirement(
                    name="Pipe Thread Compound",
                    category="consumables",
                    required=True,
                    approximate_cost=6.0,
                    skill_notes="For threaded connections"
                )
            ],
            
            materials_required=[
                MaterialRequirement(
                    name="Bathroom Faucet",
                    category="fixture",
                    quantity="1 unit",
                    unit_cost_range=(40.0, 250.0),
                    quality_tiers=["basic", "mid-range", "premium"],
                    where_to_buy=["Home Depot", "Lowe's", "Ferguson", "Amazon"],
                    alternatives=["Single-handle", "Widespread", "Wall-mounted"]
                ),
                MaterialRequirement(
                    name="Supply Lines",
                    category="hardware",
                    quantity="2 flexible lines",
                    unit_cost_range=(8.0, 20.0),
                    quality_tiers=["basic braided", "premium braided", "copper"],
                    where_to_buy=["Home Depot", "Lowe's", "plumbing supply"]
                )
            ],
            
            steps=[
                ProjectStep(
                    step_number=1,
                    title="Shut off water supply",
                    description="Turn off water supply valves under sink (clockwise). If no shut-off valves, turn off main water supply to house.",
                    estimated_time="5 minutes",
                    tools_needed=["Flashlight"],
                    materials_needed=[],
                    safety_notes=["Always turn off water before starting"],
                    common_mistakes=["Forgetting to turn off water", "Not checking both hot and cold supplies"],
                    pro_tips=["Test faucet after shutoff to ensure water is off", "Take photo of connections before disconnecting"]
                ),
                ProjectStep(
                    step_number=2,
                    title="Disconnect supply lines",
                    description="Use basin wrench to disconnect supply lines from old faucet. Water may drain out, so have towels ready.",
                    estimated_time="15 minutes",
                    tools_needed=["Basin Wrench", "Flashlight"],
                    materials_needed=[],
                    safety_notes=["Have towels ready for water spillage"],
                    common_mistakes=["Using wrong wrench and damaging connections", "Not having towels ready"],
                    pro_tips=["Turn counterclockwise to loosen", "Take photos of connections for reference"],
                    difficulty_within_project=SkillLevel.INTERMEDIATE
                ),
                ProjectStep(
                    step_number=3,
                    title="Remove old faucet",
                    description="Remove mounting nuts that hold faucet to sink using basin wrench. Lift out old faucet from above.",
                    estimated_time="20 minutes",
                    tools_needed=["Basin Wrench", "Adjustable Wrench"],
                    materials_needed=[],
                    safety_notes=["Faucet may be heavy when lifted out"],
                    common_mistakes=["Not removing all mounting hardware", "Damaging sink surface"],
                    pro_tips=["Clean sink surface thoroughly before installing new faucet"]
                ),
                ProjectStep(
                    step_number=4,
                    title="Install new faucet",
                    description="Place new faucet through sink holes. From underneath, install washers and mounting nuts. Hand-tighten, then snug with wrench.",
                    estimated_time="30 minutes",
                    tools_needed=["Basin Wrench", "Adjustable Wrench"],
                    materials_needed=["New Faucet", "Plumber's Putty"],
                    safety_notes=["Don't overtighten mounting nuts"],
                    common_mistakes=["Overtightening and cracking sink", "Forgetting washers or gaskets"],
                    pro_tips=["Apply plumber's putty if required by manufacturer", "Ensure faucet is centered and straight"],
                    difficulty_within_project=SkillLevel.INTERMEDIATE
                ),
                ProjectStep(
                    step_number=5,
                    title="Connect supply lines",
                    description="Connect new supply lines to faucet and shut-off valves. Use pipe thread compound on threaded connections.",
                    estimated_time="20 minutes",
                    tools_needed=["Adjustable Wrench", "Basin Wrench"],
                    materials_needed=["Supply Lines", "Pipe Thread Compound"],
                    safety_notes=["Don't overtighten flexible supply lines"],
                    common_mistakes=["Cross-threading connections", "Connecting hot to cold"],
                    pro_tips=["Hand-tighten first, then 1/4 turn with wrench", "Hot supply typically on left"],
                    difficulty_within_project=SkillLevel.INTERMEDIATE
                ),
                ProjectStep(
                    step_number=6,
                    title="Test installation",
                    description="Turn water supply back on slowly. Check all connections for leaks. Test faucet operation.",
                    estimated_time="15 minutes",
                    tools_needed=["Flashlight"],
                    materials_needed=[],
                    safety_notes=["Turn water on slowly to avoid pressure surge"],
                    common_mistakes=["Not checking for leaks thoroughly", "Ignoring small drips"],
                    pro_tips=["Check connections after 24 hours for delayed leaks", "Run water for several minutes to check operation"]
                )
            ],
            
            safety_considerations=[
                SafetyConsideration(
                    hazard_type="water damage",
                    risk_level="medium",
                    safety_equipment=["Towels", "Bucket"],
                    precautions=["Always shut off water supply", "Have towels ready", "Check for leaks before leaving"],
                    when_to_call_professional=["If supply valves won't turn", "If pipes are corroded", "If electrical connections are involved"]
                )
            ],
            
            common_mistakes=[
                CommonMistake(
                    mistake="Not shutting off water completely",
                    why_it_happens="Assuming faucet shutoff is enough",
                    how_to_avoid="Always use supply valves or main shutoff",
                    how_to_fix="Turn off water and start over",
                    cost_impact="medium"
                ),
                CommonMistake(
                    mistake="Overtightening connections",
                    why_it_happens="Fear of leaks leads to excessive force",
                    how_to_avoid="Hand-tight plus 1/4 turn with wrench",
                    how_to_fix="Replace damaged components",
                    cost_impact="high"
                )
            ],
            
            pro_tips=[
                "Take photos before disconnecting anything",
                "Buy supply lines longer than you think you need",
                "Test fit everything before applying sealants",
                "Keep old faucet until project is complete in case of problems"
            ],
            
            best_seasons=[Season.ANY],
            prerequisites=["Basic plumbing knowledge"],
            leads_to=["Bathroom vanity upgrade", "Sink replacement"],
            
            popularity_score=85.0,
            success_rate=78.0,
            
            related_products=["faucet-basin-wrench-001", "supply-lines-braided-002", "plumber-putty-003"]
        )
        
        # Sample Project 2: Building a Deck
        deck_project = DIYProject(
            project_id="carpentry_001",
            name="Build Basic Deck",
            category=ProjectCategory.CARPENTRY,
            subcategory="outdoor structures",
            description="Build a simple rectangular deck using pressure-treated lumber. Includes foundation, framing, decking, and basic railing.",
            
            skill_level=SkillLevel.ADVANCED,
            complexity=ProjectComplexity.MAJOR,
            estimated_time="3-5 days",
            estimated_cost_range=(800.0, 2500.0),
            
            tools_required=[
                ToolRequirement(
                    name="Circular Saw",
                    category="power_tool",
                    required=True,
                    approximate_cost=120.0,
                    alternatives=["Miter Saw", "Hand Saw"],
                    skill_notes="Essential for cutting lumber to length"
                ),
                ToolRequirement(
                    name="Power Drill",
                    category="power_tool",
                    required=True,
                    approximate_cost=80.0,
                    alternatives=["Impact Driver"],
                    skill_notes="For drilling pilot holes and driving screws"
                ),
                ToolRequirement(
                    name="Level (4-foot)",
                    category="hand_tool",
                    required=True,
                    approximate_cost=35.0,
                    skill_notes="Critical for ensuring level deck surface"
                ),
                ToolRequirement(
                    name="Speed Square",
                    category="hand_tool",
                    required=True,
                    approximate_cost=15.0,
                    skill_notes="For marking square cuts and angles"
                ),
                ToolRequirement(
                    name="Post-Hole Digger",
                    category="specialty_tool",
                    required=True,
                    rental_option=True,
                    approximate_cost=60.0,
                    alternatives=["Shovel", "Auger"],
                    skill_notes="For digging foundation holes"
                )
            ],
            
            materials_required=[
                MaterialRequirement(
                    name="Pressure-Treated Lumber",
                    category="lumber",
                    quantity="Varies by deck size",
                    unit_cost_range=(3.0, 8.0),
                    quality_tiers=["standard PT", "premium PT", "cedar"],
                    where_to_buy=["Home Depot", "Lowe's", "Lumber yard"],
                    alternatives=["Composite decking", "Cedar", "Redwood"]
                ),
                MaterialRequirement(
                    name="Galvanized Carriage Bolts",
                    category="hardware",
                    quantity="20-30 bolts",
                    unit_cost_range=(1.0, 3.0),
                    where_to_buy=["Home Depot", "Fastener stores"],
                    alternatives=["Structural screws", "Lag bolts"]
                )
            ],
            
            steps=[
                ProjectStep(
                    step_number=1,
                    title="Plan and mark deck layout",
                    description="Mark deck corners with stakes and string. Check measurements and ensure square using 3-4-5 triangle method.",
                    estimated_time="2 hours",
                    tools_needed=["Measuring Tape", "Stakes", "String", "Speed Square"],
                    materials_needed=["Stakes", "String"],
                    safety_notes=["Call 811 for utility marking before digging"],
                    common_mistakes=["Not checking for square", "Ignoring property lines", "Not considering drainage"],
                    pro_tips=["Double-check all measurements", "Consider deck height and stairs early"],
                    difficulty_within_project=SkillLevel.INTERMEDIATE
                )
            ],
            
            safety_considerations=[
                SafetyConsideration(
                    hazard_type="structural",
                    risk_level="high",
                    safety_equipment=["Safety glasses", "Work gloves", "Hard hat"],
                    precautions=["Follow local building codes", "Get permits if required", "Use proper lumber grades"],
                    when_to_call_professional=["If structural calculations are needed", "For electrical work", "If soil conditions are poor"]
                )
            ],
            
            common_mistakes=[
                CommonMistake(
                    mistake="Not getting building permits",
                    why_it_happens="Wanting to avoid fees and delays",
                    how_to_avoid="Check local requirements before starting",
                    how_to_fix="Stop work and get permits",
                    cost_impact="high"
                )
            ],
            
            pro_tips=[
                "Rent a pneumatic nailer for faster assembly",
                "Pre-drill all holes near board ends",
                "Use joist hangers for stronger connections",
                "Plan for deck drainage and ventilation"
            ],
            
            best_seasons=[Season.SPRING, Season.SUMMER, Season.FALL],
            prerequisites=["Basic carpentry skills", "Building permits"],
            leads_to=["Deck staining", "Outdoor lighting", "Pergola addition"],
            
            popularity_score=72.0,
            success_rate=65.0,
            
            related_products=["pressure-treated-lumber-2x8", "deck-screws-galvanized", "post-anchors"]
        )
        
        # Add projects to database
        self.add_project(faucet_project)
        self.add_project(deck_project)
        
        # Add more sample projects
        self._add_electrical_projects()
        self._add_painting_projects()
        self._add_flooring_projects()
    
    def _add_electrical_projects(self) -> None:
        """Add sample electrical projects."""
        outlet_project = DIYProject(
            project_id="electrical_001",
            name="Install GFCI Outlet",
            category=ProjectCategory.ELECTRICAL,
            subcategory="electrical outlets",
            description="Replace standard outlet with GFCI outlet in bathroom, kitchen, or outdoor location for safety.",
            
            skill_level=SkillLevel.INTERMEDIATE,
            complexity=ProjectComplexity.MODERATE,
            estimated_time="1-2 hours",
            estimated_cost_range=(15.0, 40.0),
            
            tools_required=[
                ToolRequirement(
                    name="Non-Contact Voltage Tester",
                    category="safety_equipment",
                    required=True,
                    approximate_cost=25.0,
                    skill_notes="Critical for electrical safety"
                ),
                ToolRequirement(
                    name="Wire Strippers",
                    category="hand_tool",
                    required=True,
                    approximate_cost=18.0,
                    skill_notes="For preparing wire connections"
                ),
                ToolRequirement(
                    name="Screwdriver Set",
                    category="hand_tool",
                    required=True,
                    approximate_cost=20.0,
                    skill_notes="Both flathead and Phillips needed"
                )
            ],
            
            materials_required=[
                MaterialRequirement(
                    name="GFCI Outlet",
                    category="electrical",
                    quantity="1 unit",
                    unit_cost_range=(12.0, 35.0),
                    quality_tiers=["basic", "tamper-resistant", "USB combo"],
                    where_to_buy=["Home Depot", "Electrical supply", "Amazon"]
                )
            ],
            
            steps=[
                ProjectStep(
                    step_number=1,
                    title="Turn off power at breaker",
                    description="Turn off circuit breaker for the outlet. Test with voltage tester to confirm power is off.",
                    estimated_time="5 minutes",
                    tools_needed=["Non-Contact Voltage Tester"],
                    materials_needed=[],
                    safety_notes=["Never work on live circuits", "Double-check with voltage tester"],
                    common_mistakes=["Not testing with voltage detector", "Working on wrong circuit"],
                    pro_tips=["Test voltage tester on known live circuit first", "Label breaker for future reference"],
                    difficulty_within_project=SkillLevel.BEGINNER
                )
            ],
            
            safety_considerations=[
                SafetyConsideration(
                    hazard_type="electrical",
                    risk_level="high",
                    safety_equipment=["Non-contact voltage tester", "Insulated tools"],
                    precautions=["Always turn off power", "Test circuits before working", "Use proper tools"],
                    when_to_call_professional=["If wiring is aluminum", "If panel work is needed", "If unsure about any step"]
                )
            ],
            
            common_mistakes=[
                CommonMistake(
                    mistake="Connecting wires to wrong terminals",
                    why_it_happens="GFCI outlets have LINE and LOAD terminals",
                    how_to_avoid="Follow manufacturer's wiring diagram carefully",
                    how_to_fix="Rewire correctly - LINE from panel, LOAD to downstream outlets",
                    cost_impact="low"
                )
            ],
            
            pro_tips=[
                "Take photo of existing wiring before disconnecting",
                "Test GFCI monthly with test/reset buttons",
                "LINE terminals connect to power source, LOAD to downstream outlets"
            ],
            
            best_seasons=[Season.ANY],
            prerequisites=["Basic electrical knowledge", "Electrical permits if required"],
            leads_to=["Bathroom fan installation", "Kitchen electrical upgrades"],
            
            popularity_score=68.0,
            success_rate=82.0,
            
            related_products=["gfci-outlet-20amp", "voltage-tester-non-contact", "wire-strippers-12awg"]
        )
        
        self.add_project(outlet_project)
    
    def _add_painting_projects(self) -> None:
        """Add sample painting projects."""
        room_painting = DIYProject(
            project_id="painting_001",
            name="Paint Interior Room",
            category=ProjectCategory.PAINTING,
            subcategory="interior painting",
            description="Complete interior room painting including prep work, priming, and finish coating.",
            
            skill_level=SkillLevel.BEGINNER,
            complexity=ProjectComplexity.MODERATE,
            estimated_time="1-2 days",
            estimated_cost_range=(50.0, 200.0),
            
            tools_required=[
                ToolRequirement(
                    name="Paint Roller and Tray",
                    category="painting_tool",
                    required=True,
                    approximate_cost=15.0,
                    skill_notes="9-inch roller for walls, 4-inch for trim"
                ),
                ToolRequirement(
                    name="Paint Brushes",
                    category="painting_tool",
                    required=True,
                    approximate_cost=25.0,
                    alternatives=["Foam brushes for small areas"],
                    skill_notes="Angled brush for cutting in, flat brush for trim"
                ),
                ToolRequirement(
                    name="Drop Cloths",
                    category="protection",
                    required=True,
                    approximate_cost=20.0,
                    alternatives=["Plastic sheeting", "Old sheets"],
                    skill_notes="Canvas drop cloths are best"
                )
            ],
            
            materials_required=[
                MaterialRequirement(
                    name="Interior Paint",
                    category="paint",
                    quantity="1 gallon per 350 sq ft",
                    unit_cost_range=(25.0, 60.0),
                    quality_tiers=["basic latex", "premium latex", "zero-VOC"],
                    where_to_buy=["Home Depot", "Sherwin Williams", "Benjamin Moore stores"]
                )
            ],
            
            steps=[
                ProjectStep(
                    step_number=1,
                    title="Prepare room and surfaces",
                    description="Remove furniture, lay drop cloths, remove outlet covers, fill holes, sand rough spots.",
                    estimated_time="2-3 hours",
                    tools_needed=["Screwdriver", "Sandpaper", "Putty Knife"],
                    materials_needed=["Drop Cloths", "Painter's Tape", "Spackle"],
                    safety_notes=["Wear dust mask when sanding"],
                    common_mistakes=["Skipping prep work", "Not removing outlet covers"],
                    pro_tips=["Good prep work makes all the difference", "Use high-quality painter's tape"],
                    difficulty_within_project=SkillLevel.BEGINNER
                )
            ],
            
            safety_considerations=[
                SafetyConsideration(
                    hazard_type="chemical",
                    risk_level="low",
                    safety_equipment=["Dust mask", "Ventilation"],
                    precautions=["Ensure good ventilation", "Read paint labels"],
                    when_to_call_professional=["For lead paint removal", "High ceilings", "Complex trim work"]
                )
            ],
            
            common_mistakes=[
                CommonMistake(
                    mistake="Not using primer",
                    why_it_happens="Trying to save time and money",
                    how_to_avoid="Prime all new surfaces and color changes",
                    how_to_fix="Apply primer coat, then finish coats",
                    cost_impact="medium"
                )
            ],
            
            pro_tips=[
                "Cut in edges first, then roll walls",
                "Maintain wet edge to avoid lap marks",
                "Remove tape while paint is still wet",
                "Two thin coats better than one thick coat"
            ],
            
            best_seasons=[Season.ANY],
            prerequisites=["None - great beginner project"],
            leads_to=["Exterior painting", "Decorative finishes", "Cabinet painting"],
            
            popularity_score=95.0,
            success_rate=88.0,
            
            related_products=["interior-paint-eggshell", "paint-roller-9inch", "painters-tape-blue"]
        )
        
        self.add_project(room_painting)
    
    def _add_flooring_projects(self) -> None:
        """Add sample flooring projects."""
        laminate_flooring = DIYProject(
            project_id="flooring_001",
            name="Install Laminate Flooring",
            category=ProjectCategory.FLOORING,
            subcategory="laminate installation",
            description="Install click-lock laminate flooring including underlayment, transitions, and trim.",
            
            skill_level=SkillLevel.INTERMEDIATE,
            complexity=ProjectComplexity.COMPLEX,
            estimated_time="2-3 days",
            estimated_cost_range=(200.0, 800.0),
            
            tools_required=[
                ToolRequirement(
                    name="Miter Saw",
                    category="power_tool",
                    required=True,
                    rental_option=True,
                    approximate_cost=200.0,
                    alternatives=["Circular saw with guide", "Hand saw"],
                    skill_notes="Essential for accurate crosscuts"
                ),
                ToolRequirement(
                    name="Pull Bar",
                    category="specialty_tool",
                    required=True,
                    approximate_cost=25.0,
                    skill_notes="For fitting last row against wall"
                ),
                ToolRequirement(
                    name="Tapping Block",
                    category="specialty_tool",
                    required=True,
                    approximate_cost=15.0,
                    skill_notes="Protects edges while joining planks"
                )
            ],
            
            materials_required=[
                MaterialRequirement(
                    name="Laminate Flooring",
                    category="flooring",
                    quantity="Room sq ft + 10% waste",
                    unit_cost_range=(1.50, 5.00),
                    quality_tiers=["basic", "AC3 rated", "AC4 commercial grade"],
                    where_to_buy=["Home Depot", "Lowe's", "Lumber Liquidators"]
                ),
                MaterialRequirement(
                    name="Underlayment",
                    category="flooring",
                    quantity="Same as flooring sq ft",
                    unit_cost_range=(0.30, 0.80),
                    quality_tiers=["basic foam", "premium with moisture barrier"],
                    where_to_buy=["Flooring retailers", "Home improvement stores"]
                )
            ],
            
            steps=[
                ProjectStep(
                    step_number=1,
                    title="Prepare subfloor",
                    description="Clean subfloor, check for squeaks and level issues, install underlayment.",
                    estimated_time="3-4 hours",
                    tools_needed=["Vacuum", "Level", "Utility Knife"],
                    materials_needed=["Underlayment", "Tape"],
                    safety_notes=["Ensure subfloor is dry and structurally sound"],
                    common_mistakes=["Not checking subfloor level", "Overlapping underlayment"],
                    pro_tips=["Butt underlayment seams, don't overlap", "Run underlayment up walls 1/4 inch"],
                    difficulty_within_project=SkillLevel.BEGINNER
                )
            ],
            
            safety_considerations=[
                SafetyConsideration(
                    hazard_type="physical",
                    risk_level="medium",
                    safety_equipment=["Knee pads", "Safety glasses", "Dust mask"],
                    precautions=["Use proper lifting techniques", "Keep work area clean"],
                    when_to_call_professional=["If subfloor repairs needed", "For complex room shapes", "If moisture issues present"]
                )
            ],
            
            common_mistakes=[
                CommonMistake(
                    mistake="Not leaving expansion gaps",
                    why_it_happens="Trying to make flooring tight to walls",
                    how_to_avoid="Leave 1/4 inch gap around perimeter",
                    how_to_fix="Remove trim and cut back flooring",
                    cost_impact="high"
                )
            ],
            
            pro_tips=[
                "Stagger seams by at least 12 inches",
                "Start with longest, straightest wall",
                "Save cutoffs for end pieces",
                "Let flooring acclimate 48 hours before installation"
            ],
            
            best_seasons=[Season.ANY],
            prerequisites=["Room measurement skills", "Basic tool knowledge"],
            leads_to=["Baseboard installation", "Transition strips", "Room finishing"],
            
            popularity_score=78.0,
            success_rate=71.0,
            
            related_products=["laminate-flooring-oak", "underlayment-premium", "laminate-pull-bar"]
        )
        
        self.add_project(laminate_flooring)
    
    def add_project(self, project: DIYProject) -> None:
        """Add a project to the database and update indexes."""
        self.projects[project.project_id] = project
        self._update_indexes(project)
        self.logger.info(f"Added project: {project.name} ({project.project_id})")
    
    def _update_indexes(self, project: DIYProject) -> None:
        """Update search indexes for a project."""
        # Index by category
        category_key = project.category.value
        if category_key not in self.project_index["by_category"]:
            self.project_index["by_category"][category_key] = set()
        self.project_index["by_category"][category_key].add(project.project_id)
        
        # Index by skill level
        skill_key = project.skill_level.value
        if skill_key not in self.project_index["by_skill_level"]:
            self.project_index["by_skill_level"][skill_key] = set()
        self.project_index["by_skill_level"][skill_key].add(project.project_id)
        
        # Index by tools
        for tool in project.tools_required:
            tool_key = tool.name.lower()
            if tool_key not in self.project_index["by_tools"]:
                self.project_index["by_tools"][tool_key] = set()
            self.project_index["by_tools"][tool_key].add(project.project_id)
        
        # Index by materials
        for material in project.materials_required:
            material_key = material.name.lower()
            if material_key not in self.project_index["by_materials"]:
                self.project_index["by_materials"][material_key] = set()
            self.project_index["by_materials"][material_key].add(project.project_id)
        
        # Index by seasons
        for season in project.best_seasons:
            season_key = season.value
            if season_key not in self.project_index["by_season"]:
                self.project_index["by_season"][season_key] = set()
            self.project_index["by_season"][season_key].add(project.project_id)
    
    def find_projects_by_tool(self, tool_name: str) -> List[DIYProject]:
        """Find projects that use a specific tool."""
        tool_key = tool_name.lower()
        project_ids = self.project_index["by_tools"].get(tool_key, set())
        return [self.projects[pid] for pid in project_ids]
    
    def find_projects_by_skill_level(self, skill_level: SkillLevel) -> List[DIYProject]:
        """Find projects matching a skill level."""
        project_ids = self.project_index["by_skill_level"].get(skill_level.value, set())
        return [self.projects[pid] for pid in project_ids]
    
    def find_projects_by_category(self, category: ProjectCategory) -> List[DIYProject]:
        """Find projects in a specific category."""
        project_ids = self.project_index["by_category"].get(category.value, set())
        return [self.projects[pid] for pid in project_ids]
    
    def find_projects_by_season(self, season: Season) -> List[DIYProject]:
        """Find projects suitable for a specific season."""
        project_ids = self.project_index["by_season"].get(season.value, set())
        return [self.projects[pid] for pid in project_ids]
    
    def enhance_product_with_project_knowledge(self, product_sku: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance product data with relevant DIY project knowledge.
        
        This is the core integration function that enriches basic product information
        with practical DIY applications, project requirements, and expert guidance.
        """
        enhanced_data = product_data.copy()
        
        # Find relevant projects for this product
        relevant_projects = self._find_relevant_projects(product_sku, product_data)
        
        if relevant_projects:
            # Add DIY project enrichment
            enhanced_data["diy_project_applications"] = []
            enhanced_data["tool_usage_context"] = []
            enhanced_data["skill_level_recommendations"] = []
            enhanced_data["project_cost_context"] = []
            
            for project in relevant_projects:
                # Project application info
                project_info = {
                    "project_id": project.project_id,
                    "project_name": project.name,
                    "category": project.category.value,
                    "skill_level": project.skill_level.value,
                    "estimated_time": project.estimated_time,
                    "success_rate": f"{project.success_rate:.0f}%",
                    "popularity": f"{project.popularity_score:.0f}%"
                }
                enhanced_data["diy_project_applications"].append(project_info)
                
                # Tool usage context
                relevant_tools = self._find_product_in_project_tools(product_sku, product_data, project)
                for tool_req in relevant_tools:
                    tool_context = {
                        "project": project.name,
                        "usage": tool_req.skill_notes,
                        "required": tool_req.required,
                        "alternatives": tool_req.alternatives,
                        "rental_option": tool_req.rental_option
                    }
                    enhanced_data["tool_usage_context"].append(tool_context)
                
                # Skill level recommendations
                if project.skill_level not in [sl["level"] for sl in enhanced_data["skill_level_recommendations"]]:
                    skill_rec = {
                        "level": project.skill_level.value,
                        "project_examples": [project.name],
                        "key_considerations": self._get_skill_level_considerations(project.skill_level)
                    }
                    enhanced_data["skill_level_recommendations"].append(skill_rec)
                
                # Project cost context
                if relevant_tools:  # If this product is used in the project
                    cost_context = {
                        "project": project.name,
                        "total_project_cost_range": project.estimated_cost_range,
                        "tool_cost_range": project.get_total_tool_cost_range(),
                        "this_item_in_context": "Essential tool" if any(t.required for t in relevant_tools) else "Optional tool"
                    }
                    enhanced_data["project_cost_context"].append(cost_context)
            
            # Add aggregated insights
            enhanced_data["diy_insights"] = self._generate_diy_insights(relevant_projects, product_data)
            
            # Add common mistakes and tips relevant to this product
            enhanced_data["common_mistakes"] = self._extract_relevant_mistakes(relevant_projects, product_data)
            enhanced_data["pro_tips"] = self._extract_relevant_tips(relevant_projects, product_data)
            
            # Add seasonal recommendations
            enhanced_data["seasonal_usage"] = self._get_seasonal_recommendations(relevant_projects)
        
        return enhanced_data
    
    def _find_relevant_projects(self, product_sku: str, product_data: Dict[str, Any]) -> List[DIYProject]:
        """Find projects relevant to a specific product."""
        relevant_projects = []
        
        # Check if product SKU is directly referenced in projects
        for project in self.projects.values():
            if product_sku in project.related_products:
                relevant_projects.append(project)
                continue
        
        # Find projects by product name/category matching
        product_name = product_data.get("name", "").lower()
        product_category = product_data.get("category", "").lower()
        
        # Match by tools
        for project in self.projects.values():
            for tool in project.tools_required:
                if (tool.name.lower() in product_name or 
                    any(alt.lower() in product_name for alt in tool.alternatives)):
                    if project not in relevant_projects:
                        relevant_projects.append(project)
                        break
        
        # Match by materials
        for project in self.projects.values():
            for material in project.materials_required:
                if (material.name.lower() in product_name or
                    any(alt.lower() in product_name for alt in material.alternatives)):
                    if project not in relevant_projects:
                        relevant_projects.append(project)
                        break
        
        # Sort by relevance (popularity and success rate)
        relevant_projects.sort(key=lambda p: (p.popularity_score + p.success_rate) / 2, reverse=True)
        
        return relevant_projects[:5]  # Return top 5 most relevant projects
    
    def _find_product_in_project_tools(self, product_sku: str, product_data: Dict[str, Any], project: DIYProject) -> List[ToolRequirement]:
        """Find how a product is used as a tool in a project."""
        product_name = product_data.get("name", "").lower()
        matching_tools = []
        
        for tool in project.tools_required:
            if (tool.name.lower() in product_name or
                any(alt.lower() in product_name for alt in tool.alternatives) or
                product_sku in project.related_products):
                matching_tools.append(tool)
        
        return matching_tools
    
    def _get_skill_level_considerations(self, skill_level: SkillLevel) -> List[str]:
        """Get key considerations for a skill level."""
        considerations = {
            SkillLevel.BEGINNER: [
                "No prior experience required",
                "Basic hand tools sufficient",
                "Good first project",
                "Minimal safety risks"
            ],
            SkillLevel.INTERMEDIATE: [
                "Some DIY experience helpful",
                "May require power tools",
                "Basic understanding of techniques needed",
                "Moderate time investment"
            ],
            SkillLevel.ADVANCED: [
                "Significant DIY experience required",
                "Specialized tools may be needed",
                "Complex techniques involved",
                "Consider professional consultation"
            ],
            SkillLevel.EXPERT: [
                "Professional-level skills required",
                "Expensive specialized tools needed",
                "High risk if done incorrectly",
                "Strong recommendation to hire professional"
            ]
        }
        return considerations.get(skill_level, [])
    
    def _generate_diy_insights(self, projects: List[DIYProject], product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate aggregated insights from relevant projects."""
        if not projects:
            return {}
        
        insights = {
            "most_common_category": max(set(p.category.value for p in projects), 
                                       key=[p.category.value for p in projects].count),
            "skill_level_range": {
                "easiest": min(p.skill_level.value for p in projects),
                "hardest": max(p.skill_level.value for p in projects)
            },
            "time_investment_range": {
                "shortest": min((p.estimated_time for p in projects), key=self._parse_time_estimate),
                "longest": max((p.estimated_time for p in projects), key=self._parse_time_estimate)
            },
            "cost_range": {
                "min_project_cost": min(p.estimated_cost_range[0] for p in projects),
                "max_project_cost": max(p.estimated_cost_range[1] for p in projects)
            },
            "average_success_rate": sum(p.success_rate for p in projects) / len(projects),
            "best_seasons": list(set(season.value for p in projects for season in p.best_seasons))
        }
        
        return insights
    
    def _parse_time_estimate(self, time_str: str) -> float:
        """Parse time estimate string to hours for comparison."""
        time_str = time_str.lower()
        if "hour" in time_str:
            # Extract first number
            import re
            numbers = re.findall(r'\d+', time_str)
            return float(numbers[0]) if numbers else 0
        elif "day" in time_str:
            numbers = re.findall(r'\d+', time_str)
            return float(numbers[0]) * 8 if numbers else 0  # Assume 8 hours per day
        return 0
    
    def _extract_relevant_mistakes(self, projects: List[DIYProject], product_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract common mistakes relevant to the product."""
        relevant_mistakes = []
        product_name = product_data.get("name", "").lower()
        
        for project in projects:
            for mistake in project.common_mistakes:
                # Check if mistake mentions the product or related terms
                if (product_name in mistake.mistake.lower() or
                    any(word in mistake.mistake.lower() for word in product_name.split())):
                    relevant_mistakes.append({
                        "project": project.name,
                        "mistake": mistake.mistake,
                        "how_to_avoid": mistake.how_to_avoid,
                        "cost_impact": mistake.cost_impact
                    })
        
        return relevant_mistakes[:3]  # Return top 3 most relevant
    
    def _extract_relevant_tips(self, projects: List[DIYProject], product_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract pro tips relevant to the product."""
        relevant_tips = []
        product_name = product_data.get("name", "").lower()
        
        for project in projects:
            for tip in project.pro_tips:
                # Check if tip mentions the product or related terms
                if (product_name in tip.lower() or
                    any(word in tip.lower() for word in product_name.split())):
                    relevant_tips.append({
                        "project": project.name,
                        "tip": tip
                    })
        
        return relevant_tips[:3]  # Return top 3 most relevant
    
    def _get_seasonal_recommendations(self, projects: List[DIYProject]) -> Dict[str, List[str]]:
        """Get seasonal recommendations from projects."""
        seasonal_recs = {}
        
        for project in projects:
            for season in project.best_seasons:
                if season.value not in seasonal_recs:
                    seasonal_recs[season.value] = []
                seasonal_recs[season.value].append(project.name)
        
        return seasonal_recs
    
    def generate_workflow_for_product_enhancement(self, product_skus: List[str]) -> WorkflowBuilder:
        """Generate a Kailash workflow for bulk product enhancement with DIY project knowledge."""
        workflow = WorkflowBuilder()
        
        # Step 1: Load product data
        workflow.add_node("PythonCodeNode", "load_products", {
            "code": f"""
# Load products from database
product_skus = {product_skus}
products = []

# This would connect to your actual product database
# For demo, we'll create sample products
for sku in product_skus:
    sample_product = {{
        'sku': sku,
        'name': f'Product {{sku}}',
        'category': 'tools',
        'description': f'Description for {{sku}}'
    }}
    products.append(sample_product)

result = products
""",
            "requirements": []
        })
        
        # Step 2: Enhance products with DIY knowledge
        workflow.add_node("PythonCodeNode", "enhance_with_diy", {
            "code": """
# Initialize DIY database
from diy_project_database import DIYProjectDatabase

diy_db = DIYProjectDatabase()
enhanced_products = []

for product in products:
    enhanced = diy_db.enhance_product_with_project_knowledge(
        product['sku'], product
    )
    enhanced_products.append(enhanced)

result = enhanced_products
""",
            "requirements": []
        })
        
        # Step 3: Save enhanced data
        workflow.add_node("PythonCodeNode", "save_enhanced_products", {
            "code": """
import json
from datetime import datetime

# Save enhanced products
output_file = f'enhanced_products_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

with open(output_file, 'w') as f:
    json.dump(enhanced_products, f, indent=2, default=str)

print(f"Enhanced {len(enhanced_products)} products")
print(f"Saved to {output_file}")

result = {
    'enhanced_count': len(enhanced_products),
    'output_file': output_file
}
""",
            "requirements": []
        })
        
        # Connect workflow
        workflow.connect("load_products", "enhance_with_diy")
        workflow.connect("enhance_with_diy", "save_enhanced_products")
        
        return workflow
    
    def save_database(self, filename: str = None) -> str:
        """Save the entire database to a JSON file."""
        if filename is None:
            filename = f"diy_projects_database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.data_directory / filename
        
        database_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "total_projects": len(self.projects),
                "categories": list(set(p.category.value for p in self.projects.values())),
                "skill_levels": list(set(p.skill_level.value for p in self.projects.values()))
            },
            "projects": {pid: project.to_dict() for pid, project in self.projects.items()},
            "indexes": {
                "by_category": {k: list(v) for k, v in self.project_index["by_category"].items()},
                "by_skill_level": {k: list(v) for k, v in self.project_index["by_skill_level"].items()},
                "by_tools": {k: list(v) for k, v in self.project_index["by_tools"].items()},
                "by_materials": {k: list(v) for k, v in self.project_index["by_materials"].items()},
                "by_season": {k: list(v) for k, v in self.project_index["by_season"].items()}
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(database_data, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Database saved to {filepath}")
        return str(filepath)
    
    def load_database(self, filepath: str) -> bool:
        """Load database from a JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                database_data = json.load(f)
            
            # Load projects
            self.projects = {}
            for pid, project_data in database_data["projects"].items():
                # Convert enum strings back to enums
                project_data["category"] = ProjectCategory(project_data["category"])
                project_data["skill_level"] = SkillLevel(project_data["skill_level"])
                project_data["complexity"] = ProjectComplexity(project_data["complexity"])
                project_data["best_seasons"] = [Season(s) for s in project_data["best_seasons"]]
                
                # Convert tool and material requirements
                project_data["tools_required"] = [ToolRequirement(**tool) for tool in project_data["tools_required"]]
                project_data["materials_required"] = [MaterialRequirement(**mat) for mat in project_data["materials_required"]]
                project_data["steps"] = [ProjectStep(**step) for step in project_data["steps"]]
                project_data["safety_considerations"] = [SafetyConsideration(**safety) for safety in project_data["safety_considerations"]]
                project_data["common_mistakes"] = [CommonMistake(**mistake) for mistake in project_data["common_mistakes"]]
                
                # Convert datetime strings
                project_data["created_at"] = datetime.fromisoformat(project_data["created_at"])
                project_data["updated_at"] = datetime.fromisoformat(project_data["updated_at"])
                
                project = DIYProject(**project_data)
                self.projects[pid] = project
            
            # Load indexes
            self.project_index = {
                "by_category": {k: set(v) for k, v in database_data["indexes"]["by_category"].items()},
                "by_skill_level": {k: set(v) for k, v in database_data["indexes"]["by_skill_level"].items()},
                "by_tools": {k: set(v) for k, v in database_data["indexes"]["by_tools"].items()},
                "by_materials": {k: set(v) for k, v in database_data["indexes"]["by_materials"].items()},
                "by_season": {k: set(v) for k, v in database_data["indexes"]["by_season"].items()}
            }
            
            self.logger.info(f"Database loaded from {filepath}")
            self.logger.info(f"Loaded {len(self.projects)} projects")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load database from {filepath}: {str(e)}")
            return False


# Example usage and testing functions
def create_sample_diy_database() -> DIYProjectDatabase:
    """Create a sample DIY database for testing."""
    return DIYProjectDatabase()


def demonstrate_product_enhancement():
    """Demonstrate how DIY project knowledge enhances basic product data."""
    # Create DIY database
    diy_db = DIYProjectDatabase()
    
    # Sample basic product data (what you might get from Excel or scraping)
    basic_products = [
        {
            "sku": "wrench-adjustable-10inch",
            "name": "10-inch Adjustable Wrench",
            "price": 24.99,
            "category": "hand tools",
            "description": "Adjustable wrench with 10-inch length"
        },
        {
            "sku": "drill-cordless-18v",
            "name": "18V Cordless Drill",
            "price": 89.99,
            "category": "power tools",
            "description": "Cordless drill with 18V battery"
        },
        {
            "sku": "paint-interior-latex",
            "name": "Interior Latex Paint - Eggshell",
            "price": 45.99,
            "category": "paint",
            "description": "Premium interior latex paint, eggshell finish"
        }
    ]
    
    print("=== DIY Project Database Enhancement Demo ===\n")
    
    for product in basic_products:
        print(f"BASIC PRODUCT: {product['name']} (${product['price']})")
        print(f"Category: {product['category']}")
        print(f"Description: {product['description']}")
        print()
        
        # Enhance with DIY project knowledge
        enhanced = diy_db.enhance_product_with_project_knowledge(product['sku'], product)
        
        if 'diy_project_applications' in enhanced:
            print("DIY PROJECT APPLICATIONS:")
            for app in enhanced['diy_project_applications']:
                print(f"  • {app['project_name']} ({app['category']})")
                print(f"    Skill Level: {app['skill_level'].title()}")
                print(f"    Time: {app['estimated_time']}")
                print(f"    Success Rate: {app['success_rate']}")
            print()
        
        if 'tool_usage_context' in enhanced:
            print("TOOL USAGE CONTEXT:")
            for context in enhanced['tool_usage_context']:
                print(f"  • In {context['project']}: {context['usage']}")
                if context['alternatives']:
                    print(f"    Alternatives: {', '.join(context['alternatives'])}")
            print()
        
        if 'diy_insights' in enhanced:
            insights = enhanced['diy_insights']
            print("DIY INSIGHTS:")
            print(f"  • Most common use: {insights['most_common_category'].title()} projects")
            print(f"  • Skill range: {insights['skill_level_range']['easiest'].title()} to {insights['skill_level_range']['hardest'].title()}")
            print(f"  • Project costs: ${insights['cost_range']['min_project_cost']:.0f} - ${insights['cost_range']['max_project_cost']:.0f}")
            print(f"  • Average success rate: {insights['average_success_rate']:.0f}%")
            print()
        
        if 'pro_tips' in enhanced and enhanced['pro_tips']:
            print("PRO TIPS:")
            for tip in enhanced['pro_tips'][:2]:  # Show first 2 tips
                print(f"  • {tip['tip']}")
            print()
        
        print("-" * 60)
        print()


if __name__ == "__main__":
    # Run demonstration
    demonstrate_product_enhancement()
    
    # Save sample database
    diy_db = create_sample_diy_database()
    saved_file = diy_db.save_database()
    print(f"Sample database saved to: {saved_file}")