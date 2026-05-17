from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class DiagramRequest(BaseModel):
    title: str
    source_code: str


class ParsedClass(BaseModel):
    name: str
    attributes: List[str]
    methods: List[str]


class DiagramResponse(BaseModel):
    title: str
    classes: List[ParsedClass]
    plantuml: str


class DiagramHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_code: str
    classes: List[ParsedClass]
    plantuml: str
    created_at: datetime