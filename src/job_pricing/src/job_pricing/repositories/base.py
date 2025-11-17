"""
Base Repository

Provides generic CRUD operations for all repositories.
Uses the repository pattern to encapsulate data access logic.
"""

from typing import Generic, TypeVar, Type, List, Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, or_

from job_pricing.models import Base

# Type variable for model class
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic base repository with CRUD operations.

    This class provides common database operations that can be inherited
    by specific repositories. It uses generics to maintain type safety.

    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: Session):
                super().__init__(User, session)

            def get_by_email(self, email: str) -> Optional[User]:
                return self.session.query(self.model).filter_by(email=email).first()
    """

    def __init__(self, model: Type[ModelType], session: Session):
        """
        Initialize repository with model class and database session.

        Args:
            model: SQLAlchemy model class
            session: SQLAlchemy database session
        """
        self.model = model
        self.session = session

    def get_by_id(self, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID.

        Args:
            id: Primary key value

        Returns:
            Model instance or None if not found
        """
        return self.session.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get all records with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of model instances
        """
        return self.session.query(self.model).offset(skip).limit(limit).all()

    def get_by_filters(self, **filters) -> List[ModelType]:
        """
        Get records matching filter criteria.

        Args:
            **filters: Column=value pairs for filtering

        Returns:
            List of model instances matching filters

        Example:
            repo.get_by_filters(status='active', location='Singapore')
        """
        query = self.session.query(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.all()

    def get_one_by_filters(self, **filters) -> Optional[ModelType]:
        """
        Get a single record matching filter criteria.

        Args:
            **filters: Column=value pairs for filtering

        Returns:
            Model instance or None if not found

        Example:
            repo.get_one_by_filters(email='user@example.com')
        """
        query = self.session.query(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.first()

    def create(self, obj: ModelType) -> ModelType:
        """
        Create a new record.

        Args:
            obj: Model instance to create

        Returns:
            Created model instance with populated ID

        Example:
            user = User(name="John", email="john@example.com")
            created_user = repo.create(user)
        """
        self.session.add(obj)
        self.session.flush()  # Flush to get the ID without committing
        self.session.refresh(obj)
        return obj

    def create_many(self, objs: List[ModelType]) -> List[ModelType]:
        """
        Create multiple records in a single operation.

        Args:
            objs: List of model instances to create

        Returns:
            List of created model instances

        Example:
            users = [User(name="John"), User(name="Jane")]
            created_users = repo.create_many(users)
        """
        self.session.add_all(objs)
        self.session.flush()
        for obj in objs:
            self.session.refresh(obj)
        return objs

    def update(self, obj: ModelType) -> ModelType:
        """
        Update an existing record.

        Args:
            obj: Model instance with updated values

        Returns:
            Updated model instance

        Example:
            user = repo.get_by_id(1)
            user.name = "Updated Name"
            updated_user = repo.update(user)
        """
        self.session.flush()
        self.session.refresh(obj)
        return obj

    def update_by_id(self, id: Any, **updates) -> Optional[ModelType]:
        """
        Update a record by ID.

        Args:
            id: Primary key value
            **updates: Column=value pairs to update

        Returns:
            Updated model instance or None if not found

        Example:
            repo.update_by_id(1, name="New Name", status="active")
        """
        obj = self.get_by_id(id)
        if obj:
            for key, value in updates.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            self.session.flush()
            self.session.refresh(obj)
        return obj

    def delete(self, obj: ModelType) -> None:
        """
        Delete a record.

        Args:
            obj: Model instance to delete

        Example:
            user = repo.get_by_id(1)
            repo.delete(user)
        """
        self.session.delete(obj)
        self.session.flush()

    def delete_by_id(self, id: Any) -> bool:
        """
        Delete a record by ID.

        Args:
            id: Primary key value

        Returns:
            True if deleted, False if not found

        Example:
            deleted = repo.delete_by_id(1)
        """
        obj = self.get_by_id(id)
        if obj:
            self.session.delete(obj)
            self.session.flush()
            return True
        return False

    def count(self, **filters) -> int:
        """
        Count records matching filter criteria.

        Args:
            **filters: Column=value pairs for filtering

        Returns:
            Number of matching records

        Example:
            active_count = repo.count(status='active')
        """
        query = self.session.query(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.count()

    def exists(self, **filters) -> bool:
        """
        Check if any record exists matching filter criteria.

        Args:
            **filters: Column=value pairs for filtering

        Returns:
            True if at least one record exists, False otherwise

        Example:
            exists = repo.exists(email='user@example.com')
        """
        return self.count(**filters) > 0

    def commit(self) -> None:
        """
        Commit the current transaction.

        Call this after create/update/delete operations to persist changes.
        """
        self.session.commit()

    def rollback(self) -> None:
        """
        Rollback the current transaction.

        Call this to undo changes in case of errors.
        """
        self.session.rollback()

    def refresh(self, obj: ModelType) -> ModelType:
        """
        Refresh an object from the database.

        Args:
            obj: Model instance to refresh

        Returns:
            Refreshed model instance

        Example:
            user = repo.refresh(user)  # Reload from DB
        """
        self.session.refresh(obj)
        return obj
