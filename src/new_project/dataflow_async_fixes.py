"""
DataFlow Async Connection Wrapper Fixes
=======================================

Fixes for AsyncSQLConnectionWrapper protocol issues and missing connection_pool attributes.
This module provides proper async context manager support and connection pool integration.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, AsyncContextManager
from contextlib import asynccontextmanager
import asyncpg
from dataflow import DataFlow

logger = logging.getLogger(__name__)

class AsyncSQLConnectionWrapper:
    """Fixed AsyncSQL connection wrapper with proper async context manager protocol"""
    
    def __init__(self, connection_pool, database_url: str):
        self.connection_pool = connection_pool
        self.database_url = database_url
        self._connection = None
        self._transaction = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        try:
            if self.connection_pool:
                self._connection = await self.connection_pool.acquire()
            else:
                self._connection = await asyncpg.connect(self.database_url)
            return self
        except Exception as e:
            logger.error(f"Failed to acquire database connection: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        try:
            if self._transaction:
                if exc_type:
                    await self._transaction.rollback()
                else:
                    await self._transaction.commit()
                self._transaction = None
                
            if self._connection:
                if self.connection_pool:
                    await self.connection_pool.release(self._connection)
                else:
                    await self._connection.close()
                self._connection = None
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query"""
        if not self._connection:
            raise RuntimeError("Connection not established. Use async with statement.")
        return await self._connection.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> list:
        """Fetch query results"""
        if not self._connection:
            raise RuntimeError("Connection not established. Use async with statement.")
        return await self._connection.fetch(query, *args)
        
    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch single row"""
        if not self._connection:
            raise RuntimeError("Connection not established. Use async with statement.")
        row = await self._connection.fetchrow(query, *args)
        return dict(row) if row else None
    
    async def begin_transaction(self):
        """Begin a transaction"""
        if not self._connection:
            raise RuntimeError("Connection not established. Use async with statement.")
        self._transaction = self._connection.transaction()
        await self._transaction.start()
        return self._transaction

class DataFlowConnectionPoolFix:
    """Fix for DataFlow connection pool attribute issues"""
    
    def __init__(self, dataflow_instance: DataFlow):
        self.dataflow = dataflow_instance
        self._connection_pool = None
        self._pool_created = False
        
    async def ensure_connection_pool(self):
        """Ensure connection pool is created and available"""
        if not self._pool_created:
            try:
                # Extract connection details from DataFlow
                database_url = getattr(self.dataflow, 'database_url', None)
                if not database_url:
                    # Try to construct from config
                    config = getattr(self.dataflow, 'config', {})
                    database_url = (
                        f"postgresql://{config.get('user', 'horme_user')}:"
                        f"{config.get('password', 'horme_password')}@"
                        f"{config.get('host', 'localhost')}:"
                        f"{config.get('port', 5432)}/"
                        f"{config.get('database', 'horme_classification_db')}"
                    )
                
                # Create connection pool
                pool_config = {
                    'min_size': getattr(self.dataflow, 'pool_size', 10),
                    'max_size': getattr(self.dataflow, 'pool_size', 10) + 
                               getattr(self.dataflow, 'pool_max_overflow', 20),
                    'command_timeout': getattr(self.dataflow, 'pool_timeout', 30)
                }
                
                self._connection_pool = await asyncpg.create_pool(
                    database_url, **pool_config
                )
                
                # Inject connection_pool attribute into DataFlow instance
                self.dataflow.connection_pool = self._connection_pool
                self._pool_created = True
                
                logger.info(f"✅ Connection pool created successfully")
                
            except Exception as e:
                logger.error(f"❌ Failed to create connection pool: {e}")
                # Create a mock connection pool for development
                self.dataflow.connection_pool = None
                self._pool_created = True
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncContextManager[AsyncSQLConnectionWrapper]:
        """Get an async connection with proper context management"""
        await self.ensure_connection_pool()
        
        database_url = getattr(self.dataflow, 'database_url', 
                              "postgresql://horme_user:horme_password@localhost:5432/horme_classification_db")
        
        async with AsyncSQLConnectionWrapper(self._connection_pool, database_url) as conn:
            yield conn
    
    async def close_pool(self):
        """Close the connection pool"""
        if self._connection_pool:
            await self._connection_pool.close()
            self._connection_pool = None
            self._pool_created = False
            self.dataflow.connection_pool = None

def fix_dataflow_async_issues(dataflow_instance: DataFlow) -> DataFlowConnectionPoolFix:
    """Apply fixes to DataFlow instance for async issues"""
    return DataFlowConnectionPoolFix(dataflow_instance)

# Migration table creation with proper async handling
async def create_migration_table_safe(connection_wrapper: AsyncSQLConnectionWrapper):
    """Safely create migration table with proper error handling"""
    try:
        await connection_wrapper.execute("""
            CREATE TABLE IF NOT EXISTS dataflow_migrations (
                id SERIAL PRIMARY KEY,
                version VARCHAR(255) NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)
        logger.info("✅ Migration table created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create migration table: {e}")
        return False

# Test function to verify fixes
async def test_async_connection_fixes(dataflow_instance: DataFlow):
    """Test the async connection fixes"""
    logger.info("🧪 Testing async connection fixes...")
    
    fix = fix_dataflow_async_issues(dataflow_instance)
    
    try:
        async with fix.get_connection() as conn:
            # Test basic query
            result = await conn.fetchrow("SELECT 1 as test")
            if result and result.get('test') == 1:
                logger.info("✅ Basic connection test passed")
                
                # Test migration table creation
                migration_success = await create_migration_table_safe(conn)
                if migration_success:
                    logger.info("✅ Migration table creation test passed")
                    return True
                else:
                    logger.warning("⚠️ Migration table creation failed")
                    return False
            else:
                logger.error("❌ Basic connection test failed")
                return False
                
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return False
    finally:
        await fix.close_pool()

if __name__ == "__main__":
    # Example usage
    from dataflow_classification_models import db
    
    async def main():
        success = await test_async_connection_fixes(db)
        if success:
            print("✅ All async connection fixes working properly")
        else:
            print("❌ Some async connection fixes failed")
    
    asyncio.run(main())
