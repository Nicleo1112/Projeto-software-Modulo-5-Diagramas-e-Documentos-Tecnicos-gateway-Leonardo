from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class DiagramRequest(BaseModel):
    title: str
    source_code: str
    diagram_type: Optional[str] = "uml-class"
    project_id: Optional[str] = None
    project_name: Optional[str] = None


class ParsedClass(BaseModel):
    name: str
    attributes: List[str]
    methods: List[str]


class DiagramResponse(BaseModel):
    title: str
    diagram_type: str
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    classes: List[ParsedClass]
    plantuml: str


class DiagramHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_code: str
    classes: List[ParsedClass]
    plantuml: str
    diagram_type: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    created_at: datetime


class ApiDocsRequest(BaseModel):
    title: str
    source_code: str
    project_id: Optional[str] = None
    project_name: Optional[str] = None


class ApiEndpoint(BaseModel):
    method: str
    path: str
    framework: str
    description: str


class ApiDocsResponse(BaseModel):
    title: str
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    endpoints: List[ApiEndpoint]


class SourceFile(BaseModel):
    path: str
    content: str


class AiAnalyzeRequest(BaseModel):
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    source_code: Optional[str] = None
    repository_url: Optional[str] = None
    branch: Optional[str] = None
    files: Optional[List[SourceFile]] = None


class AiAnalyzeResponse(BaseModel):
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    summary: str
    suggested_diagram_type: str
    detected_profiles: List[str]
    architecture_notes: List[str]
    possible_entities: List[str]
    possible_relationships: List[str]
