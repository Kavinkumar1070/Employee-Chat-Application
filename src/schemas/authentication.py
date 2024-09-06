from pydantic import BaseModel


class TokenData(BaseModel):
    employee_id: int | None = None
