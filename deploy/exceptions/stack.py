class StackException(Exception):

    def __init__(self, message: str, reason: str = None):
        super().__init__(message)

        self.reason = reason


class StackDoesNotExist(StackException):
    pass

class StackCreationFailed(StackException):
    pass

class StackNotChanged(StackException):
    pass

class StackUpdateFailed(StackException):
    pass

class StackAlreadyExist(StackException):
    pass

class TemplateValidationFailed(StackException):
    pass

class InvalidParameter(StackException):
    pass

class StackOutputsNotAvailable(StackException):
    pass

class StackNotInitialized(StackException):
    pass
