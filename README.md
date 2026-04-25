# ShangCloud SDK for Python

Python SDK，封装了授权登录与基础用户信息接口。

- Package: `shangcloud`
- Python 版本: 3.8+
- 无外部依赖（纯标准库）
- License: [MIT](../shangcloud-sdk-go/LICENSE)

## 安装

```bash
pip install shangcloud-sdk
```

## 快速开始

以下是一个基于 Flask 的完整 OAuth 授权码模式 (Authorization Code) 流程示例。

```python
from flask import Flask, redirect, request
from shangcloud import Client

app = Flask(__name__)

client = Client(
    client_id="your-client-id",
    client_secret="your-client-secret",
    redirect_uri="https://your-app.example.com/oauth/callback",
)

# 生成授权跳转 URL，将用户引导到授权页
@app.route("/login")
def login():
    return redirect(client.generate_oauth_url())

# 处理授权回调，使用 code 换取 User 实例
@app.route("/oauth/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")

    user = client.generate_user_instance(code, state)

    # 3. 拉取用户基本信息
    info = user.get_basic_info()
    return f"Hello, {info.nickname} (uid={info.user_id})"
```

## 核心 API

### `Client(client_id, client_secret, redirect_uri)`

创建 SDK 客户端。默认 `scope` 为 `user:basic`，`base_url` 为 `https://api.yearnstudio.cn`，并使用内置的内存 KV 作为 state 存储。如需自定义，可在返回的实例上直接赋值。

```python
client = Client("client-id", "client-secret", "https://example.com/callback")
# 工厂方法
client = Client.init_client("client-id", "client-secret", "https://example.com/callback")

# 覆盖默认值
client.scope    = "user:basic"
client.base_url = "https://api.yearnstudio.cn"
```

### `client.generate_oauth_url() -> str`

生成授权跳转 URL，内部随机生成 state 并写入 `kv_storage`，用于后续回调校验。

### `client.generate_user_instance(code, state) -> User`

校验 state，向 `/oauth/token` 换取 access token / refresh token，返回实现了 `User` 接口的实例。

异常：
- `StateNotFoundError` — state 不存在或已被消费（重放攻击防护）
- `AuthError` — 服务端授权失败（非 200 响应）
- `ShangCloudError` — 其他网络或服务端错误

### `client.set_client_secret(client_secret)`

更换 Client Secret。

```python
client.set_client_secret("new-secret")
```

### `User` 接口

```python
class User(ABC):
    def init_user(self, access_token, refresh_token, token_type, expires_in, client): ...
    def save(self) -> None: ...
    def is_expired(self) -> bool: ...
    def get_basic_info(self) -> UserBasicInfo: ...
```

SDK 提供了默认的内存实现 `UserInstance`。`is_expired()` 会提前 60 秒返回 `True`，`get_basic_info()` 会请求 `/api/user/info`。

### `UserBasicInfo`

```python
@dataclass
class UserBasicInfo:
    user_id: int      # uid
    nickname: str
    mail: str
    avatar: str
```

## 自定义扩展

### 自定义 state 存储

实现 `TempVarStorage` 抽象类，替换为 Redis 等共享存储，适用于多进程 / 多实例部署：

```python
from shangcloud import TempVarStorage, Client
import redis

class RedisKv(TempVarStorage):
    def __init__(self):
        self._r = redis.Redis()

    def set_temp_variable(self, key: str, value: str) -> None:
        self._r.setex(key, 300, value)  # 5 分钟过期

    def get_temp_variable(self, key: str) -> str:
        v = self._r.get(key)
        if v is None:
            raise KeyError(key)
        return v.decode()

    def delete_temp_variable(self, key: str) -> None:
        self._r.delete(key)

client = Client("id", "secret", "https://example.com/callback")
client.kv_storage = RedisKv()
```

实现须自行保证线程安全（内置 `RamKv` 已通过 `threading.Lock` 保证）。

### 自定义 User 持久化

继承 `User` 抽象类，在 `init_user` / `save` 中加入数据库持久化逻辑：

```python
from shangcloud import User, UserBasicInfo, Client

class SessionUser(User):
    def __init__(self, session: dict):
        self._session = session
        self._client: Client | None = None

    def init_user(self, access_token, refresh_token, token_type, expires_in, client):
        self._client = client
        self._session["access_token"]  = access_token
        self._session["refresh_token"] = refresh_token
        self._session["token_type"]    = token_type
        self._session["expires_in"]    = expires_in
        self.save()

    def save(self):
        pass  # session dict 自动持久化

    def is_expired(self) -> bool:
        from datetime import datetime, timedelta
        expiry = self._session.get("expiry_time")
        if expiry is None:
            return True
        return datetime.now() + timedelta(seconds=60) > expiry

    def get_basic_info(self) -> UserBasicInfo:
        return self._client._get_user_basic_info(
            self._session["access_token"],
            self._session["token_type"],
        )
```

## 注意事项

- **内存 KV 仅适用于单进程**。多 worker / 多进程部署（如 gunicorn 多进程模式）时，请替换 `kv_storage` 为 Redis 等共享存储，否则 state 校验会失败。
- `_client_secret` 与 token 字段均为私有属性，不会出现在 `vars(client)` 或日志中，但仍应避免将客户端对象直接序列化输出。
- `is_expired()` 提前 60 秒返回 `True`，确保 token 在请求过程中不会中途失效。
- SDK 不实现 token 刷新，`refresh_token` 由 `UserInstance` 存储但不主动使用；需要刷新时请自行调用平台的 refresh 端点后重建 `UserInstance`。

## License

[MIT](../shangcloud-sdk-go/LICENSE)
