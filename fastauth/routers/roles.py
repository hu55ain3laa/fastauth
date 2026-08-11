from typing import List

from fastapi import APIRouter, Depends, status
from sqlmodel import select

from fastauth.models.role import Role, RoleCreate, RoleRead, RoleUpdate
from fastauth.dependencies.roles import RoleDependencies, RoleManager
from fastauth.exceptions import RoleNotFoundException


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

        self._register_routes()

    def _register_routes(self):
        """Register all role management routes."""

        @self.router.post(
            "/",
            response_model=RoleRead,
            status_code=status.HTTP_201_CREATED,
            dependencies=[Depends(self.role_deps.is_admin())],
        )
        async def create_role(
            role_data: RoleCreate,
            role_manager: RoleManager = Depends(self.role_deps.get_role_manager()),
        ):
            """Create a new role (admin only)."""
            return role_manager.create_role(role_data)

        @self.router.get(
            "/",
            response_model=List[RoleRead],
            dependencies=[Depends(self.role_deps.get_current_active_user())],
        )
        async def get_all_roles(
            role_manager: RoleManager = Depends(self.role_deps.get_role_manager()),
        ):
            """Get all roles."""
            return role_manager.db.exec(select(Role)).all()

        @self.router.get(
            "/{role_id}",
            response_model=RoleRead,
            dependencies=[Depends(self.role_deps.get_current_active_user())],
        )
        async def get_role(
            role_id: int,
            role_manager: RoleManager = Depends(self.role_deps.get_role_manager()),
        ):
            """Get a role by ID."""
            role = role_manager.get_role(role_id=role_id)
            if not role:
                raise RoleNotFoundException(f"Role with ID {role_id} not found")
            return role

        @self.router.put(
            "/{role_id}",
            response_model=RoleRead,
            dependencies=[Depends(self.role_deps.is_admin())],
        )
        async def update_role(
            role_id: int,
            role_data: RoleUpdate,
            role_manager: RoleManager = Depends(self.role_deps.get_role_manager()),
        ):
            """Update a role (admin only)."""
            role = role_manager.update_role(role_id, role_data)
            if not role:
                raise RoleNotFoundException(f"Role with ID {role_id} not found")
            return role

        @self.router.delete(
            "/{role_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            dependencies=[Depends(self.role_deps.is_admin())],
        )
        async def delete_role(
            role_id: int,
            role_manager: RoleManager = Depends(self.role_deps.get_role_manager()),
        ):
            """Delete a role (admin only)."""
            deleted = role_manager.delete_role(role_id)
            if not deleted:
                raise RoleNotFoundException(f"Role with ID {role_id} not found")

        @self.router.post(
            "/assign/{user_id}/{role_id}",
            status_code=status.HTTP_200_OK,
            dependencies=[Depends(self.role_deps.is_admin())],
        )
        async def assign_role_to_user(
            user_id: int,
            role_id: int,
            role_manager: RoleManager = Depends(self.role_deps.get_role_manager()),
        ):
            """Assign a role to a user (admin only)."""
            assigned = role_manager.assign_role_to_user(user_id, role_id)
            return {
                "message": "Role assigned successfully" if assigned else "User already has this role"
            }

        @self.router.delete(
            "/assign/{user_id}/{role_id}",
            status_code=status.HTTP_200_OK,
            dependencies=[Depends(self.role_deps.is_admin())],
        )
        async def remove_role_from_user(
            user_id: int,
            role_id: int,
            role_manager: RoleManager = Depends(self.role_deps.get_role_manager()),
        ):
            """Remove a role from a user (admin only)."""
            removed = role_manager.remove_role_from_user(user_id, role_id)
            if not removed:
                raise RoleNotFoundException("User does not have this role")
            return {"message": "Role removed successfully"}

        @self.router.get(
            "/user/{user_id}",
            response_model=List[RoleRead],
            dependencies=[Depends(self.role_deps.get_current_active_user())],
        )
        async def get_user_roles(
            user_id: int,
            role_manager: RoleManager = Depends(self.role_deps.get_role_manager()),
        ):
            """Get all roles for a user."""
            return role_manager.get_user_roles(user_id)
