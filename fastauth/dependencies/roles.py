from typing import List, Optional, Type

from fastapi import Depends
from sqlmodel import Session, SQLModel, select

from fastauth.models.user import User, UserRole
from fastauth.models.role import Role, RoleCreate, RoleUpdate
from fastauth.dependencies.auth import AuthDependencies
from fastauth.exceptions import (
    PermissionDeniedException,
    RoleExistsException,
    RoleNotFoundException,
    UserNotFoundException,
)


class RoleDependencies:
    """Role-based authorization dependencies for FastAPI applications."""

    def __init__(self, auth_dependencies: AuthDependencies):
        """Initialize dependencies with AuthDependencies instance.

        Args:
            auth_dependencies: AuthDependencies instance for authentication
        """
        self.auth_deps = auth_dependencies
        self.auth = auth_dependencies.auth

    def _role_checker(self, required_roles: List[str], require_all: bool):
        """Build a dependency that checks the current user's roles.

        Args:
            required_roles: List of role names to check
            require_all: If True the user needs every role, otherwise any one

        Returns:
            callable: A dependency returning the current user if authorized
        """
        # Sync for the same reason as the auth dependencies: every role check
        # queries the database, which must not happen on the event loop.
        def _check_roles(
            current_user: User = Depends(self.auth_deps.get_current_active_user()),
            db: Session = Depends(self.auth_deps.get_db_session()),
        ):
            role_manager = RoleManager(db, user_model=self.auth.user_model)

            if require_all:
                authorized = role_manager.user_has_all_roles(current_user.id, required_roles)
            else:
                authorized = role_manager.user_has_any_role(current_user.id, required_roles)

            if not authorized:
                raise PermissionDeniedException("Insufficient permissions")
            return current_user
        return _check_roles

    def require_roles(self, required_roles: List[str]):
        """Create a dependency that requires any of the specified roles.

        Args:
            required_roles: List of role names, any of which grants access

        Returns:
            callable: A dependency that validates if the user has a required role
        """
        return self._role_checker(required_roles, require_all=False)

    def require_all_roles(self, required_roles: List[str]):
        """Create a dependency that requires all of the specified roles.

        Args:
            required_roles: List of role names, all of which are required

        Returns:
            callable: A dependency that validates if the user has all required roles
        """
        return self._role_checker(required_roles, require_all=True)

    def is_admin(self):
        """Create a dependency that requires the user to have the 'admin' role.

        Returns:
            callable: A dependency that validates if the user has admin role
        """
        return self.require_roles(["admin"])

    def get_role_manager(self):
        """Get a RoleManager instance as a FastAPI dependency.

        Returns:
            callable: A dependency that provides a RoleManager
        """
        def _get_role_manager(db: Session = Depends(self.auth_deps.get_db_session())):
            return RoleManager(db, user_model=self.auth.user_model)
        return _get_role_manager

    def get_current_active_user(self):
        """Get the current active user dependency from auth_deps.

        Returns:
            callable: A dependency that retrieves the current active user
        """
        return self.auth_deps.get_current_active_user()


