"""
Development-only Windows compatibility patch.
This is NOT included in Docker containers (Linux-only).
Only used for local development and testing.
"""

import sys
import platform

# Only apply on Windows for development
if platform.system() == "Windows":
    try:
        # Mock the resource module for Windows development
        import types
        resource = types.ModuleType('resource')
        
        # Add basic resource constants
        resource.RLIMIT_CPU = 0
        resource.RLIMIT_FSIZE = 1
        resource.RLIMIT_DATA = 2
        resource.RLIMIT_STACK = 3
        resource.RLIMIT_CORE = 4
        resource.RLIMIT_RSS = 5
        resource.RLIMIT_NPROC = 6
        resource.RLIMIT_NOFILE = 7
        resource.RLIMIT_MEMLOCK = 8
        resource.RLIMIT_AS = 9
        
        # Mock functions that return safe defaults
        def getrlimit(resource_type):
            return (65536, 65536)  # soft limit, hard limit
            
        def setrlimit(resource_type, limits):
            pass  # No-op on Windows
            
        def getrusage(who):
            # Return mock usage statistics
            Usage = types.SimpleNamespace()
            usage = Usage()
            usage.ru_utime = 0.0
            usage.ru_stime = 0.0
            usage.ru_maxrss = 1024
            usage.ru_ixrss = 0
            usage.ru_idrss = 0
            usage.ru_isrss = 0
            usage.ru_minflt = 0
            usage.ru_majflt = 0
            usage.ru_nswap = 0
            usage.ru_inblock = 0
            usage.ru_oublock = 0
            usage.ru_msgsnd = 0
            usage.ru_msgrcv = 0
            usage.ru_nsignals = 0
            usage.ru_nvcsw = 0
            usage.ru_nivcsw = 0
            return usage
            
        resource.getrlimit = getrlimit
        resource.setrlimit = setrlimit
        resource.getrusage = getrusage
        resource.RUSAGE_SELF = 0
        resource.RUSAGE_CHILDREN = -1
        
        # Add to sys.modules
        sys.modules['resource'] = resource
        
        print("Development Windows compatibility enabled")
        
    except Exception as e:
        print(f"Warning: Could not apply Windows compatibility: {e}")