from pydantic import BaseModel


class RegisterPayload(BaseModel):
    role: str
    display_name: str = ""