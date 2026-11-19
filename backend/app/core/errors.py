class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 422, fields=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.fields = fields
