class TemplateException(Exception):

    def __init__(self, message: str):
        super().__init__(message)


class TemplateNotFound(TemplateException):
    pass


class TemplateUploadError(TemplateException):
    pass


class TemplateBucketNotFound(TemplateException):
    pass


class InaccessibleTemplateBucket(TemplateException):
    pass


class TemplateBucketAlreadyExists(TemplateException):
    pass


class ZipNotFound(TemplateException):
    pass
