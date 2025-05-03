from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from fastauth.models.role import Role, RoleCreate, RoleRead, RoleUpdate
from fastauth.models.user import User
from fastauth.dependencies.roles import RoleDependencies, RoleManager


class RoleRouter:
    """Router for role-based authorization endpoints."""
    
    def __init__(self, role_deps: RoleDependencies, prefix: str = "/roles"):
        """Initialize with role dependencies.
        
        Args:
            role_deps: RoleDependencies instance
            prefix: API route prefix
        """
        self.router = APIRouter(prefix=prefix, tags=["roles"])
        self.role_deps = role_deps
        self.auth_deps = role_deps.auth_deps
        
        # Register routes
        self._register_routes()
        
    def _register_routes(self):
        """Register all role management routes."""
        
        @self.router.post(
            "/", 
            response_model=RoleRead,
            status_code=status.HTTP_201_CREATED,
            dependencies=[Depends(self.role_deps.is_admin())]
        )
        async def create_role(
            role_data: RoleCreate,
            role_manager: RoleManager = Depends(self.role_deps.get_role_manager())
        ):
            """Create a new role.
            
            Args:
                role_data: Role creation data
                role_manager: Role manager instance
                
            Returns:
                Role: The created role
            """
            return role_manager.create_role(role_data)
            
        @self.router.get(
            "/", 
            response_model=List[RoleRead],
            dependencies=[Depends(self.role_deps.get_current_active_user())]
        )
        async def get_all_roles(
            role_manager: RoleManager = Depends(self.role_deps.get_role_manager())
        ):
            """Get all roles.
            
            Args:
                role_manager: Role manager instance
                
            Returns:
                List[Role]: All roles
            """
            # Use SQLModel select to get all roles
            from sqlmodel import select
            roles = role_manager.db.exec(select(Role)).all()
            return roles
            
        @self.router.get(
            "/{role_id}", 
            response_model=RoleRead,
            dependencies=[Depends(self.role_deps.get_current_active_user())]
        )
        async def get_role(
            role_id: int,
            role_manager: RoleManager = Depends(self.role_deps.get_role_manager())
        ):
            """Get a role by ID.
            
            Args:
                role_id: Role ID
                role_manager: Role manager instance
                
            Returns:
                Role: The role
                
            Raises:
                HTTPException: If role not found
            """
            role = role_manager.get_role(role_id=role_id)
            
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Role with ID {role_id} not found"
                )
                
            return role
            
        @self.router.put(
            "/{role_id}", 
            response_model=RoleRead,
            dependencies=[Depends(self.role_deps.is_admin())]
        )
        async def update_role(
            role_id: int,
            role_data: RoleUpdate,
            role_manager: RoleManager = Depends(self.role_deps.get_role_manager())
        ):
            """Update a role.
            
            Args:
                role_id: Role ID
                role_data: Role update data
                role_manager: Role manager instance
                
            Returns:
                Role: The updated role
                
            Raises:
                HTTPException: If role not found
            """
            role = role_manager.update_role(role_id, role_data)
            
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Role with ID {role_id} not found"
                )
                
            return role
            
        @self.router.delete(
            "/{role_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            dependencies=[Depends(self.role_deps.is_admin())]
        )
        async def delete_role(
            role_id: int,
            role_manager: RoleManager = Depends(self.role_deps.get_role_manager())
        ):
            """Delete a role.
            
            Args:
                role_id: Role ID
                role_manager: Role manager instance
                
            Raises:
                HTTPException: If role not found
            """
            deleted = role_manager.delete_role(role_id)
            
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Role with ID {role_id} not found"
                )
                
        @self.router.post(
            "/assign/{user_id}/{role_id}",
            status_code=status.HTTP_200_OK,
            dependencies=[Depends(self.role_deps.is_admin())]
        )
        async def assign_role_to_user(
            user_id: int,
            role_id: int,
            role_manager: RoleManager = Depends(self.role_deps.get_role_manager())
        ):
            """Assign a role to a user.
            
            Args:
                user_id: User ID
                role_id: Role ID
                role_manager: Role manager instance
                
            Returns:
                dict: Success message
                
            Raises:
                HTTPException: If user or role not found
            """
            assigned = role_manager.assign_role_to_user(user_id, role_id)
            
            return {"message": "Role assigned successfully" if assigned else "User already has this role"}
            
        @self.router.delete(
            "/assign/{user_id}/{role_id}",
            status_code=status.HTTP_200_OK,
            dependencies=[Depends(self.role_deps.is_admin())]
        )
        async def remove_role_from_user(
            user_id: int,
            role_id: int,
            role_manager: RoleManager = Depends(self.role_deps.get_role_manager())
        ):
            """Remove a role from a user.
            
            Args:
                user_id: User ID
                role_id: Role ID
                role_manager: Role manager instance
                
            Returns:
                dict: Success message
                
            Raises:
                HTTPException: If association not found
            """
            removed = role_manager.remove_role_from_user(user_id, role_id)
            
            if not removed:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User does not have this role"
                )
                
            return {"message": "Role removed successfully"}
            
        @self.router.get(
            "/user/{user_id}",
            response_model=List[RoleRead],
            dependencies=[Depends(self.role_deps.get_current_active_user())]
        )
        async def get_user_roles(
            user_id: int,
            role_manager: RoleManager = Depends(self.role_deps.get_role_manager())
        ):
            """Get all roles for a user.
            
            Args:
                user_id: User ID
                role_manager: Role manager instance
                
            Returns:
                List[Role]: User's roles
                
            Raises:
                HTTPException: If user not found
            """
            return role_manager.get_user_roles(user_id)
