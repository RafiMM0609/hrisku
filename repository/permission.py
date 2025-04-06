"""
This file need sets to user KIS (keep it simple) method
this file build to make curd for role permssion in this apps
"""
import calendar
from typing import List
from core.rafiexcel import RafiExcel, blue_fill, yellow_fill
from models import SessionLocal
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timedelta, date
from models.Role import Role
from models.RolePermission import RolePermission
from models.Module import Module
from models.Permission import Permission
from models.User import User
from tempfile import NamedTemporaryFile
from starlette.datastructures import UploadFile
from core.file import upload_file, upload_file_to_tmp
import io
from schemas.permission import (
    RolePermissionSchema,
    PermissionSchema
)

async def get_data_permission_table(
    db: Session,
    role_id: str,
) -> List[RolePermissionSchema]:
    """
    Fetch permissions for a specific role and return them as a list of RolePermissionSchema.
    """
    try:
        # Query RolePermission and join with Permission and Module to get the required data
        query = (
            db.query(
                RolePermission.c.id.label("role_permission_id"),
                RolePermission.c.isact.label("role_permission_isact"),
                Permission.id.label("permission_id"),
                Permission.name.label("permission_name"),
                Module.name.label("module_name")
            )
            .join(Permission, RolePermission.c.permission_id == Permission.id)
            .join(Module, Permission.module_id == Module.id)
            .filter(
                RolePermission.c.role_id == role_id,
                RolePermission.c.isact == True,
                Permission.isact == True,
            )
            .order_by(Module.name)  # Order by module name for better grouping
        )
        role_permissions = query.all()

        # Group permissions by module name
        module_permissions = {}
        for rp in role_permissions:
            module_name = rp.module_name
            if module_name not in module_permissions:
                module_permissions[module_name] = []
            module_permissions[module_name].append(
                PermissionSchema(
                    id=rp.role_permission_id,
                    name=rp.permission_name,
                    isact=rp.role_permission_isact,
                )
            )

        # Map the grouped data to RolePermissionSchema
        result = [
            RolePermissionSchema(
                name=module_name,
                permissions=permissions
            ).model_dump()
            for module_name, permissions in module_permissions.items()
        ]

        return result
    except Exception as e:
        print(f"Error when fetching permission data for role_id={role_id}: {e}")
        raise ValueError("Failed to fetch permission data")
    

async def edit_permission(
    db: Session,
    role_permission_id: str,
):
    """
    This function is used to edit role permissions.
    It toggles the 'isact' field (active status) of a role permission based on its current value.
    """
    try:
        # Fetch the existing role permission record
        role_permission = db.execute(
            RolePermission.select().where(RolePermission.c.id == role_permission_id)
        ).fetchone()

        if not role_permission:
            raise ValueError(f"Role permission with ID {role_permission_id} not found")

        # Toggle the isact value
        new_isact = not role_permission.isact

        # Update the isact value in the database
        db.execute(
            RolePermission.update()
            .where(RolePermission.c.id == role_permission_id)
            .values(isact=new_isact)
        )
        db.commit()

        return {
            "message": "Permission updated successfully",
            "data": {
                "id": role_permission_id,
                "isact": new_isact,
            },
        }
    except ValueError as ve:
        # Handle specific errors like missing role permission
        print(f"Validation error: {ve}")
        raise ve
    except Exception as e:
        # Log unexpected errors
        print(f"Unexpected error when editing permission: {e}")
        db.rollback()  # Rollback the transaction in case of an error
        raise ValueError("An unexpected error occurred while editing the permission")