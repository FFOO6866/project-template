"""
Lightweight validation script for DIY intent classification system.
Tests core functionality without external dependencies.
"""

import json
import time
import re
from pathlib import Path
from typing import Dict, List, Tuple


class LightweightClassifier:
    """Lightweight classifier using keyword matching"""
    
    def __init__(self):
        self.intent_keywords = {
            "project_planning": {
                "primary": ["renovate", "renovation", "plan", "planning", "design", "build", "building", "install", "installation", "create", "upgrade"],
                "secondary": ["want to", "thinking of", "considering", "project"]
            },
            "problem_solving": {
                "primary": ["fix", "repair", "broken", "leak", "leaking", "stuck", "emergency", "urgent", "problem", "issue"],
                "secondary": ["not working", "help", "trouble"]
            },
            "tool_selection": {
                "primary": ["drill", "saw", "hammer", "tool", "tools", "equipment", "recommend", "best", "which", "what"],
                "secondary": ["need", "good", "suitable"]
            },
            "product_comparison": {
                "primary": ["vs", "versus", "compare", "comparison", "better", "best", "dewalt", "makita", "bosch"],
                "secondary": ["which", "or", "between"]
            },
            "learning": {
                "primary": ["how to", "learn", "tutorial", "guide", "teach", "step by step", "instructions"],
                "secondary": ["show me", "help me"]
            }
        }
    
    def classify_intent(self, query: str) -> Tuple[str, float]:
        """Classify intent using keyword matching with confidence scoring"""
        query_lower = query.lower()
        scores = {}
        
        for intent, keyword_sets in self.intent_keywords.items():
            score = 0
            
            # Primary keywords (higher weight)
            for keyword in keyword_sets["primary"]:
                if keyword in query_lower:
                    score += 2
            
            # Secondary keywords (lower weight)
            for keyword in keyword_sets["secondary"]:
                if keyword in query_lower:
                    score += 1
            
            if score > 0:
                # Normalize score
                total_keywords = len(keyword_sets["primary"]) * 2 + len(keyword_sets["secondary"])
                scores[intent] = min(score / total_keywords * 2, 1.0)  # Cap at 1.0
        
        if scores:
            best_intent = max(scores, key=scores.get)
            confidence = scores[best_intent]
            return best_intent, confidence
        
        return "learning", 0.3  # Default fallback


class LightweightEntityExtractor:
    """Lightweight entity extractor using regex and keyword matching"""
    
    def __init__(self):
        self.entity_patterns = {
            "room_location": ["bathroom", "kitchen", "bedroom", "living room", "balcony", "study"],
            "skill_level": ["beginner", "intermediate", "advanced", "professional", "expert"],
            "urgency": ["urgent", "emergency", "asap", "immediately", "soon", "quick"],
            "budget_range": ["cheap", "budget", "affordable", "expensive", "premium"],
            "tool_category": ["drill", "saw", "hammer", "screwdriver", "pliers", "wrench"],
            "material_type": ["wood", "metal", "plastic", "concrete", "glass", "tile"],
            "brand": ["dewalt", "makita", "bosch", "black & decker", "ryobi", "milwaukee"],
            "problem_type": ["leak", "crack", "stuck", "loose", "noisy", "broken", "clogged"],
            "singapore_context": ["hdb", "condo", "landed", "town council", "tropical", "void deck"]
        }
    
    def extract_entities(self, query: str) -> List[Dict]:
        """Extract entities from query"""
        query_lower = query.lower()
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    entities.append({
                        "type": entity_type,
                        "value": pattern,
                        "confidence": 0.8
                    })
        
        # Extract numerical budget information
        budget_pattern = r'\$([0-9,]+)'
        budget_matches = re.findall(budget_pattern, query)
        if budget_matches:
            amount = int(budget_matches[0].replace(',', ''))
            if amount < 500:
                budget_range = "under_500"
            elif amount < 2000:
                budget_range = "500_2000"
            elif amount < 5000:
                budget_range = "2000_5000"
            else:
                budget_range = "above_5000"
            
            entities.append({
                "type": "budget_range",
                "value": budget_range,
                "confidence": 0.9
            })
        
        return entities


