#!/usr/bin/env python3
"""
SDK-compliant background processing workflow
Converts TypeScript background processing to proper Kailash SDK patterns
"""

from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime
import json
import os
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import hashlib
import asyncio

@dataclass
class StoredFile:
    id: str
    original_name: str
    stored_path: str
    size: int
    mime_type: str
    uploaded_at: str
    checksum: str

@dataclass 
class ProcessingStatus:
    id: str
    status: str  # 'processing' | 'completed' | 'error'
    progress: int
    message: str
    context_id: Optional[str] = None
    start_time: Optional[str] = None
    completed_time: Optional[str] = None
    error: Optional[str] = None
    files_processed: int = 0
    total_files: int = 0
    items_extracted: int = 0
    products_matched: int = 0

class BackgroundProcessingWorkflow:
    """SDK-compliant background processing using proper workflow patterns"""
    
    def __init__(self, base_dir: str = None):
        # Essential pattern: proper runtime initialization
        self.runtime = LocalRuntime()
        self.base_dir = base_dir or os.path.join(os.getcwd(), 'uploads')
    
    def create_file_processing_workflow(self, stored_files: List[StoredFile], processing_id: str) -> WorkflowBuilder:
        """Create SDK-compliant file processing workflow"""
        workflow = WorkflowBuilder()
        
        # Node 1: File validation and initialization
        workflow.add_node("PythonCodeNode", "file_validator", {
            "code": """
import os
import json
from typing import List, Dict, Any

def validate_stored_files(stored_files_data: List[Dict], processing_id: str) -> Dict[str, Any]:
    '''Validate stored files and initialize processing'''
    
    valid_files = []
    invalid_files = []
    total_size = 0
    
    for file_data in stored_files_data:
        file_path = file_data.get('stored_path', '')
        
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            if file_size > 0:
                valid_files.append({
                    'id': file_data.get('id', ''),
                    'original_name': file_data.get('original_name', ''),
                    'stored_path': file_path,
                    'size': file_size,
                    'mime_type': file_data.get('mime_type', ''),
                    'checksum': file_data.get('checksum', '')
                })
                total_size += file_size
            else:
                invalid_files.append(f"{file_data.get('original_name', 'unknown')}: Empty file")
        else:
            invalid_files.append(f"{file_data.get('original_name', 'unknown')}: File not found")
    
    return {
        'processing_id': processing_id,
        'valid_files': valid_files,
        'invalid_files': invalid_files,
        'total_files': len(valid_files),
        'total_size_bytes': total_size,
        'validation_errors': invalid_files
    }

result = validate_stored_files(stored_files_data, processing_id)
"""
        })
        
        # Node 2: File content extraction
        workflow.add_node("PythonCodeNode", "content_extractor", {
            "code": """
import os
from typing import List, Dict, Any

def extract_file_contents(validation_result: Dict[str, Any]) -> Dict[str, Any]:
    '''Extract content from validated files'''
    
    extracted_contents = []
    total_items = 0
    processing_errors = []
    
    for file_info in validation_result.get('valid_files', []):
        file_path = file_info['stored_path']
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract items from content (simplified item detection)
            lines = content.split('\\n')
            items = []
            
            for line_num, line in enumerate(lines):
                line = line.strip()
                if line and len(line) > 10:
                    # Basic item detection - look for patterns
                    if ':' in line or '$' in line or any(char.isdigit() for char in line):
                        items.append({
                            'text': line,
                            'line_number': line_num + 1,
                            'source_file': file_info['original_name']
                        })
            
            extracted_contents.append({
                'file_id': file_info['id'],
                'original_name': file_info['original_name'],
                'content_preview': content[:1000],  # First 1000 chars
                'items_extracted': len(items),
                'items': items
            })
            
            total_items += len(items)
            
        except Exception as e:
            processing_errors.append(f"Failed to extract {file_info['original_name']}: {str(e)}")
    
    return {
        'processing_id': validation_result['processing_id'],
        'extracted_contents': extracted_contents,
        'total_items_extracted': total_items,
        'files_processed': len(extracted_contents),
        'extraction_errors': processing_errors
    }

result = extract_file_contents(validation_result)
"""
        })
        
        # Node 3: Status tracking and progress updates
        workflow.add_node("PythonCodeNode", "status_updater", {
            "code": """
import json
import time
from typing import Dict, Any

def update_processing_status(extraction_result: Dict[str, Any]) -> Dict[str, Any]:
    '''Update processing status with extraction results'''
    
    processing_id = extraction_result['processing_id']
    files_processed = extraction_result['files_processed']
    items_extracted = extraction_result['total_items_extracted']
    
    # Calculate progress (40% after file processing)
    progress = min(40, int((files_processed / max(files_processed, 1)) * 40))
    
    status_update = {
        'id': processing_id,
        'status': 'processing',
        'progress': progress,
        'message': f'Processed {files_processed} files, extracted {items_extracted} items',
        'files_processed': files_processed,
        'items_extracted': items_extracted,
        'updated_at': time.time()
    }
    
    return {
        'processing_id': processing_id,
        'status_update': status_update,
        'extraction_data': extraction_result,
        'ready_for_context_creation': files_processed > 0 and items_extracted > 0
    }

result = update_processing_status(extraction_result)
"""
        })
        
        # Node 4: Context creation for chat integration
        workflow.add_node("PythonCodeNode", "context_creator", {
            "code": """
import json
import time
from typing import Dict, Any, List

def create_chat_context(status_update_result: Dict[str, Any]) -> Dict[str, Any]:
    '''Create chat context from extracted file contents'''
    
    extraction_data = status_update_result['extraction_data']
    processing_id = status_update_result['processing_id']
    
    if not status_update_result.get('ready_for_context_creation', False):
        return {
            'processing_id': processing_id,
            'context_created': False,
            'error': 'No valid content for context creation',
            'context_id': None
        }
    
    # Prepare context data
    context_files = []
    total_items = 0
    
    for content_info in extraction_data.get('extracted_contents', []):
        context_files.append({
            'name': content_info['original_name'],
            'type': 'text/plain',  # Simplified
            'content': content_info['content_preview'],
            'items_count': content_info['items_extracted']
        })
        total_items += content_info['items_extracted']
    
    # Generate mock context ID (in production would call actual API)
    context_id = f"ctx_{processing_id}_{int(time.time())}"
    
    context_data = {
        'context_id': context_id,
        'files': context_files,
        'total_files': len(context_files),
        'total_items': total_items,
        'created_at': time.time()
    }
    
    return {
        'processing_id': processing_id,
        'context_created': True,
        'context_id': context_id,
        'context_data': context_data,
        'items_for_matching': total_items
    }

result = create_chat_context(status_update_result)
"""
        })
        
        # Node 5: Product matching simulation
        workflow.add_node("PythonCodeNode", "product_matcher", {
            "code": """
import time
import random
from typing import Dict, Any

def simulate_product_matching(context_result: Dict[str, Any]) -> Dict[str, Any]:
    '''Simulate product matching process'''
    
    processing_id = context_result['processing_id']
    context_id = context_result.get('context_id')
    items_count = context_result.get('items_for_matching', 0)
    
    if not context_result.get('context_created', False):
        return {
            'processing_id': processing_id,
            'context_id': context_id,
            'products_matched': 0,
            'matching_completed': False,
            'error': 'No context available for product matching'
        }
    
    # Simulate matching process with realistic timing
    time.sleep(0.1)  # Simulate processing time
    
    # Simulate product matches (in production would query actual database)
    match_rate = 0.6  # 60% of items typically find matches
    products_matched = int(items_count * match_rate) + random.randint(0, 5)
    
    matching_results = {
        'total_items_processed': items_count,
        'products_matched': products_matched,
        'match_rate': products_matched / max(items_count, 1),
        'matching_confidence': 0.85,
        'processing_time_ms': 100
    }
    
    return {
        'processing_id': processing_id,
        'context_id': context_id,
        'products_matched': products_matched,
        'matching_completed': True,
        'matching_results': matching_results
    }

result = simulate_product_matching(context_result)
"""
        })
        
        # Node 6: Final status completion
        workflow.add_node("PythonCodeNode", "completion_handler", {
            "code": """
import time
from typing import Dict, Any

def complete_processing(matching_result: Dict[str, Any]) -> Dict[str, Any]:
    '''Complete the processing workflow with final status'''
    
    processing_id = matching_result['processing_id']
    context_id = matching_result.get('context_id')
    products_matched = matching_result.get('products_matched', 0)
    
    # Calculate final results
    completion_time = time.time()
    
    if matching_result.get('matching_completed', False):
        final_status = {
            'id': processing_id,
            'status': 'completed',
            'progress': 100,
            'message': f'Processing complete! {products_matched} products matched.',
            'context_id': context_id,
            'products_matched': products_matched,
            'completed_time': completion_time,
            'success': True
        }
    else:
        final_status = {
            'id': processing_id,
            'status': 'error',
            'progress': 60,
            'message': 'Processing failed during product matching',
            'context_id': context_id,
            'products_matched': 0,
            'completed_time': completion_time,
            'success': False,
            'error': matching_result.get('error', 'Unknown matching error')
        }
    
    return {
        'processing_id': processing_id,
        'final_status': final_status,
        'workflow_completed': True,
        'execution_summary': {
            'context_created': context_id is not None,
            'products_matched': products_matched,
            'success': final_status['success']
        }
    }

result = complete_processing(matching_result)
"""
        })
        
        # Connect workflow nodes using 4-parameter connections (ESSENTIAL PATTERN)
        workflow.add_connection("file_validator", "result", "content_extractor", "validation_result")
        workflow.add_connection("content_extractor", "result", "status_updater", "extraction_result") 
        workflow.add_connection("status_updater", "result", "context_creator", "status_update_result")
        workflow.add_connection("context_creator", "result", "product_matcher", "context_result")
        workflow.add_connection("product_matcher", "result", "completion_handler", "matching_result")
        
        return workflow
    
    async def process_files_background(self, stored_files: List[StoredFile], processing_id: str) -> Dict[str, Any]:
        """Execute background processing workflow with essential SDK pattern"""
        
        try:
            # Create workflow with proper SDK patterns
            workflow = self.create_file_processing_workflow(stored_files, processing_id)
            
            # Convert stored files to serializable format
            stored_files_data = [
                {
                    'id': f.id,
                    'original_name': f.original_name,
                    'stored_path': f.stored_path,
                    'size': f.size,
                    'mime_type': f.mime_type,
                    'checksum': f.checksum
                }
                for f in stored_files
            ]
            
            # ESSENTIAL PATTERN: runtime.execute(workflow.build())
            results, run_id = self.runtime.execute(workflow.build(), {
                "file_validator": {
                    "stored_files_data": stored_files_data,
                    "processing_id": processing_id
                }
            })
            
            # Extract final results from workflow execution
            completion_result = results.get('completion_handler', {})
            final_status = completion_result.get('final_status', {})
            
            return {
                'success': final_status.get('success', False),
                'processing_id': processing_id,
                'run_id': run_id,
                'final_status': final_status,
                'workflow_summary': completion_result.get('execution_summary', {}),
                'nodes_executed': list(results.keys())
            }
            
        except Exception as e:
            return {
                'success': False,
                'processing_id': processing_id,
                'error': f'Background processing workflow failed: {str(e)}',
                'workflow_summary': {'error': True}
            }
    
    def create_file_storage_workflow(self, files_data: List[Dict[str, Any]]) -> WorkflowBuilder:
        """Create SDK-compliant file storage workflow"""
        workflow = WorkflowBuilder()
        
        # Node 1: File validation
        workflow.add_node("PythonCodeNode", "file_validator", {
            "code": """
import os
from typing import List, Dict, Any

def validate_files(files_data: List[Dict[str, Any]], base_dir: str) -> Dict[str, Any]:
    '''Validate uploaded files before storage'''
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_TYPES = [
        'text/plain', 'text/csv', 'application/json',
        'application/pdf', 'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ]
    
    valid_files = []
    validation_errors = []
    
    for file_data in files_data:
        name = file_data.get('name', '')
        size = file_data.get('size', 0)
        mime_type = file_data.get('type', '')
        
        # Validate file size
        if size > MAX_FILE_SIZE:
            validation_errors.append(f"{name}: File size exceeds 50MB limit")
            continue
        
        # Validate file type
        if mime_type not in ALLOWED_TYPES:
            validation_errors.append(f"{name}: File type {mime_type} not allowed")
            continue
        
        # Validate file name
        if not name or len(name.strip()) == 0:
            validation_errors.append("File name cannot be empty")
            continue
        
        valid_files.append({
            'name': name,
            'size': size,
            'mime_type': mime_type,
            'content': file_data.get('content', ''),
            'validated': True
        })
    
    return {
        'valid_files': valid_files,
        'validation_errors': validation_errors,
        'total_valid': len(valid_files),
        'total_invalid': len(validation_errors)
    }

result = validate_files(files_data, base_dir)
"""
        })
        
        # Node 2: File storage
        workflow.add_node("PythonCodeNode", "file_storer", {
            "code": """
import os
import hashlib
import time
from typing import List, Dict, Any

def store_files(validation_result: Dict[str, Any], base_dir: str) -> Dict[str, Any]:
    '''Store validated files to disk'''
    
    stored_files = []
    storage_errors = []
    
    # Create base directory
    os.makedirs(base_dir, exist_ok=True)
    
    # Create date-based subdirectory
    today = time.strftime('%Y-%m-%d')
    today_dir = os.path.join(base_dir, today)
    os.makedirs(today_dir, exist_ok=True)
    
    for file_info in validation_result.get('valid_files', []):
        try:
            # Generate unique file ID
            timestamp = int(time.time() * 1000)
            random_part = str(hash(file_info['name'] + str(timestamp)))[-6:]
            file_id = f"file_{timestamp}_{random_part}"
            
            # Generate safe filename
            original_name = file_info['name']
            extension = os.path.splitext(original_name)[1]
            safe_filename = f"{file_id}_{original_name.replace(' ', '_').replace('/', '_')}"
            
            stored_path = os.path.join(today_dir, safe_filename)
            
            # Write file content
            content = file_info.get('content', '')
            with open(stored_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Calculate checksum
            checksum = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            stored_files.append({
                'id': file_id,
                'original_name': original_name,
                'stored_path': stored_path,
                'size': file_info['size'],
                'mime_type': file_info['mime_type'],
                'uploaded_at': time.time(),
                'checksum': checksum
            })
            
        except Exception as e:
            storage_errors.append(f"Failed to store {file_info['name']}: {str(e)}")
    
    return {
        'stored_files': stored_files,
        'storage_errors': storage_errors,
        'files_stored': len(stored_files),
        'storage_success': len(storage_errors) == 0
    }

result = store_files(validation_result, base_dir)
"""
        })
        
        # Connect storage workflow nodes
        workflow.add_connection("file_validator", "result", "file_storer", "validation_result")
        
        return workflow
    
    async def store_files(self, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute file storage workflow with essential SDK pattern"""
        
        try:
            # Create storage workflow
            workflow = self.create_file_storage_workflow(files_data)
            
            # ESSENTIAL PATTERN: runtime.execute(workflow.build())
            results, run_id = self.runtime.execute(workflow.build(), {
                "file_validator": {
                    "files_data": files_data,
                    "base_dir": self.base_dir
                }
            })
            
            # Extract results from workflow execution
            storage_result = results.get('file_storer', {})
            
            return {
                'success': storage_result.get('storage_success', False),
                'stored_files': storage_result.get('stored_files', []),
                'storage_errors': storage_result.get('storage_errors', []),
                'files_stored': storage_result.get('files_stored', 0),
                'run_id': run_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'stored_files': [],
                'storage_errors': [f'File storage workflow failed: {str(e)}'],
                'files_stored': 0
            }

# Export for compatibility with existing code
background_processor = BackgroundProcessingWorkflow()

async def process_files_in_background(stored_files: List[StoredFile], processing_id: str) -> Dict[str, Any]:
    """SDK-compliant background processing entry point"""
    return await background_processor.process_files_background(stored_files, processing_id)

async def store_uploaded_files(files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """SDK-compliant file storage entry point"""  
    return await background_processor.store_files(files_data)

if __name__ == "__main__":
    # Demo usage
    import asyncio
    
    async def demo():
        # Test file storage
        test_files = [
            {
                'name': 'test_document.txt',
                'size': 1024,
                'type': 'text/plain',
                'content': 'Sample document content with items:\nItem 1: Product A - $10.99\nItem 2: Product B - $15.50'
            }
        ]
        
        storage_result = await store_uploaded_files(test_files)
        print("Storage Result:", json.dumps(storage_result, indent=2))
        
        if storage_result.get('success') and storage_result.get('stored_files'):
            # Test background processing
            stored_files = [
                StoredFile(
                    id=sf['id'],
                    original_name=sf['original_name'],
                    stored_path=sf['stored_path'],
                    size=sf['size'],
                    mime_type=sf['mime_type'],
                    uploaded_at=str(sf['uploaded_at']),
                    checksum=sf['checksum']
                )
                for sf in storage_result['stored_files']
            ]
            
            processing_result = await process_files_in_background(stored_files, "demo_proc_123")
            print("Processing Result:", json.dumps(processing_result, indent=2))
    
    asyncio.run(demo())