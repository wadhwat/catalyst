from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class InspectionPreferences(BaseModel):
    inspectionCadenceHours: int = Field(default=12, ge=1)
    captureMaxDurationSec: int = Field(default=120, ge=1)
    frameSampleFps: int = Field(default=1, ge=1)
    captureResolution: Literal['720p', '1080p'] = '1080p'
    autoUpload: bool = True


class MachinePreferences(BaseModel):
    inspectionCadenceHours: Optional[int] = Field(default=None, ge=1)
    captureMaxDurationSec: Optional[int] = Field(default=None, ge=1)
    frameSampleFps: Optional[int] = Field(default=None, ge=1)
    captureResolution: Optional[Literal['720p', '1080p']] = None
    autoUpload: Optional[bool] = None


class PreferencesResponse(BaseModel):
    preferences: InspectionPreferences
    effective_preferences: InspectionPreferences
    updated_at: Optional[datetime] = None
    source: Literal['default', 'memory']


class MachinePreferencesResponse(BaseModel):
    preferences: MachinePreferences
    effective_preferences: InspectionPreferences
    updated_at: Optional[datetime] = None
    source: Literal['default', 'memory']


DEFAULT_PREFERENCES = InspectionPreferences()
