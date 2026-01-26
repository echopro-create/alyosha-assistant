
import logging
from PyQt6.QtCore import QObject, pyqtSignal

class QLogHandler(logging.Handler):
    """
    Log Handler that emits a signal with the log message.
    Connect to 'log_signal' to receive colored/formatted logs.
    """
    def __init__(self, parent=None):
        super().__init__()
        self.emitter = QLogEmitter(parent)

    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname
            self.emitter.log_signal.emit(msg, level)
        except Exception:
            self.handleError(record)

class QLogEmitter(QObject):
    """Separator object to hold the signal (logging.Handler is not QObject)"""
    log_signal = pyqtSignal(str, str)  # message, level
