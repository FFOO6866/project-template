"""Check available kailash.nodes modules"""
import windows_patch  # Apply compatibility first
import pkgutil
import kailash.nodes

print("Available nodes modules:")
for importer, modname, ispkg in pkgutil.iter_modules(kailash.nodes.__path__, 'kailash.nodes.'):
    print(f"  {modname}")