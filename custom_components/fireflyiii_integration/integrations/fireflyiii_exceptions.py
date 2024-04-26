"""FireflyIII Integration FireflyIII Integration Exceptions"""


class AuthenticationError(Exception):
    """Exception for authentication errors."""


class ParseJSONError(Exception):
    """Exception for JSON parsing errors."""


class FireflyiiiException(Exception):
    """Base Exception"""


class UnknownError(FireflyiiiException):
    """Exception for Unknown errors."""


class MissingMethod(FireflyiiiException):
    """Exception for missing method variable."""


class UnsupportedFeature(FireflyiiiException):
    """Exception for firmware that is too old."""


class InvalidType(FireflyiiiException):
    """Exception for invalid types."""


class FireflyiiiObjectException(Exception):
    """Exception to FireflyIII Objects"""
