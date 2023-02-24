from logging.handlers import RotatingFileHandler


class ServerRotatingFileHandler(RotatingFileHandler):
    def emit(self, record):
        if not hasattr(record, 'address'):
            setattr(record, 'address', 'None:None')
        return super().emit(record)
