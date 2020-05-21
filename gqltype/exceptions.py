from typing import Optional, List, Union

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
    errors: "List[ValidationError]"

    def __init__(self, *args, errors: "List[ValidationError]" = (), **kwargs):
        super().__init__(*args, **kwargs)
        self.errors = errors
        self.extensions.update(
            errors=[self._format_validation_error(err) for err in errors]
        )

    def _format_validation_error(self, err):
        data = {"message": err.message}
        if err.code is not None:
            data["code"] = err.code
        if err.data is not None:
            data["data"] = err.data
        if err.fields is not None:
            data["fields"] = err.fields
        return data
