# app/models/link_schemas.py
from pydantic import BaseModel, HttpUrl, field_validator
from typing import List, Optional, Dict
import re


class LinkCreate(BaseModel):
    slug: Optional[str] = None  # ahora es opcional
    title: str
    destinationUrl: HttpUrl
    variants: Optional[List[str]] = ["default"]

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if not (1 <= len(v) <= 120):
            raise ValueError("title must be between 1 and 120 characters")
        return v.strip()

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v):
        if v is None:  # permitir None
            return v
        pattern = r"^[a-z0-9-]{3,48}$"
        if not re.match(pattern, v):
            raise ValueError("slug must match ^[a-z0-9-]{3,48}$")
        return v.strip().lower()

    @field_validator("variants")
    @classmethod
    def validate_variants(cls, v):
        if not v:
            return ["default"]
        if len(v) > 20:
            raise ValueError("variants cannot exceed 20")
        clean = []
        for variant in v:
            if not re.match(r"^[a-z0-9_-]{1,32}$", variant):
                raise ValueError(f"invalid variant '{variant}'")
            if variant in clean:
                raise ValueError(f"duplicate variant '{variant}'")
            clean.append(variant)
        return clean


class LinkOut(BaseModel):
    linkId: str
    slug: str
    title: str
    destinationUrl: HttpUrl
    variants: List[str]
    createdAt: str


class MetricTotals(BaseModel):
    clicks: int
    byVariant: Dict[str, int]
    byDevice: Dict[str, int]
    byCountry: Dict[str, int]
