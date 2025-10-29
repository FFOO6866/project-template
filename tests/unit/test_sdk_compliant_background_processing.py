#!/usr/bin/env python3
"""
Tier 1 Unit Tests for SDK-Compliant Background Processing Workflow
Tests individual node functionality with real implementations (NO MOCKING)
Target: <1 second execution per test
"""

import pytest
import time
import tempfile
import os
import json
from typing import Dict, Any, List
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Test timeout decorator for Tier 1 compliance
def test_timeout(func):
    """Decorator to ensure tests complete within 1 second"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Test {func.__name__} took {execution_time:.3f}s (must be <1s)"
        return result
    return wrapper

class TestBackgroundProcessingNodes:
    """Test individual nodes in background processing workflow with real implementations"""
    
    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory for file operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def runtime(self):
        """Create LocalRuntime instance"""
        return LocalRuntime()
    
    @pytest.fixture
    def sample_files_data(self, temp_directory):
        """Create sample files for testing"""
        files_data = []
        
        # Create test files with real content
        for i in range(3):
            file_path = os.path.join(temp_directory, f"test_file_{i}.txt")
            content = f"""Test file {i} content
Item 1: Product A - $10.99
Item 2: Product B - $15.50
Item 3: Service C - $25.00
Additional content line {i}
More test data for processing"""
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            files_data.append({
                'id': f'file_{i}',
                'original_name': f'test_file_{i}.txt',
                'stored_path': file_path,
                'size': len(content.encode('utf-8')),
                'mime_type': 'text/plain',
                'checksum': f'hash_{i}'
            })
        
        return files_data
    
    @test_timeout
    def test_file_validator_node_valid_files(self, runtime, sample_files_data):
        """Test file validator node with valid files"""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "file_validator", {
            "code": """
import os
def validate_stored_files(stored_files_data, processing_id):
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
    
    result = {
        'processing_id': processing_id,
        'valid_files': valid_files,
        'invalid_files': invalid_files,
        'total_files': len(valid_files),
        'total_size_bytes': total_size,
        'validation_errors': invalid_files
    }
"""
        })
        
        results, run_id = runtime.execute(workflow.build(), {
            "file_validator": {
                "stored_files_data": sample_files_data,
                "processing_id": "test_proc_123"
            }
        })
        
        result = results.get('file_validator', {})
        
        # Validate file validation results
        assert result['processing_id'] == 'test_proc_123'
        assert result['total_files'] == 3
        assert len(result['valid_files']) == 3
        assert len(result['invalid_files']) == 0
        assert result['total_size_bytes'] > 0
        
        # Validate file structure
        first_file = result['valid_files'][0]
        assert 'id' in first_file
        assert 'original_name' in first_file
        assert 'stored_path' in first_file
        assert 'size' in first_file
        assert first_file['size'] > 0
    
    @test_timeout
    def test_file_validator_node_missing_files(self, runtime):
        """Test file validator node with missing files"""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "file_validator", {
            "code": """
import os
def validate_stored_files(stored_files_data, processing_id):
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
    
    result = {
        'processing_id': processing_id,
        'valid_files': valid_files,
        'invalid_files': invalid_files,
        'total_files': len(valid_files),
        'total_size_bytes': total_size,
        'validation_errors': invalid_files
    }
"""
        })
        
        # Test with non-existent files
        invalid_files_data = [
            {
                'id': 'missing_1',
                'original_name': 'missing_file.txt',
                'stored_path': '/nonexistent/path/file.txt',
                'size': 1000,
                'mime_type': 'text/plain',
                'checksum': 'hash_missing'
            }
        ]
        
        results, run_id = runtime.execute(workflow.build(), {
            "file_validator": {
                "stored_files_data": invalid_files_data,
                "processing_id": "test_invalid"
            }
        })
        
        result = results.get('file_validator', {})
        
        # Validate error handling
        assert result['total_files'] == 0
        assert len(result['valid_files']) == 0
        assert len(result['invalid_files']) == 1
        assert 'File not found' in result['invalid_files'][0]
    
    @test_timeout
    def test_content_extractor_node_functionality(self, runtime, sample_files_data):
        """Test content extractor node with real file content"""
        workflow = WorkflowBuilder()
        
        # First validate files
        workflow.add_node("PythonCodeNode", "file_validator", {
            "code": """
