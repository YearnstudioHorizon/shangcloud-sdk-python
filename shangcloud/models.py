from dataclasses import dataclass


@dataclass
class UserBasicInfo:
    user_id: int    # uid
    nickname: str
    mail: str
    avatar: str
