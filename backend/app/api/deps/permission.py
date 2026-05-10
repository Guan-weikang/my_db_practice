from fastapi import HTTPException, status


def require_role(allowed_roles: set[str], actual_role: str) -> None:
    if actual_role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

