python
from pydantic import BaseModel
from typing import List


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
