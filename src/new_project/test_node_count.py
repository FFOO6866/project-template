import windows_patch  # Must be first
import kailash.nodes
import pkgutil
import inspect

print('Counting unique node classes...')
unique_nodes = set()
for importer, modname, ispkg in pkgutil.walk_packages(kailash.nodes.__path__, 'kailash.nodes.'):
    try:
        module = __import__(modname, fromlist=[''])
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if name.endswith('Node') and hasattr(obj, '__module__') and name != 'Node':
                unique_nodes.add(name)
    except Exception as e:
        pass

print(f'UNIQUE NODES: {len(unique_nodes)} unique node types')
print('Sample unique nodes:')
sorted_nodes = sorted(list(unique_nodes))
for i, node in enumerate(sorted_nodes[:15]):
    print(f'  {i+1}. {node}')
print(f'... and {len(unique_nodes) - 15} more unique nodes')

# Also test if we can create basic workflow
try:
    from kailash.workflow.builder import WorkflowBuilder
    from kailash.runtime.local import LocalRuntime
    
    workflow = WorkflowBuilder()
    print('SUCCESS: WorkflowBuilder can be created')
    
    runtime = LocalRuntime()
    print('SUCCESS: LocalRuntime can be created')
    
except Exception as e:
    print(f'FAILED: Basic workflow creation failed - {e}')