"""
Database Query Optimization Utilities

Provides tools for optimizing database queries and monitoring performance.
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional, Dict, List
from functools import wraps

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Query

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Database query optimization utilities.

    Features:
    - Query timing and logging
    - Slow query detection
    - Query plan analysis
    - Index recommendations
    """

    def __init__(self, slow_query_threshold_ms: float = 100.0):
        """
        Initialize query optimizer.

        Args:
            slow_query_threshold_ms: Threshold for slow queries (milliseconds)
        """
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.query_stats: Dict[str, List[float]] = {}

    @contextmanager
    def timed_query(self, query_name: str):
        """
        Context manager for timing database queries.

        Usage:
            with optimizer.timed_query("get_users"):
                users = session.query(User).all()

        Args:
            query_name: Name of the query for logging

        Yields:
            None
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000

            # Record query statistics
            if query_name not in self.query_stats:
                self.query_stats[query_name] = []
            self.query_stats[query_name].append(duration_ms)

            # Log slow queries
            if duration_ms > self.slow_query_threshold_ms:
                logger.warning(
                    f"Slow query detected: {query_name} took {duration_ms:.2f}ms "
                    f"(threshold: {self.slow_query_threshold_ms}ms)"
                )

    def get_query_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get query performance statistics.

        Returns:
            Dict with query stats (count, avg, min, max)
        """
        stats = {}

        for query_name, durations in self.query_stats.items():
            stats[query_name] = {
                "count": len(durations),
                "avg_ms": sum(durations) / len(durations),
                "min_ms": min(durations),
                "max_ms": max(durations),
            }

        return stats

    def reset_stats(self):
        """Reset query statistics"""
        self.query_stats.clear()


def time_query(func):
    """
    Decorator to time database query functions.

    Usage:
        @time_query
        def get_all_users(session):
            return session.query(User).all()

    Args:
        func: Function to time

    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration_ms = (time.time() - start_time) * 1000
            logger.debug(f"{func.__name__} took {duration_ms:.2f}ms")

    return wrapper


# SQLAlchemy event listeners for query logging
def setup_query_logging(engine: Engine, enable_explain: bool = False):
    """
    Setup SQLAlchemy event listeners for query logging.

    Args:
        engine: SQLAlchemy engine
        enable_explain: Enable EXPLAIN for queries (development only)
    """

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Log queries before execution"""
        conn.info.setdefault('query_start_time', []).append(time.time())
        logger.debug(f"SQL Query: {statement}")

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Log query execution time"""
        total = time.time() - conn.info['query_start_time'].pop()
        duration_ms = total * 1000

        if duration_ms > 100:  # Log slow queries
            logger.warning(f"Slow query ({duration_ms:.2f}ms): {statement[:100]}...")

        # Log EXPLAIN plan for slow queries (development only)
        if enable_explain and duration_ms > 100:
            try:
                explain_result = conn.execute(text(f"EXPLAIN ANALYZE {statement}"))
                logger.debug(f"Query plan:\n{explain_result.fetchall()}")
            except Exception as e:
                logger.debug(f"Could not get query plan: {e}")


def add_database_indexes(engine: Engine):
    """
    Add recommended database indexes for common queries.

    Args:
        engine: SQLAlchemy engine
    """
    logger.info("Adding database indexes for query optimization")

    indexes = [
        # Users table
        "CREATE INDEX IF NOT EXISTS idx_users_email_active ON users(email) WHERE is_active = true;",
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
        "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);",

        # Refresh tokens table
        "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id) WHERE revoked = false;",
        "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at) WHERE revoked = false;",

        # Audit logs table
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action ON audit_logs(user_id, action);",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at_desc ON audit_logs(created_at DESC);",

        # Add indexes for other tables as needed
    ]

    with engine.connect() as conn:
        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
                logger.info(f"Index created: {index_sql.split('ON')[0].strip()}")
            except Exception as e:
                logger.warning(f"Could not create index: {e}")

        conn.commit()


def analyze_query_plan(engine: Engine, query: str) -> str:
    """
    Analyze query execution plan.

    Args:
        engine: SQLAlchemy engine
        query: SQL query to analyze

    Returns:
        Query execution plan
    """
    with engine.connect() as conn:
        result = conn.execute(text(f"EXPLAIN ANALYZE {query}"))
        plan = "\n".join([str(row) for row in result.fetchall()])
        return plan


def optimize_query(query: Query) -> Query:
    """
    Apply common optimizations to SQLAlchemy query.

    Args:
        query: SQLAlchemy query

    Returns:
        Optimized query
    """
    # Enable lazy loading only when needed
    query = query.options()

    # Limit result size for safety
    if not query._limit:
        query = query.limit(1000)

    return query


# Global query optimizer instance
query_optimizer = QueryOptimizer(slow_query_threshold_ms=100.0)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.DEBUG)

    from job_pricing.core.database import engine

    # Setup query logging
    setup_query_logging(engine, enable_explain=True)

    # Add indexes
    add_database_indexes(engine)

    # Print stats
    stats = query_optimizer.get_query_stats()
    print("Query Statistics:")
    for query_name, query_stats in stats.items():
        print(f"  {query_name}: {query_stats}")
