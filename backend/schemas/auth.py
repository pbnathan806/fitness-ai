import uuid

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: uuid.UUID
    roles: list[str]


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str = (
        "If an account with that email exists, a password reset link has been sent."
    )


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class ResetPasswordResponse(BaseModel):
    message: str = "Password has been reset successfully."


class RolesResponse(BaseModel):
    roles: list[str]
    active_role: str | None = None


class SwitchRoleRequest(BaseModel):
    role: str = Field(min_length=1)


class SwitchRoleResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    active_role: str
    roles: list[str]
