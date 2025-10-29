"""
Mock Kailash SDK for Horme System
Provides basic workflow functionality without the full SDK
"""

class WorkflowBuilder:
    """Mock WorkflowBuilder for basic workflow operations"""
    def __init__(self):
        self.nodes = []
        self.connections = []
    
    def add_node(self, node_type, node_id, params=None):
        """Add a node to the workflow"""
        self.nodes.append({
            'type': node_type,
            'id': node_id,
            'params': params or {}
        })
        return self
    
    def connect(self, from_node, from_output, to_node, to_input):
        """Connect nodes in the workflow"""
        self.connections.append({
            'from': from_node,
            'from_output': from_output,
            'to': to_node,
            'to_input': to_input
        })
        return self
    
    def build(self):
        """Build the workflow"""
        return {
            'nodes': self.nodes,
            'connections': self.connections
        }


class LocalRuntime:
    """Mock LocalRuntime for executing workflows"""
    def __init__(self):
        self.results = {}
    
    def execute(self, workflow, parameters=None):
        """Execute a workflow and return mock results"""
        # Simple mock execution - just process the text
        if parameters and 'parameters' in parameters:
            text = parameters['parameters'].get('TextInput', {}).get('text', '')
            
            # Mock keyword extraction
            keywords = []
            for word in ['plumbing', 'electrical', 'hardware', 'tools', 'supplies', 'renovation']:
                if word.lower() in text.lower():
                    keywords.append(word)
            
            # Mock results
            results = {
                'KeywordExtractor': {
                    'keywords': keywords or ['general', 'supplies']
                },
                'ProductMatcher': {
                    'products': [
                        {
                            'id': 'P001',
                            'name': 'Premium Tool Set',
                            'description': 'Professional grade tools',
                            'price': 299.99,
                            'score': 0.95
                        },
                        {
                            'id': 'P002', 
                            'name': 'Safety Equipment Bundle',
                            'description': 'Complete safety gear',
                            'price': 149.99,
                            'score': 0.85
                        }
                    ]
                }
            }
            return results, 'mock-run-id'
        
        return {}, 'mock-run-id'