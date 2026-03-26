from typing import Literal

from pydantic import BaseModel, ConfigDict


class RedirectorDataPool(BaseModel):
    model_config = ConfigDict(extra="ignore")

    origins: dict[str, str]


class RedirectorData(BaseModel):
    version: Literal["1.0"]
    pools: list[RedirectorDataPool]


class MirrorLinks(BaseModel):
    mirrors: list[str]
