class ShangCloudError(Exception):
    pass


class StateNotFoundError(ShangCloudError):
    pass


class AuthError(ShangCloudError):
    pass
