from dataclasses import dataclass
from typing import Optional


@dataclass
class UserBasicInfo:
    user_id: int    # uid
    nickname: str
    mail: str
    avatar: str


@dataclass
class MMONewRoomResponse:
    connect_key: str
    edge_url: str
    room_id: str
    protocol: str


@dataclass
class MMOJoinRoomResponse:
    connect_key: str
    edge_url: str
    room_id: str
    protocol: str
    assigned_uid: Optional[str] = None
