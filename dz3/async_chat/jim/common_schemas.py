from pydantic import BaseModel, Field
import datetime as dt


class TimeBase(BaseModel):
    time: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc)
    )

    class Config:
        json_encoders = {
            dt.datetime: lambda v: v.timestamp(),
        }


class ActionTimeBase(TimeBase):
    action: str = Field(min_length=0, max_length=15)
