from typing import List

from graphql import GraphQLError


class GeneralError(GraphQLError):
    code: str = "GENERAL_ERROR"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extensions.update(code=self.code)


class AuthenticationError(GeneralError):
    code: str = "UNAUTHENTICATED"


class ForbiddenError(GeneralError):
    code: str = "FORBIDDEN"


class UserInputError(GeneralError):
    code: str = "BAD_USER_INPUT"
    errors: List[dict]

    def __init__(self, *args, errors: List[dict], **kwargs):
        super().__init__(*args, **kwargs)
        self.errors = errors
        if not self.extensions:
            self.extensions = {}
        self.extensions.update(errors=errors)
