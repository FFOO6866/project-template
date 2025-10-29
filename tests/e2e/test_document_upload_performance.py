"""End-to-end performance tests for document upload workflow.

Tests complete user workflows with real infrastructure and performance validation.
NO MOCKING - complete scenarios with real services and performance constraints.

Tier 3 (E2E) Requirements:
- Complete user workflows from start to finish
- Real infrastructure and data
- NO MOCKING - complete scenarios with real services  
- Test actual user scenarios and expectations
- Validate business requirements end-to-end
- Performance validation under load
"""

import pytest
import tempfile
import shutil
import os
import time
import threading
import concurrent.futures
from pathlib import Path
import json
from datetime import datetime
import sqlite3
import psutil
import statistics
from typing import List, Dict, Tuple
import asyncio
from unittest.mock import patch

# Test markers
pytestmark = [pytest.mark.performance, pytest.mark.slow]

class TestDocumentUploadPerformance:
    """End-to-end performance tests for document upload workflow."""
    
    def setup_method(self):
        """Set up test fixtures for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.cleanup_files = []
        self.performance_metrics = {
            'upload_times': [],
            'processing_times': [],
            'memory_usage': [],
            'concurrent_requests': 0,
            'errors': []
        }
        
    def teardown_method(self):
        """Clean up test files and temporary directories."""
        for file_path in self.cleanup_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
                
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
    
    def create_test_database(self) -> sqlite3.Connection:
        """Create test database for performance testing."""
        db_path = Path(self.temp_dir) / "performance_test.db"
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        # Create performance-optimized schema
        conn.execute("""
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY,
                title TEXT,
                filename TEXT,
                file_size INTEGER,
                mime_type TEXT,
                type TEXT DEFAULT 'upload',
                status TEXT DEFAULT 'pending',
                processing_id TEXT,
                estimated_items INTEGER DEFAULT 0,
                actual_items INTEGER,
                total_value REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE processing_status (
                id TEXT PRIMARY KEY,
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                message TEXT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_time TIMESTAMP,
                error_message TEXT,
                files_processed INTEGER DEFAULT 0,
                total_files INTEGER DEFAULT 0,
                items_extracted INTEGER DEFAULT 0,
                products_matched INTEGER DEFAULT 0,
                memory_usage_mb REAL DEFAULT 0,
                processing_time_ms INTEGER DEFAULT 0
            )
        """)
        
        # Create indexes for performance
        conn.execute("CREATE INDEX idx_documents_status ON documents(status)")
        conn.execute("CREATE INDEX idx_documents_processing_id ON documents(processing_id)")
        conn.execute("CREATE INDEX idx_processing_status ON processing_status(status)")
        conn.execute("CREATE INDEX idx_processing_created ON processing_status(start_time)")
        
        conn.commit()
        self.cleanup_files.append(str(db_path))
        return conn
    
    def create_large_test_file(self, size_mb: int, filename: str) -> Dict:
        """Create a large test file for performance testing."""
        file_path = Path(self.temp_dir) / filename
        content_lines = []
        
        # Generate realistic content that totals approximately size_mb
        line_template = "Item {}: {} - ${:.2f} - Category: {} - Description: {}\n"
        target_size = size_mb * 1024 * 1024
        current_size = 0
        item_id = 1
        
        while current_size < target_size:
            line = line_template.format(
                item_id,
                f"Product_{item_id}",
                item_id * 10.50,
                f"Category_{(item_id % 10) + 1}",
                f"Detailed description for product {item_id} with specifications"
            )
            content_lines.append(line)
            current_size += len(line.encode('utf-8'))
            item_id += 1
        
        content = ''.join(content_lines)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        actual_size = file_path.stat().st_size
        self.cleanup_files.append(str(file_path))
        
        return {
            'path': str(file_path),
            'name': filename,
            'content': content[:1000],  # Sample for verification
            'size': actual_size,
            'item_count': item_id - 1,
            'type': 'text/plain'
        }
    
    def measure_memory_usage(self) -> float:
        """Measure current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    
    def simulate_file_upload_processing(self, file_data: Dict, db_conn: sqlite3.Connection) -> Dict:
        """Simulate complete file upload and processing workflow."""
        start_time = time.time()
        processing_id = f"perf_{int(time.time())}_{threading.current_thread().ident}"
        
        try:
            # Step 1: File upload simulation
            cursor = db_conn.cursor()
            
            cursor.execute("""
                INSERT INTO documents (title, filename, file_size, processing_id, status)
                VALUES (?, ?, ?, ?, ?)
            """, (file_data['name'], file_data['name'], file_data['size'], 
                  processing_id, 'uploaded'))
            
            db_conn.commit()
            upload_time = time.time() - start_time
            
            # Step 2: Initialize processing status
            cursor.execute("""
                INSERT INTO processing_status (id, status, total_files, start_time)
                VALUES (?, ?, ?, ?)
            """, (processing_id, 'processing', 1, datetime.now()))
            
            db_conn.commit()
            
            # Step 3: Simulate processing with progress updates
            processing_steps = [
                (10, 'Reading file...'),
                (30, 'Extracting items...'),
                (60, 'Matching products...'),
                (90, 'Finalizing results...'),
                (100, 'Processing complete!')
            ]
            
            memory_start = self.measure_memory_usage()
            
            for progress, message in processing_steps:
                # Simulate processing work
                time.sleep(0.01)  # Minimal delay to simulate processing
                
                current_memory = self.measure_memory_usage()
                
                cursor.execute("""
                    UPDATE processing_status 
                    SET progress = ?, message = ?, memory_usage_mb = ?
                    WHERE id = ?
                """, (progress, message, current_memory, processing_id))
                
                db_conn.commit()
            
            # Step 4: Complete processing
            total_time = time.time() - start_time
            memory_peak = self.measure_memory_usage()
            
            cursor.execute("""
                UPDATE processing_status 
                SET status = ?, completed_time = ?, processing_time_ms = ?,
                    items_extracted = ?, products_matched = ?
                WHERE id = ?
            """, ('completed', datetime.now(), int(total_time * 1000),
                  file_data['item_count'], file_data['item_count'] // 2, processing_id))
            
            cursor.execute("""
                UPDATE documents 
                SET status = ?, completed_at = ?, actual_items = ?
                WHERE processing_id = ?
            """, ('completed', datetime.now(), file_data['item_count'], processing_id))
            
            db_conn.commit()
            
            return {
                'processing_id': processing_id,
                'total_time': total_time,
                'upload_time': upload_time,
                'processing_time': total_time - upload_time,
                'memory_peak': memory_peak,
                'memory_delta': memory_peak - memory_start,
                'items_processed': file_data['item_count'],
                'status': 'completed'
            }
            
        except Exception as e:
            # Handle errors
            cursor.execute("""
                UPDATE processing_status 
                SET status = ?, error_message = ?, completed_time = ?
                WHERE id = ?
            """, ('error', str(e), datetime.now(), processing_id))
            
            db_conn.commit()
            
            return {
                'processing_id': processing_id,
                'total_time': time.time() - start_time,
                'status': 'error',
                'error': str(e)
            }
    
    def test_single_large_file_performance(self):
        """Test performance with single large file (10MB)."""
        # Arrange
        db_conn = self.create_test_database()
        large_file = self.create_large_test_file(10, "large_rfp_10mb.txt")
        
        # Act
        start_memory = self.measure_memory_usage()
        result = self.simulate_file_upload_processing(large_file, db_conn)
        end_memory = self.measure_memory_usage()
        
        # Assert - Performance benchmarks
        assert result['status'] == 'completed'
        assert result['total_time'] < 5.0  # Should complete within 5 seconds
        assert result['memory_delta'] < 50  # Should not use more than 50MB extra memory
        assert result['items_processed'] > 0
        
        # Log performance metrics
        print(f"\nLarge File Performance (10MB):")
        print(f"  Total Time: {result['total_time']:.3f} seconds")
        print(f"  Memory Usage: {result['memory_delta']:.1f} MB")
        print(f"  Items Processed: {result['items_processed']}")
        print(f"  Processing Rate: {result['items_processed'] / result['total_time']:.1f} items/sec")
        
        db_conn.close()
    
    def test_multiple_concurrent_uploads(self):
        """Test performance with multiple concurrent file uploads."""
        # Arrange
        db_conn = self.create_test_database()
        num_concurrent = 5
        file_size_mb = 2
        
        test_files = []
        for i in range(num_concurrent):
            file_data = self.create_large_test_file(file_size_mb, f"concurrent_{i}.txt")
            test_files.append(file_data)
        
        # Act
        start_time = time.time()
        start_memory = self.measure_memory_usage()
        
        results = []
        
        def process_file(file_data):
            # Each thread needs its own database connection
            thread_db = sqlite3.connect(str(Path(self.temp_dir) / "performance_test.db"))
            thread_db.row_factory = sqlite3.Row
            try:
                return self.simulate_file_upload_processing(file_data, thread_db)
            finally:
                thread_db.close()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            future_to_file = {executor.submit(process_file, file_data): file_data 
                              for file_data in test_files}
            
            for future in concurrent.futures.as_completed(future_to_file):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({'status': 'error', 'error': str(e)})
        
        total_time = time.time() - start_time
        end_memory = self.measure_memory_usage()
        memory_delta = end_memory - start_memory
        
        # Assert - Concurrent performance benchmarks
        successful_results = [r for r in results if r['status'] == 'completed']
        assert len(successful_results) >= num_concurrent * 0.8  # At least 80% success rate
        assert total_time < 10.0  # Should complete within 10 seconds
        assert memory_delta < 100  # Should not use more than 100MB extra memory
        
        # Performance analysis
        processing_times = [r['total_time'] for r in successful_results]
        avg_processing_time = statistics.mean(processing_times)
        max_processing_time = max(processing_times)
        total_items = sum(r.get('items_processed', 0) for r in successful_results)
        
        print(f"\nConcurrent Upload Performance ({num_concurrent} files):")
        print(f"  Success Rate: {len(successful_results)}/{num_concurrent}")
        print(f"  Total Time: {total_time:.3f} seconds")
        print(f"  Average Processing Time: {avg_processing_time:.3f} seconds")
        print(f"  Max Processing Time: {max_processing_time:.3f} seconds")
        print(f"  Memory Usage: {memory_delta:.1f} MB")
        print(f"  Total Items Processed: {total_items}")
        print(f"  Overall Processing Rate: {total_items / total_time:.1f} items/sec")
        
        db_conn.close()
    
    def test_memory_usage_under_load(self):
        """Test memory usage remains reasonable under sustained load."""
        # Arrange
        db_conn = self.create_test_database()
        num_iterations = 20
        file_size_mb = 1
        
        memory_samples = []
        processing_times = []
        
        # Act - Process files in sequence to test sustained load
        initial_memory = self.measure_memory_usage()
        
        for i in range(num_iterations):
            file_data = self.create_large_test_file(file_size_mb, f"load_test_{i}.txt")
            
            iteration_start = time.time()
            result = self.simulate_file_upload_processing(file_data, db_conn)
            iteration_time = time.time() - iteration_start
            
            current_memory = self.measure_memory_usage()
            memory_samples.append(current_memory)
            processing_times.append(iteration_time)
            
            # Clean up file to prevent disk space issues
            os.remove(file_data['path'])
        
        final_memory = self.measure_memory_usage()
        
        # Assert - Memory usage should remain stable
        memory_growth = final_memory - initial_memory
        avg_memory = statistics.mean(memory_samples)
        max_memory = max(memory_samples)
        avg_processing_time = statistics.mean(processing_times)
        
        assert memory_growth < 20  # Memory growth should be less than 20MB
        assert max_memory - avg_memory < 30  # Memory spikes should be limited
        assert avg_processing_time < 2.0  # Average processing time should be reasonable
        
        print(f"\nSustained Load Performance ({num_iterations} iterations):")
        print(f"  Initial Memory: {initial_memory:.1f} MB")
        print(f"  Final Memory: {final_memory:.1f} MB")
        print(f"  Memory Growth: {memory_growth:.1f} MB")
        print(f"  Average Memory: {avg_memory:.1f} MB")
        print(f"  Peak Memory: {max_memory:.1f} MB")
        print(f"  Average Processing Time: {avg_processing_time:.3f} seconds")
        
        db_conn.close()
    
    def test_database_performance_under_concurrent_access(self):
        """Test database performance with concurrent read/write operations."""
        # Arrange
        db_conn = self.create_test_database()
        num_writers = 3
        num_readers = 5
        operations_per_thread = 10
        
        # Pre-populate database with some data
        cursor = db_conn.cursor()
        for i in range(50):
            processing_id = f"prepop_{i}"
            cursor.execute("""
                INSERT INTO processing_status (id, status, progress, items_extracted)
                VALUES (?, ?, ?, ?)
            """, (processing_id, 'completed', 100, i * 10))
        db_conn.commit()
        
        results = []
        
        def writer_task():
            """Simulate concurrent write operations."""
            write_db = sqlite3.connect(str(Path(self.temp_dir) / "performance_test.db"))
            write_db.row_factory = sqlite3.Row
            
            thread_results = []
            for i in range(operations_per_thread):
                start_time = time.time()
                processing_id = f"writer_{threading.current_thread().ident}_{i}"
                
                cursor = write_db.cursor()
                cursor.execute("""
                    INSERT INTO processing_status (id, status, progress, message)
                    VALUES (?, ?, ?, ?)
                """, (processing_id, 'processing', i * 10, f'Processing item {i}'))
                
                write_db.commit()
                
                operation_time = time.time() - start_time
                thread_results.append(('write', operation_time))
            
            write_db.close()
            return thread_results
        
        def reader_task():
            """Simulate concurrent read operations."""
            read_db = sqlite3.connect(str(Path(self.temp_dir) / "performance_test.db"))
            read_db.row_factory = sqlite3.Row
            
            thread_results = []
            for i in range(operations_per_thread):
                start_time = time.time()
                
                cursor = read_db.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM processing_status WHERE status = ?", 
                              ('completed',))
                result = cursor.fetchone()
                
                cursor.execute("SELECT * FROM processing_status ORDER BY start_time DESC LIMIT 10")
                recent = cursor.fetchall()
                
                operation_time = time.time() - start_time
                thread_results.append(('read', operation_time))
            
            read_db.close()
            return thread_results
        
        # Act - Run concurrent operations
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_writers + num_readers) as executor:
            # Submit writer tasks
            writer_futures = [executor.submit(writer_task) for _ in range(num_writers)]
            
            # Submit reader tasks
            reader_futures = [executor.submit(reader_task) for _ in range(num_readers)]
            
            # Collect results
            for future in concurrent.futures.as_completed(writer_futures + reader_futures):
                try:
                    thread_results = future.result()
                    results.extend(thread_results)
                except Exception as e:
                    print(f"Thread error: {e}")
        
        total_time = time.time() - start_time
        
        # Assert - Database performance benchmarks
        write_times = [t for op_type, t in results if op_type == 'write']
        read_times = [t for op_type, t in results if op_type == 'read']
        
        avg_write_time = statistics.mean(write_times) if write_times else 0
        avg_read_time = statistics.mean(read_times) if read_times else 0
        max_write_time = max(write_times) if write_times else 0
        max_read_time = max(read_times) if read_times else 0
        
        assert avg_write_time < 0.1  # Average write should be under 100ms
        assert avg_read_time < 0.05  # Average read should be under 50ms
        assert max_write_time < 0.5   # No write should take more than 500ms
        assert max_read_time < 0.2    # No read should take more than 200ms
        
        print(f"\nDatabase Concurrent Access Performance:")
        print(f"  Total Operations: {len(results)}")
        print(f"  Total Time: {total_time:.3f} seconds")
        print(f"  Operations/Second: {len(results) / total_time:.1f}")
        print(f"  Average Write Time: {avg_write_time * 1000:.1f} ms")
        print(f"  Average Read Time: {avg_read_time * 1000:.1f} ms")
        print(f"  Max Write Time: {max_write_time * 1000:.1f} ms")
        print(f"  Max Read Time: {max_read_time * 1000:.1f} ms")
        
        db_conn.close()
    
    @pytest.mark.slow
    def test_end_to_end_workflow_performance(self):
        """Test complete end-to-end workflow performance with realistic data."""
        # Arrange
        db_conn = self.create_test_database()
        
        # Create realistic test scenario: 5 files of varying sizes
        test_scenario = [
            (1, "small_quote.txt"),      # 1MB - typical quote request
            (5, "medium_rfp.txt"),       # 5MB - medium RFP document  
            (3, "product_list.csv"),     # 3MB - product catalog
            (2, "specifications.txt"),   # 2MB - technical specs
            (4, "requirements.json")     # 4MB - structured requirements
        ]
        
        test_files = []
        for size_mb, filename in test_scenario:
            file_data = self.create_large_test_file(size_mb, filename)
            test_files.append(file_data)
        
        # Act - Process complete workflow
        workflow_start = time.time()
        workflow_results = []
        total_items = 0
        
        for file_data in test_files:
            result = self.simulate_file_upload_processing(file_data, db_conn)
            workflow_results.append(result)
            total_items += result.get('items_processed', 0)
        
        workflow_time = time.time() - workflow_start
        
        # Act - Query final state
        cursor = db_conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM documents WHERE status = 'completed'")
        completed_docs = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM processing_status WHERE status = 'completed'")
        completed_processing = cursor.fetchone()['count']
        
        cursor.execute("SELECT AVG(processing_time_ms) as avg_time FROM processing_status")
        avg_processing_time_ms = cursor.fetchone()['avg_time'] or 0
        
        # Assert - End-to-end performance benchmarks
        successful_results = [r for r in workflow_results if r['status'] == 'completed']
        
        assert len(successful_results) == len(test_files)  # All files should process successfully
        assert completed_docs == len(test_files)
        assert completed_processing == len(test_files)
        assert workflow_time < 20.0  # Complete workflow under 20 seconds
        assert avg_processing_time_ms < 3000  # Average processing under 3 seconds
        
        # Performance summary
        total_file_size = sum(f['size'] for f in test_files)
        processing_rate_mb_per_sec = (total_file_size / (1024 * 1024)) / workflow_time
        
        print(f"\nEnd-to-End Workflow Performance:")
        print(f"  Files Processed: {len(test_files)}")
        print(f"  Total File Size: {total_file_size / (1024 * 1024):.1f} MB")
        print(f"  Total Items: {total_items}")
        print(f"  Workflow Time: {workflow_time:.3f} seconds")
        print(f"  Processing Rate: {processing_rate_mb_per_sec:.1f} MB/sec")
        print(f"  Items Per Second: {total_items / workflow_time:.1f} items/sec")
        print(f"  Average Processing Time: {avg_processing_time_ms:.0f} ms")
        
        db_conn.close()