import os
def validate_stored_files(stored_files_data, processing_id):
    valid_files = []
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
    result = {
        'processing_id': processing_id,
        'valid_files': valid_files
    }
"""
        })
        
        # Then extract content
        workflow.add_node("PythonCodeNode", "content_extractor", {
            "code": """
import os
def extract_file_contents(validation_result):
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
    
    result = {
        'processing_id': validation_result['processing_id'],
        'extracted_contents': extracted_contents,
        'total_items_extracted': total_items,
        'files_processed': len(extracted_contents),
        'extraction_errors': processing_errors
    }
"""
        })
        
        # Connect nodes
        workflow.add_connection("file_validator", "result", "content_extractor", "validation_result")
        
        results, run_id = runtime.execute(workflow.build(), {
            "file_validator": {
                "stored_files_data": sample_files_data,
                "processing_id": "extract_test"
            }
        })
        
        result = results.get('content_extractor', {})
        
        # Validate content extraction
        assert result['processing_id'] == 'extract_test'
        assert result['files_processed'] == 3
        assert result['total_items_extracted'] > 0  # Should find items with $ and :
        assert len(result['extraction_errors']) == 0
        
        # Validate extracted content structure
        first_content = result['extracted_contents'][0]
        assert 'file_id' in first_content
        assert 'original_name' in first_content
        assert 'content_preview' in first_content
        assert 'items_extracted' in first_content
        assert len(first_content['content_preview']) > 0
        
        # Should find items with patterns like "Item 1: Product A - $10.99"
        assert any(item for content in result['extracted_contents'] 
                  for item in content['items'] if '$' in item['text'])
    
    @test_timeout
    def test_status_updater_node_functionality(self, runtime):
        """Test status updater node with processing results"""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "status_updater", {
            "code": """
import time
def update_processing_status(extraction_result):
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
    
    result = {
        'processing_id': processing_id,
        'status_update': status_update,
        'extraction_data': extraction_result,
        'ready_for_context_creation': files_processed > 0 and items_extracted > 0
    }
"""
        })
        
        # Test status update with sample extraction result
        extraction_result = {
            'processing_id': 'status_test',
            'files_processed': 2,
            'total_items_extracted': 8,
            'extraction_errors': []
        }
        
        results, run_id = runtime.execute(workflow.build(), {
            "status_updater": {
                "extraction_result": extraction_result
            }
        })
        
        result = results.get('status_updater', {})
        
        # Validate status update
        assert result['processing_id'] == 'status_test'
        assert result['ready_for_context_creation'] is True
        
        status_update = result['status_update']
        assert status_update['id'] == 'status_test'
        assert status_update['status'] == 'processing'
        assert status_update['progress'] == 40
        assert 'Processed 2 files' in status_update['message']
        assert 'extracted 8 items' in status_update['message']
        assert status_update['files_processed'] == 2
        assert status_update['items_extracted'] == 8
    
    @test_timeout
    def test_context_creator_node_functionality(self, runtime):
        """Test context creator node with extracted content"""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "context_creator", {
            "code": """
import time
def create_chat_context(status_update_result):
    extraction_data = status_update_result['extraction_data']
    processing_id = status_update_result['processing_id']
    
    if not status_update_result.get('ready_for_context_creation', False):
        result = {
            'processing_id': processing_id,
            'context_created': False,
            'error': 'No valid content for context creation',
            'context_id': None
        }
    else:
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
        
        result = {
            'processing_id': processing_id,
            'context_created': True,
            'context_id': context_id,
            'context_data': context_data,
            'items_for_matching': total_items
        }
