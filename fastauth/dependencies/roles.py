from typing import Callable, List, Optional, Union
from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select

from fastauth.models.user import User
from fastauth.models.role import Role, RoleCreate, RoleUpdate
from fastauth.dependencies.auth import AuthDependencies


class RoleDependencies:
    """Role-based authorization dependencies for FastAPI applications."""
    
    def __init__(self, auth_dependencies: AuthDependencies):
        """Initialize dependencies with AuthDependencies instance.
        
        Args:
            auth_dependencies: AuthDependencies instance for authentication
        """
        self.auth_deps = auth_dependencies
        self.auth = auth_dependencies.auth
    
    def require_roles(self, required_roles: List[str]):
        """Create a dependency that requires the user to have specific roles.
        
        Args:
            required_roles: List of role names required to access the endpoint
            
        Returns:
            callable: A dependency that validates if the user has the required roles
        """
        async def _require_roles(
            current_user: User = Depends(self.auth_deps.get_current_active_user()),
            db: Session = Depends(self.auth_deps.get_db_session())
        ):
            # Get role manager with the proper session
            role_manager = RoleManager(db)
            
            # Manually check if user has any of the required roles
            has_required_role = False
            for role_name in required_roles:
                if role_manager.user_has_role(current_user.id, role_name):
                    has_required_role = True
                    break
            
            if not has_required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return current_user
        return _require_roles
    
    def require_all_roles(self, required_roles: List[str]):
        """Create a dependency that requires the user to have all specified roles.
        
        Args:
            required_roles: List of role names, all of which are required
            
        Returns:
            callable: A dependency that validates if the user has all required roles
        """
        async def _require_all_roles(
            current_user: User = Depends(self.auth_deps.get_current_active_user()),
            db: Session = Depends(self.auth_deps.get_db_session())
        ):
            # Get role manager with the proper session
            role_manager = RoleManager(db)
            
            # Check if the user has all of the required roles
            if not role_manager.user_has_all_roles(current_user.id, required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return current_user
        return _require_all_roles
        
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
            return RoleManager(db)
        return _get_role_manager
        
    def get_current_active_user(self):
        """Get the current active user dependency from auth_deps.
        
        Returns:
            callable: A dependency that retrieves the current active user
        """
        return self.auth_deps.get_current_active_user()


class RoleManager:
    """Manages role operations in the database."""
    
    def __init__(self, db: Session):
        """Initialize with a database session.
        
        Args:
            db: SQLModel database session
        """
        self.db = db
        
    def create_role(self, role_data: RoleCreate) -> Role:
        """Create a new role.
        
        Args:
            role_data: Role creation data
            
        Returns:
            Role: The created role
            
        Raises:
            HTTPException: If a role with the same name already exists
        """
        # Check if role already exists
        existing_role = self.db.exec(
            select(Role).where(Role.name == role_data.name)
        ).first()
        
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{role_data.name}' already exists"
            )
            
        # Create new role
        role = Role(
            name=role_data.name,
            description=role_data.description
        )
        
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
            return self.db.exec(
                select(Role).where(Role.id == role_id)
            ).first()
            
        if role_name is not None:
            return self.db.exec(
                select(Role).where(Role.name == role_name)
            ).first()
            
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
            
        # Update fields if provided
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
        
    def assign_role_to_user(self, user_id: int, role_id: int) -> bool:
        """Assign a role to a user.
        
        Args:
            user_id: User ID
            role_id: Role ID
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            HTTPException: If user or role not found
        """
        from fastauth.models.user import UserRole
        
        # Get user
        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
            
        # Get role
        role = self.db.get(Role, role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
            
        # Check if the user already has this role
        user_role = self.db.exec(
            select(UserRole).where(
                (UserRole.user_id == user_id) & 
                (UserRole.role_id == role_id)
            )
        ).first()
        
        if user_role:
            # User already has this role
            return False
            
        # Create the association
        user_role = UserRole(user_id=user_id, role_id=role_id)
        self.db.add(user_role)
        self.db.commit()
        
        return True
        
    def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
        """Remove a role from a user.
        
        Args:
            user_id: User ID
            role_id: Role ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        from fastauth.models.user import UserRole
        
        # Find the user-role association
        user_role = self.db.exec(
            select(UserRole).where(
                (UserRole.user_id == user_id) & 
                (UserRole.role_id == role_id)
            )
        ).first()
        
        if not user_role:
            # Association doesn't exist
            return False
            
        # Remove the association
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
            HTTPException: If user not found
        """
        # Get user
        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
            
        # Get role IDs for this user from the association table
        from sqlmodel import select
        from fastauth.models.user import UserRole
        
        role_associations = self.db.exec(
            select(UserRole).where(UserRole.user_id == user_id)
        ).all()
        
        role_ids = [assoc.role_id for assoc in role_associations]
        
        # Get all roles with these IDs
        if not role_ids:
            return []
            
        roles = self.db.exec(
            select(Role).where(Role.id.in_(role_ids))
        ).all()
        
        return roles
        
    def user_has_role(self, user_id: int, role_name: str) -> bool:
        """Check if a user has a specific role.
        
        Args:
            user_id: User ID
            role_name: Role name
            
        Returns:
            bool: True if user has the role, False otherwise
        """
        # First get the role by name
        role = self.get_role(role_name=role_name)
        if not role:
            return False
            
        # Check if the user-role association exists
        from sqlmodel import select
        from fastauth.models.user import UserRole
        
        association = self.db.exec(
            select(UserRole).where(
                (UserRole.user_id == user_id) & 
                (UserRole.role_id == role.id)
            )
        ).first()
        
        return association is not None
        
    def user_has_all_roles(self, user_id: int, role_names: List[str]) -> bool:
        """Check if a user has all specified roles.
        
        Args:
            user_id: User ID
            role_names: List of role names
            
        Returns:
            bool: True if user has all roles, False otherwise
        """
        # Check each role individually
        return all(self.user_has_role(user_id, role_name) for role_name in role_names)
