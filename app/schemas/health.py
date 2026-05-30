from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class HealthCheck(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    environment: str
    timestamp: datetime

