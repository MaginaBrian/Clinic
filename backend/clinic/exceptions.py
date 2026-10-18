from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler


class BookingError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "booking_error"

    def __init__(self, message: str, code: str | None = None):
        super().__init__(detail=message, code=code or self.default_code)


class InvalidSlot(BookingError):
    status_code = status.HTTP_400_BAD_REQUEST


class Conflict(BookingError):
    status_code = status.HTTP_409_CONFLICT


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, ValidationError):
        body = {"error": {"code": "validation_error", "message": "The request was invalid.", "details": response.data}}
    else:
        message = response.data.get("detail", "Request failed.") if isinstance(response.data, dict) else str(response.data)
        codes = exc.get_codes() if hasattr(exc, "get_codes") else "not_found"
        body = {"error": {"code": codes if isinstance(codes, str) else "error", "message": str(message)}}
    response.data = body
    return response
