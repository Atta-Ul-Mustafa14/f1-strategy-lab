from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator


class Lap(BaseModel):
    session_key: int
    driver_number: int
    lap_number: int = Field(ge=1)
    lap_duration: Optional[float] = Field(default=None, gt=40, lt=300)  # null on some laps is normal
    is_pit_out_lap: bool = False
    date_start: Optional[str] = None


class Stint(BaseModel):
    session_key: int
    driver_number: int
    stint_number: int = Field(ge=1)
    lap_start: int = Field(ge=1)
    lap_end: int = Field(ge=1)
    compound: Literal["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"]
    tyre_age_at_start: Optional[int] = Field(default=0, ge=0)

    @model_validator(mode="after")
    def order(self):
        if self.lap_start > self.lap_end:
            raise ValueError("stint starts after it ends")
        return self


class Pit(BaseModel):
    session_key: int
    driver_number: int
    lap_number: int = Field(ge=1)
    pit_duration: float = Field(gt=1, lt=120)


class Weather(BaseModel):
    session_key: int
    date: str
    air_temperature: float = Field(ge=-10, le=60)
    track_temperature: float = Field(ge=-10, le=80)
    humidity: float = Field(ge=0, le=100)
    rainfall: int = Field(ge=0, le=1)
