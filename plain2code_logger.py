import logging
import os
import time
from typing import Optional

from event_bus import EventBus
from plain2code_console import console
from plain2code_events import LogMessageEmitted


class RetryOnlyFilter(logging.Filter):
    def filter(self, record):
        # Allow all logs with level > DEBUG (i.e., INFO and above)
        if record.levelno > logging.DEBUG:
            return True
        # For DEBUG logs, only allow if message matches retry-related patterns
        msg = record.getMessage().lower()
        return (
            "retrying due to" in msg
            or "raising timeout error" in msg
            or "raising connection error" in msg
            or "encountered exception" in msg
            or "retrying request" in msg
            or "retry left" in msg
            or "1 retry left" in msg
            or "retries left" in msg
        )


class IndentedFormatter(logging.Formatter):
    def format(self, record):
        original_message = record.getMessage()

        modified_message = original_message.replace("\n", "\n                ")

        record.msg = modified_message
        return super().format(record)


class TuiLoggingHandler(logging.Handler):
    def __init__(self, event_bus: EventBus):
        super().__init__()
        self.event_bus = event_bus
        self._buffer = []
        self.start_time = time.time()  # Record start time for offset calculation

        # Register to be notified when event bus is ready
        self.event_bus.on_ready(self._flush_buffer)

    def emit(self, record):
        try:
            # Extract structured data from the log record

            # Original timestamp format (absolute time):
            # timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.created))

            # Calculate offset time from start of generation
            offset_seconds = record.created - self.start_time
            minutes = int(offset_seconds // 60)
            seconds = int(offset_seconds % 60)
            milliseconds = int((offset_seconds % 1) * 100)
            timestamp = f"{minutes:02d}:{seconds:02d}:{milliseconds:02d}"
            event = LogMessageEmitted(
                logger_name=record.name,
                level=record.levelname,
                message=record.getMessage(),
                timestamp=timestamp,
            )

            # Try to publish, fall back to buffering if not ready
            if self.event_bus._main_thread_callback:
                self.event_bus.publish(event)
            else:
                self._buffer.append(event)
        except Exception:
            self.handleError(record)

    def _flush_buffer(self):
        """Flush buffered log messages to the event bus."""
        for event in self._buffer:
            try:
                self.event_bus.publish(event)
            except Exception:
                pass
        self._buffer.clear()


class CrashLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)

    def dump_to_file(self, filepath, formatter=None):
        if not self.records:
            return False

        try:
            with open(filepath, "w") as f:
                for record in self.records:
                    if formatter:
                        msg = formatter.format(record)
                    else:
                        msg = self.format(record)
                    f.write(msg + "\n")
            return True
        except Exception:
            return False


def get_log_file_path(plain_file_path: Optional[str], log_file_name: str) -> Optional[str]:
    """Get the full path to the log file, relative to the plain file directory."""
    if not plain_file_path:
        return None
    plain_dir = os.path.dirname(os.path.abspath(plain_file_path))
    return os.path.join(plain_dir, log_file_name)


def dump_crash_logs(args, formatter=None):
    """Dump buffered logs to file if CrashLogHandler is present."""
    if args.log_to_file:
        return

    if formatter is None:
        formatter = IndentedFormatter("%(levelname)s:%(name)s:%(message)s")

    root_logger = logging.getLogger()
    crash_handler = next((h for h in root_logger.handlers if isinstance(h, CrashLogHandler)), None)

    if crash_handler and args.filename:
        log_file_path = get_log_file_path(args.filename, args.log_file_name)

        if crash_handler.dump_to_file(log_file_path, formatter):
            console.error(f"\nLogs have been dumped to {log_file_path}")
