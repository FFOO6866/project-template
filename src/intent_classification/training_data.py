"""
Training data generator for DIY intent classification system.
Creates 1000+ labeled examples across 5 intent categories with Singapore-specific contexts.
"""

import json
import random
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class TrainingExample:
    """Single training example with query, intent, entities, and confidence"""
    query: str
    intent: str
    entities: Dict[str, str]
    confidence: float = 1.0


class DIYTrainingDataGenerator:
    """Generates comprehensive DIY training data for intent classification"""
    
    def __init__(self):
        self.intents = [
            "project_planning",
            "problem_solving", 
            "tool_selection",
            "product_comparison",
            "learning"
        ]
        
        # Singapore-specific terms and contexts
        self.sg_contexts = {
            "locations": ["HDB", "condo", "landed property", "void deck", "shophouse"],
            "climate": ["humid weather", "tropical climate", "monsoon season", "aircon"],
            "regulations": ["HDB guidelines", "URA requirements", "fire safety", "neighbour consent"],
            "materials": ["moisture-resistant", "anti-termite", "weather-proof"],
            "services": ["Town Council", "managing agent", "contractor", "handyman"]
        }
        
    def generate_project_planning_queries(self) -> List[TrainingExample]:
        """Generate project planning intent queries"""
        templates = [
            "I want to renovate my {room}",
            "Planning to {action} {project_type}",
            "How to plan {project_type} in {location}",
            "Need help designing {project_type}",
            "What's involved in {project_type} project",
            "I'm thinking of {action} my {room}",
            "Want to {action} {project_type} for {location}",
            "Planning {project_type} renovation",
            "Need {project_type} design ideas",
            "How to start {project_type} project"
        ]
        
        rooms = ["bathroom", "kitchen", "bedroom", "living room", "balcony", "study room", "dining area"]
        actions = ["renovating", "upgrading", "installing", "building", "adding", "creating"]
        projects = ["deck", "shelving", "cabinet", "flooring", "lighting", "storage system", "feature wall"]
        
        examples = []
        for _ in range(200):
            template = random.choice(templates)
            query = template.format(
                room=random.choice(rooms),
                action=random.choice(actions),
                project_type=random.choice(projects),
                location=random.choice(self.sg_contexts["locations"])
            )
            
            entities = {
                "project_type": random.choice(projects),
                "room": random.choice(rooms) if "{room}" in template else None,
                "skill_level": random.choice(["beginner", "intermediate", "advanced"]),
                "budget_range": random.choice(["under_500", "500_2000", "2000_5000", "above_5000"])
            }
            
            examples.append(TrainingExample(
                query=query,
                intent="project_planning",
                entities={k: v for k, v in entities.items() if v is not None}
            ))
            
        return examples
    
    def generate_problem_solving_queries(self) -> List[TrainingExample]:
        """Generate problem solving intent queries"""
        templates = [
            "How to fix {problem}",
            "My {item} is {issue}",
            "{problem} in my {location}",
            "Need help with {problem}",
            "{item} {issue}, what to do",
            "Emergency: {problem}",
            "Urgent help needed for {problem}",
            "Repair {item} {issue}",
            "Fix {problem} quickly",
            "Troubleshoot {problem}"
        ]
        
        problems = ["leaky faucet", "squeaky floors", "clogged drain", "electrical outlet not working",
                   "aircon not cooling", "water heater issues", "sliding door stuck", "tile cracking"]
        items = ["faucet", "door", "window", "toilet", "sink", "fan", "light", "switch"]
        issues = ["leaking", "broken", "stuck", "not working", "making noise", "loose"]
        
        examples = []
        for _ in range(200):
            template = random.choice(templates)
            query = template.format(
                problem=random.choice(problems),
                item=random.choice(items),
                issue=random.choice(issues),
                location=random.choice(self.sg_contexts["locations"])
            )
            
            entities = {
                "problem_type": random.choice(problems),
                "urgency": random.choice(["low", "medium", "high", "emergency"]),
                "skill_level": random.choice(["beginner", "intermediate", "advanced"])
            }
            
            examples.append(TrainingExample(
                query=query,
                intent="problem_solving",
                entities=entities
            ))
            
        return examples
    
    def generate_tool_selection_queries(self) -> List[TrainingExample]:
        """Generate tool selection intent queries"""
        templates = [
            "Best {tool_type} for {material}",
            "What {tool_type} do I need for {task}",
            "Recommend {tool_type} for {project}",
            "Which {tool_type} is good for {use_case}",
            "Need {tool_type} for {material} work",
            "{tool_type} suitable for {environment}",
            "Professional vs DIY {tool_type}",
            "Budget {tool_type} for {task}",
            "Heavy duty {tool_type} recommendation",
            "{tool_type} for {frequency} use"
        ]
        
        tools = ["drill", "saw", "screwdriver", "hammer", "measuring tape", "level", "pliers", "wrench"]
        materials = ["concrete", "wood", "metal", "plastic", "tile", "glass", "brick"]
        tasks = ["drilling", "cutting", "measuring", "fastening", "demolition", "assembly"]
        environments = ["humid weather", "outdoor use", "precision work", "heavy duty"]
        
        examples = []
        for _ in range(200):
            template = random.choice(templates)
            query = template.format(
                tool_type=random.choice(tools),
                material=random.choice(materials),
                task=random.choice(tasks),
                project=random.choice(["renovation", "installation", "repair", "construction"]),
                use_case=random.choice(tasks),
                environment=random.choice(environments),
                frequency=random.choice(["occasional", "regular", "professional"])
            )
            
            entities = {
                "tool_category": random.choice(tools),
                "material_type": random.choice(materials),
                "use_frequency": random.choice(["occasional", "regular", "professional"]),
                "budget_range": random.choice(["budget", "mid_range", "premium"])
            }
            
            examples.append(TrainingExample(
                query=query,
                intent="tool_selection",
                entities=entities
            ))
            
        return examples
    
    def generate_product_comparison_queries(self) -> List[TrainingExample]:
        """Generate product comparison intent queries"""
        templates = [
            "{brand1} vs {brand2} {product}",
            "Compare {product1} and {product2}",
            "Which is better: {brand1} or {brand2}",
            "{product} comparison {brand1} {brand2}",
            "Pros and cons {brand1} vs {brand2}",
            "Should I buy {brand1} or {brand2} {product}",
            "Best value: {brand1} vs {brand2}",
            "{brand1} {product} or {brand2} alternative",
            "Quality comparison {product} brands",
            "Price vs performance {brand1} {brand2}"
        ]
        
        brands = ["DeWalt", "Makita", "Bosch", "Black & Decker", "Ryobi", "Milwaukee", "Festool"]
        products = ["drill", "saw", "impact driver", "router", "sander", "grinder", "jigsaw"]
        
        examples = []
        for _ in range(200):
            template = random.choice(templates)
            brand1, brand2 = random.sample(brands, 2)
            product = random.choice(products)
            
            query = template.format(
                brand1=brand1,
                brand2=brand2,
                product=product,
                product1=f"{brand1} {product}",
                product2=f"{brand2} {product}"
            )
            
            entities = {
                "brands": [brand1, brand2],
                "product_category": product,
                "comparison_type": random.choice(["price", "quality", "features", "durability"]),
                "budget_range": random.choice(["budget", "mid_range", "premium"])
            }
            
            examples.append(TrainingExample(
                query=query,
                intent="product_comparison",
                entities=entities
            ))
            
        return examples
    
    def generate_learning_queries(self) -> List[TrainingExample]:
        """Generate learning intent queries"""
        templates = [
            "How to {skill}",
            "Learn to {skill}",
            "Tutorial for {skill}",
            "Step by step {skill}",
            "Guide to {skill}",
            "Beginner {skill} tips",
            "How do I {skill}",
            "Best way to {skill}",
            "{skill} for beginners",
            "Teach me {skill}"
        ]
        
        skills = [
            "install tiles", "paint walls", "use a drill", "measure accurately",
            "cut wood", "install outlets", "fix plumbing", "lay flooring",
            "mount TV", "install shelves", "use power tools", "read blueprints"
        ]
        
        examples = []
        for _ in range(200):
            template = random.choice(templates)
            skill = random.choice(skills)
            
            query = template.format(skill=skill)
            
            entities = {
                "skill_category": skill.split()[0] if skill else "general",
                "difficulty_level": random.choice(["basic", "intermediate", "advanced"]),
                "learning_type": random.choice(["tutorial", "guide", "tips", "course"])
            }
            
            examples.append(TrainingExample(
                query=query,
                intent="learning",
                entities=entities
            ))
            
        return examples
    
    def add_data_augmentation(self, examples: List[TrainingExample]) -> List[TrainingExample]:
        """Add variations and augmented examples"""
        augmented = []
        
        for example in examples:
            # Original example
            augmented.append(example)
            
            # Add variations with different phrasings
            variations = self.create_variations(example.query)
            for variation in variations:
                augmented.append(TrainingExample(
                    query=variation,
                    intent=example.intent,
                    entities=example.entities,
                    confidence=0.9  # Slightly lower confidence for variations
                ))
                
        return augmented
    
    def create_variations(self, query: str) -> List[str]:
        """Create query variations for data augmentation"""
        variations = []
        
        # Add question variations
        if not query.startswith(('How', 'What', 'Which', 'Where', 'When', 'Why')):
            variations.append(f"How to {query.lower()}")
            variations.append(f"What about {query.lower()}")
        
        # Add Singapore-specific variations
        if "my" in query.lower():
            variations.append(query.replace("my", "our HDB"))
            variations.append(query.replace("my", "the condo"))
        
        # Add urgency variations
        if any(word in query.lower() for word in ['fix', 'repair', 'problem']):
            variations.append(f"Urgent: {query}")
            variations.append(f"Need immediate help with {query.lower()}")
        
        return variations[:2]  # Limit to 2 variations per original
    
    def generate_all_training_data(self) -> List[TrainingExample]:
        """Generate complete training dataset"""
        all_examples = []
        
        # Generate base examples for each intent
        all_examples.extend(self.generate_project_planning_queries())
        all_examples.extend(self.generate_problem_solving_queries())
        all_examples.extend(self.generate_tool_selection_queries())
        all_examples.extend(self.generate_product_comparison_queries())
        all_examples.extend(self.generate_learning_queries())
        
        # Add data augmentation
        all_examples = self.add_data_augmentation(all_examples)
        
        # Shuffle the dataset
        random.shuffle(all_examples)
        
        return all_examples
    
    def save_training_data(self, examples: List[TrainingExample], filename: str):
        """Save training data to JSON file"""
        data = []
        for example in examples:
            data.append({
                "query": example.query,
                "intent": example.intent,
                "entities": example.entities,
                "confidence": example.confidence
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(data)} training examples to {filename}")
        
        # Print statistics
        intent_counts = {}
        for example in examples:
            intent_counts[example.intent] = intent_counts.get(example.intent, 0) + 1
        
        print("Intent distribution:")
        for intent, count in intent_counts.items():
            print(f"  {intent}: {count} examples")


if __name__ == "__main__":
    import os
    from pathlib import Path

    generator = DIYTrainingDataGenerator()
    training_data = generator.generate_all_training_data()

    # Save to file - use environment variable or relative path
    project_root = Path(__file__).parent.parent.parent
    output_path = os.getenv(
        'INTENT_TRAINING_DATA_PATH',
        str(project_root / 'src' / 'intent_classification' / 'training_data.json')
    )
    generator.save_training_data(training_data, output_path)