from pydantic import BaseModel, Field
import datetime as dt
import uuid


class TimeBase(BaseModel):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid1())
    )
    time: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc)
    )

    class Config:
        json_encoders = {
            dt.datetime: lambda v: v.timestamp(),
        }


class ActionTimeBase(TimeBase):
    action: str = Field(min_length=0, max_length=15)


class UserBase(BaseModel):
    account_name: str = Field(min_length=3, max_length=25)
