"""
DataFlow Models Import Alias
============================

Simple import alias to maintain compatibility with existing test infrastructure.
The actual DataFlow models are defined in dataflow_classification_models.py.
"""

# Apply Windows compatibility first
import windows_sdk_compatibility

# Import everything from the actual dataflow models file
from dataflow_classification_models import *

# Ensure 'db' is available as expected by tests
from dataflow_classification_models import db