class RoleManager:
    """Manages role operations in the database."""

    def __init__(self, db: Session, user_model: Type[SQLModel] = User):
        """Initialize with a database session.

        Args:
            db: SQLModel database session
            user_model: User model class (supports custom user models)
        """
        self.db = db
        self.user_model = user_model

    def _get_user_or_404(self, user_id: int):
        user = self.db.get(self.user_model, user_id)
        if not user:
            raise UserNotFoundException(f"User with ID {user_id} not found")
        return user

    def create_role(self, role_data: RoleCreate) -> Role:
        """Create a new role.

        Args:
            role_data: Role creation data

        Returns:
            Role: The created role

        Raises:
            RoleExistsException: If a role with the same name already exists
        """
        existing_role = self.get_role(role_name=role_data.name)
        if existing_role:
            raise RoleExistsException(f"Role with name '{role_data.name}' already exists")

        role = Role(name=role_data.name, description=role_data.description)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def get_role(self, role_id: Optional[int] = None, role_name: Optional[str] = None) -> Optional[Role]:
        """Get a role by ID or name.

        Args:
            role_id: Role ID (optional)
            role_name: Role name (optional)

        Returns:
            Role: The found role or None

        Raises:
            ValueError: If both role_id and role_name are None
        """
        if role_id is not None:
            return self.db.get(Role, role_id)
        if role_name is not None:
            return self.db.exec(select(Role).where(Role.name == role_name)).first()
        raise ValueError("Either role_id or role_name must be provided")

    def update_role(self, role_id: int, role_data: RoleUpdate) -> Optional[Role]:
        """Update an existing role.

        Args:
            role_id: Role ID
            role_data: Role update data

        Returns:
            Role: The updated role or None if not found
        """
        role = self.get_role(role_id=role_id)
        if not role:
            return None

        if role_data.name is not None:
            role.name = role_data.name
        if role_data.description is not None:
            role.description = role_data.description

        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def delete_role(self, role_id: int) -> bool:
        """Delete a role by ID.

        Args:
            role_id: Role ID

        Returns:
            bool: True if deleted, False if not found
        """
        role = self.get_role(role_id=role_id)
        if not role:
            return False

        self.db.delete(role)
        self.db.commit()
        return True

    def _get_association(self, user_id: int, role_id: int) -> Optional[UserRole]:
        return self.db.exec(
            select(UserRole).where(
                (UserRole.user_id == user_id) & (UserRole.role_id == role_id)
            )
        ).first()

    def assign_role_to_user(self, user_id: int, role_id: int) -> bool:
        """Assign a role to a user.

        Args:
            user_id: User ID
            role_id: Role ID

        Returns:
            bool: True if assigned, False if the user already had the role

        Raises:
            UserNotFoundException: If the user does not exist
            RoleNotFoundException: If the role does not exist
        """
        self._get_user_or_404(user_id)

        role = self.db.get(Role, role_id)
        if not role:
            raise RoleNotFoundException(f"Role with ID {role_id} not found")

        if self._get_association(user_id, role_id):
            return False

        self.db.add(UserRole(user_id=user_id, role_id=role_id))
        self.db.commit()
        return True

    def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
        """Remove a role from a user.

        Args:
            user_id: User ID
            role_id: Role ID

        Returns:
            bool: True if removed, False if the user did not have the role
        """
        user_role = self._get_association(user_id, role_id)
        if not user_role:
            return False

        self.db.delete(user_role)
        self.db.commit()
        return True

    def get_user_roles(self, user_id: int) -> List[Role]:
        """Get all roles for a user.

        Args:
            user_id: User ID

        Returns:
            List[Role]: User's roles

        Raises:
            UserNotFoundException: If the user does not exist
        """
        self._get_user_or_404(user_id)

        return list(
            self.db.exec(
                select(Role)
                .join(UserRole, Role.id == UserRole.role_id)
                .where(UserRole.user_id == user_id)
            ).all()
        )

    def user_has_role(self, user_id: int, role_name: str) -> bool:
        """Check if a user has a specific role.

        Args:
            user_id: User ID
            role_name: Role name

        Returns:
            bool: True if user has the role, False otherwise
        """
        role = self.get_role(role_name=role_name)
        if not role:
            return False
        return self._get_association(user_id, role.id) is not None

    def user_has_any_role(self, user_id: int, role_names: List[str]) -> bool:
        """Check if a user has at least one of the specified roles.

        Args:
            user_id: User ID
            role_names: List of role names

        Returns:
            bool: True if user has any of the roles, False otherwise
        """
        return any(self.user_has_role(user_id, role_name) for role_name in role_names)

    def user_has_all_roles(self, user_id: int, role_names: List[str]) -> bool:
        """Check if a user has all specified roles.

        Args:
            user_id: User ID
            role_names: List of role names

        Returns:
            bool: True if user has all roles, False otherwise
        """
        return all(self.user_has_role(user_id, role_name) for role_name in role_names)