"""
        })
        
        # Test context creation with sample data
        status_update_result = {
            'processing_id': 'context_test',
            'ready_for_context_creation': True,
            'extraction_data': {
                'extracted_contents': [
                    {
                        'original_name': 'test1.txt',
                        'content_preview': 'Test content preview 1',
                        'items_extracted': 3
                    },
                    {
                        'original_name': 'test2.txt', 
                        'content_preview': 'Test content preview 2',
                        'items_extracted': 5
                    }
                ]
            }
        }
        
        results, run_id = runtime.execute(workflow.build(), {
            "context_creator": {
                "status_update_result": status_update_result
            }
        })
        
        result = results.get('context_creator', {})
        
        # Validate context creation
        assert result['processing_id'] == 'context_test'
        assert result['context_created'] is True
        assert result['context_id'].startswith('ctx_context_test_')
        assert result['items_for_matching'] == 8  # 3 + 5
        
        context_data = result['context_data']
        assert context_data['total_files'] == 2
        assert context_data['total_items'] == 8
        assert len(context_data['files']) == 2
        
        # Validate context files structure
        first_file = context_data['files'][0]
        assert first_file['name'] == 'test1.txt'
        assert first_file['type'] == 'text/plain'
        assert first_file['items_count'] == 3
    
    @test_timeout
    def test_product_matcher_node_simulation(self, runtime):
        """Test product matcher node with realistic simulation"""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "product_matcher", {
            "code": """
import time
import random
def simulate_product_matching(context_result):
    processing_id = context_result['processing_id']
    context_id = context_result.get('context_id')
    items_count = context_result.get('items_for_matching', 0)
    
    if not context_result.get('context_created', False):
        result = {
            'processing_id': processing_id,
            'context_id': context_id,
            'products_matched': 0,
            'matching_completed': False,
            'error': 'No context available for product matching'
        }
    else:
        # Simulate matching process with realistic timing
        time.sleep(0.001)  # Minimal sleep for simulation
        
        # Simulate product matches (in production would query actual database)
        match_rate = 0.6  # 60% of items typically find matches
        products_matched = int(items_count * match_rate) + random.randint(0, 2)
        
        matching_results = {
            'total_items_processed': items_count,
            'products_matched': products_matched,
            'match_rate': products_matched / max(items_count, 1),
            'matching_confidence': 0.85,
            'processing_time_ms': 10
        }
        
        result = {
            'processing_id': processing_id,
            'context_id': context_id,
            'products_matched': products_matched,
            'matching_completed': True,
            'matching_results': matching_results
        }
"""
        })
        
        # Test product matching
        context_result = {
            'processing_id': 'match_test',
            'context_id': 'ctx_match_test_123',
            'context_created': True,
            'items_for_matching': 10
        }
        
        results, run_id = runtime.execute(workflow.build(), {
            "product_matcher": {
                "context_result": context_result
            }
        })
        
        result = results.get('product_matcher', {})
        
        # Validate product matching
        assert result['processing_id'] == 'match_test'
        assert result['context_id'] == 'ctx_match_test_123'
        assert result['matching_completed'] is True
        assert result['products_matched'] >= 0
        
        matching_results = result['matching_results']
        assert matching_results['total_items_processed'] == 10
        assert 0 <= matching_results['match_rate'] <= 1
        assert matching_results['matching_confidence'] == 0.85
    
    @test_timeout
    def test_completion_handler_node_functionality(self, runtime):
        """Test completion handler node with final processing"""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "completion_handler", {
            "code": """
import time
def complete_processing(matching_result):
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
    
    result = {
        'processing_id': processing_id,
        'final_status': final_status,
        'workflow_completed': True,
        'execution_summary': {
            'context_created': context_id is not None,
            'products_matched': products_matched,
            'success': final_status['success']
        }
    }
