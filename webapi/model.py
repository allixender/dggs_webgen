from pydantic import BaseModel

class SimpleMessage(BaseModel):
    status: str
    message: str

