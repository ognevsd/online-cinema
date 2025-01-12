class UserServiceException(Exception):
    """Class for all exceptions related to User Service"""

    pass


class AuthServiceException(Exception):
    """Class for all exceptions related to Auth Service"""

    pass


class RoleServiceException(Exception):
    """Class for all exceptions related to Role Service"""

    pass


class RoleExists(RoleServiceException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class RoleNotFound(RoleServiceException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class UserExists(UserServiceException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class UserNotFound(UserServiceException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class WrongPassword(UserServiceException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidOauth(UserServiceException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class LoggedOut(AuthServiceException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidToken(AuthServiceException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class ExpiredToken(AuthServiceException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class InvalidRefreshToken(AuthServiceException):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