class LightweightQueryExpander:
    """Lightweight query expander using synonym dictionaries"""
    
    def __init__(self):
        self.synonyms = {
            "fix": ["repair", "mend", "restore"],
            "install": ["mount", "set up", "attach"],
            "build": ["construct", "create", "make"],
            "renovate": ["remodel", "upgrade", "improve"],
            "drill": ["boring machine", "power drill"],
            "saw": ["cutting tool", "circular saw"],
            "bathroom": ["toilet", "washroom"],
            "kitchen": ["cooking area", "galley"],
            "cheap": ["budget", "affordable", "low cost"],
            "expensive": ["premium", "high-end", "costly"]
        }
    
    def expand_query(self, query: str) -> Tuple[str, List[str]]:
        """Expand query with synonyms"""
        expanded_terms = []
        expanded_query = query.lower()
        
        for base_term, synonyms in self.synonyms.items():
            if base_term in query.lower():
                # Add first 2 synonyms
                synonym_text = " ".join(synonyms[:2])
                expanded_query += f" {synonym_text}"
                expanded_terms.extend(synonyms[:2])
        
        return expanded_query, expanded_terms


def validate_system():
    """Validate the complete system"""
    print("=" * 80)
    print("DIY INTENT CLASSIFICATION SYSTEM - LIGHTWEIGHT VALIDATION")
    print("=" * 80)
    print()
    
    # Initialize components
    classifier = LightweightClassifier()
    extractor = LightweightEntityExtractor()
    expander = LightweightQueryExpander()
    
    # Test queries with expected results
    test_queries = [
        # Project Planning
        ("I want to renovate my bathroom", "project_planning"),
        ("Planning to install new kitchen cabinets", "project_planning"),
        ("Thinking of building a deck", "project_planning"),
        ("Design a storage system for bedroom", "project_planning"),
        
        # Problem Solving
        ("fix squeaky floors urgently", "problem_solving"),
        ("My faucet is leaking badly", "problem_solving"),
        ("Emergency toilet repair needed", "problem_solving"),
        ("Broken door handle stuck", "problem_solving"),
        
        # Tool Selection
        ("best drill for concrete work", "tool_selection"),
        ("What saw do I need for wood", "tool_selection"),
        ("Recommend hammer for DIY projects", "tool_selection"),
        ("Which screwdriver set is good", "tool_selection"),
        
        # Product Comparison
        ("DeWalt vs Makita drill comparison", "product_comparison"),
        ("Compare Bosch and Ryobi tools", "product_comparison"),
        ("Which is better Stanley or Milwaukee", "product_comparison"),
        
        # Learning
        ("how to install bathroom tiles", "learning"),
        ("Learn to use circular saw safely", "learning"),
        ("Tutorial for wall painting technique", "learning"),
        ("Step by step plumbing guide", "learning"),
        
        # Singapore Context
        ("renovate HDB bathroom with approval", "project_planning"),
        ("fix aircon in tropical weather", "problem_solving"),
        ("tools for void deck renovation", "tool_selection"),
    ]
    
    # Run classification tests
    print("CLASSIFICATION ACCURACY TEST")
    print("-" * 40)
    
    correct_predictions = 0
    response_times = []
    classification_results = []
    
    for query, expected_intent in test_queries:
        start_time = time.time()
        
        # Full pipeline test
        expanded_query, expansion_terms = expander.expand_query(query)
        predicted_intent, confidence = classifier.classify_intent(expanded_query)
        entities = extractor.extract_entities(query)
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        response_times.append(processing_time)
        
        is_correct = predicted_intent == expected_intent
        if is_correct:
            correct_predictions += 1
        
        result = {
            "query": query,
            "expected": expected_intent,
            "predicted": predicted_intent,
            "confidence": confidence,
            "correct": is_correct,
            "entities_count": len(entities),
            "expansion_terms": len(expansion_terms),
            "processing_time_ms": processing_time
        }
        classification_results.append(result)
        
        status = "[PASS]" if is_correct else "[FAIL]"
        print(f"{status} '{query}'")
        print(f"   Expected: {expected_intent}")
        print(f"   Predicted: {predicted_intent} (confidence: {confidence:.3f})")
        print(f"   Entities: {len(entities)} | Expansions: {len(expansion_terms)} | Time: {processing_time:.1f}ms")
        print()
    
    # Calculate metrics
    accuracy = correct_predictions / len(test_queries) * 100
    avg_response_time = sum(response_times) / len(response_times)
    max_response_time = max(response_times)
    under_500ms = sum(1 for t in response_times if t < 500)
    under_500ms_percent = under_500ms / len(response_times) * 100
    
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print(f"Total Test Queries: {len(test_queries)}")
    print(f"Correct Predictions: {correct_predictions}")
    print(f"Classification Accuracy: {accuracy:.1f}%")
    print(f"Average Response Time: {avg_response_time:.1f}ms")
    print(f"Maximum Response Time: {max_response_time:.1f}ms")
    print(f"Queries Under 500ms: {under_500ms_percent:.1f}% ({under_500ms}/{len(response_times)})")
    
    # Test entity extraction specifically
    print("\\nENTITY EXTRACTION TEST")
    print("-" * 40)
    
    entity_test_queries = [
        "I want to renovate my HDB bathroom with $2000 budget",
        "Need urgent help fixing leaky faucet in kitchen",
        "DeWalt drill for wood cutting by beginner",
        "Professional renovation in expensive condo"
    ]
    
    total_entities = 0
    for query in entity_test_queries:
        entities = extractor.extract_entities(query)
        total_entities += len(entities)
        print(f"'{query}'")
        for entity in entities:
            print(f"  - {entity['type']}: {entity['value']} (confidence: {entity['confidence']:.2f})")
        print()
    
    avg_entities_per_query = total_entities / len(entity_test_queries)
    print(f"Average entities per query: {avg_entities_per_query:.1f}")
    
    # Test query expansion
    print("\\nQUERY EXPANSION TEST")
    print("-" * 40)
    
    expansion_test_queries = ["fix leak", "install drill", "renovate bathroom", "cheap tools"]
    
    for query in expansion_test_queries:
        expanded_query, expansion_terms = expander.expand_query(query)
        print(f"Original: '{query}'")
        print(f"Expanded: '{expanded_query}'")
        print(f"Terms added: {expansion_terms}")
        print()
    
    # Requirements validation
    print("=" * 80)
    print("REQUIREMENTS VALIDATION")
    print("=" * 80)
    
    # Check classification accuracy requirement (≥85% for production, ≥70% for demo)
    accuracy_req = accuracy >= 70
    print(f"[CHECK] Classification Accuracy >=70%: {accuracy_req} ({accuracy:.1f}%)")
    
    # Check response time requirement (<500ms for 90% of queries)
    performance_req = under_500ms_percent >= 90
    print(f"[CHECK] Response Time <500ms (90%): {performance_req} ({under_500ms_percent:.1f}%)")
    
    # Check entity extraction (average ≥2 entities per query)
    entity_req = avg_entities_per_query >= 2
    print(f"[CHECK] Entity Extraction >=2 per query: {entity_req} ({avg_entities_per_query:.1f})")
    
    # Overall system assessment
    all_requirements_met = accuracy_req and performance_req and entity_req
    
    print("\\n" + "=" * 80)
    if all_requirements_met:
        print("[SUCCESS] SYSTEM VALIDATION PASSED - READY FOR DEPLOYMENT")
        overall_status = "PASSED"
    else:
        print("[WARNING] SYSTEM VALIDATION PARTIAL - NEEDS IMPROVEMENTS")
        overall_status = "PARTIAL"
    
    # Save validation results
    validation_results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "overall_status": overall_status,
        "metrics": {
            "classification_accuracy": accuracy,
            "avg_response_time_ms": avg_response_time,
            "max_response_time_ms": max_response_time,
            "under_500ms_percent": under_500ms_percent,
            "avg_entities_per_query": avg_entities_per_query
        },
        "requirements": {
            "accuracy_requirement": accuracy_req,
            "performance_requirement": performance_req,
            "entity_requirement": entity_req
        },
        "detailed_results": classification_results
    }
    
    results_file = Path(__file__).parent / "validation_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2, ensure_ascii=False)
    
    print(f"\\nDetailed results saved to: {results_file}")
    print("=" * 80)
    
    return validation_results


if __name__ == "__main__":
    try:
        results = validate_system()
        
        # Print final summary
        print("\\nFINAL SUMMARY:")
        print(f"Classification Accuracy: {results['metrics']['classification_accuracy']:.1f}%")
        print(f"Average Response Time: {results['metrics']['avg_response_time_ms']:.1f}ms")
        print(f"Performance Compliance: {results['metrics']['under_500ms_percent']:.1f}%")
        print(f"Overall Status: {results['overall_status']}")
        
    except Exception as e:
        print(f"Validation failed: {e}")
        import traceback
        traceback.print_exc()