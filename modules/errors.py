from typing import Any, Dict


class HttpException(Exception):
    def __init__(self, response_code: int, data: Dict[str, Any]):
        self.response_code = response_code
        self.data = data
        super(HttpException, self).__init__("HTTP Response Error: {}".format(response_code))


class Unauthorized(HttpException):
    """로그인이 실패되었을 때 발생합니다.."""

    pass


class BadRequest(HttpException):
    """알수 없는 오류가 발생 했을 때, 발생하는 예외입니다."""

    pass


class Forbidden(HttpException):
    """접근이 거부되었을 때, 발생하는 예외입니다."""

    pass


class NotFound(HttpException):
    """유저를 찾지 못할때 발생합니다."""

    pass


class MethodNotAllowed(HttpException):
    """Method 접근이 거부되었을 때, 발생하는 예외입니다."""

    pass


class TooManyRequests(HttpException):
    """너무 많은 요청이 들어 왔을 때, 발생하는 예외입니다."""

    pass


class InternalServerError(HttpException):
    """API 서버에서 문제가 발생 했을 때, 발생하는 예외입니다."""

    pass


class ServiceUnavailable(HttpException):
    """API 서버가 점검 중일 때, 발생하는 예외입니다."""

    pass