"""
        })
        
        # Test successful completion
        matching_result = {
            'processing_id': 'completion_test',
            'context_id': 'ctx_completion_123',
            'products_matched': 15,
            'matching_completed': True
        }
        
        results, run_id = runtime.execute(workflow.build(), {
            "completion_handler": {
                "matching_result": matching_result
            }
        })
        
        result = results.get('completion_handler', {})
        
        # Validate successful completion
        assert result['processing_id'] == 'completion_test'
        assert result['workflow_completed'] is True
        
        final_status = result['final_status']
        assert final_status['id'] == 'completion_test'
        assert final_status['status'] == 'completed'
        assert final_status['progress'] == 100
        assert final_status['success'] is True
        assert final_status['products_matched'] == 15
        assert 'Processing complete!' in final_status['message']
        
        execution_summary = result['execution_summary']
        assert execution_summary['context_created'] is True
        assert execution_summary['products_matched'] == 15
        assert execution_summary['success'] is True

class TestFileStorageWorkflowNodes:
    """Test file storage workflow nodes with real file operations"""
    
    @pytest.fixture
    def runtime(self):
        return LocalRuntime()
    
    @pytest.fixture
    def temp_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @test_timeout
    def test_file_validation_node_functionality(self, runtime):
        """Test file validation node with various file types and sizes"""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "file_validator", {
            "code": """
def validate_files(files_data, base_dir):
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
    
    result = {
        'valid_files': valid_files,
        'validation_errors': validation_errors,
        'total_valid': len(valid_files),
        'total_invalid': len(validation_errors)
    }
"""
        })
        
        # Test with various file scenarios
        test_files = [
            {'name': 'valid.txt', 'size': 1000, 'type': 'text/plain', 'content': 'Valid content'},
            {'name': 'too_large.pdf', 'size': 60 * 1024 * 1024, 'type': 'application/pdf', 'content': ''},
            {'name': 'invalid_type.exe', 'size': 500, 'type': 'application/exe', 'content': ''},
            {'name': '', 'size': 100, 'type': 'text/plain', 'content': 'No name'},
            {'name': 'valid.csv', 'size': 2000, 'type': 'text/csv', 'content': 'CSV data'}
        ]
        
        results, run_id = runtime.execute(workflow.build(), {
            "file_validator": {
                "files_data": test_files,
                "base_dir": "/tmp"
            }
        })
        
        result = results.get('file_validator', {})
        
        # Validate file validation results
        assert result['total_valid'] == 2  # valid.txt and valid.csv
        assert result['total_invalid'] == 3  # too_large, invalid_type, no_name
        assert len(result['valid_files']) == 2
        assert len(result['validation_errors']) == 3
        
        # Check specific validation errors
        errors = result['validation_errors']
        assert any('File size exceeds' in error for error in errors)
        assert any('File type' in error and 'not allowed' in error for error in errors)
        assert any('File name cannot be empty' in error for error in errors)
    
    @test_timeout
    def test_file_storage_node_functionality(self, runtime, temp_directory):
        """Test file storage node with real file operations"""
        workflow = WorkflowBuilder()
        
        workflow.add_node("PythonCodeNode", "file_storer", {
            "code": """
import os
import hashlib
import time
def store_files(validation_result, base_dir):
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
    
    result = {
        'stored_files': stored_files,
        'storage_errors': storage_errors,
        'files_stored': len(stored_files),
        'storage_success': len(storage_errors) == 0
    }
"""
        })
        
        # Test file storage with valid files
        validation_result = {
            'valid_files': [
                {
                    'name': 'test1.txt',
                    'size': 100,
                    'mime_type': 'text/plain',
                    'content': 'Test file 1 content'
                },
                {
                    'name': 'test2.csv',
                    'size': 200,
                    'mime_type': 'text/csv',
                    'content': 'col1,col2\nval1,val2'
                }
            ]
        }
        
        results, run_id = runtime.execute(workflow.build(), {
            "file_storer": {
                "validation_result": validation_result,
                "base_dir": temp_directory
            }
        })
        
        result = results.get('file_storer', {})
        
        # Validate file storage
        assert result['storage_success'] is True
        assert result['files_stored'] == 2
        assert len(result['stored_files']) == 2
        assert len(result['storage_errors']) == 0
        
        # Validate stored file structure
        first_file = result['stored_files'][0]
        assert 'id' in first_file
        assert 'original_name' in first_file
        assert 'stored_path' in first_file
        assert 'checksum' in first_file
        assert first_file['original_name'] == 'test1.txt'
        
        # Verify files actually exist on disk
        stored_path = first_file['stored_path']
        assert os.path.exists(stored_path)
        
        # Verify file content
        with open(stored_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == 'Test file 1 content'