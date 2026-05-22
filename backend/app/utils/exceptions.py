from __future__ import annotations


class AppError(Exception):
    pass


class DatabaseUnavailableError(AppError):
    pass


class RecordNotFoundError(AppError):
    pass


class MultipleRecordsFoundError(AppError):
    pass
