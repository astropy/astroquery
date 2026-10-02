import inspect
import logging
import sys
import warnings
from contextlib import contextmanager
from pathlib import Path

from astropy import config as _config
from astropy.utils import find_current_module
from astropy.utils.exceptions import AstropyUserWarning, AstropyWarning


_WITHIN_IPYTHON = "__IPYTHON__" in globals()


class LoggingError(Exception):
    """Raised when a logging feature cannot be enabled or disabled."""


class _AstroqueryIPythonException(Exception):
    """Marker used to register Astroquery's IPython exception handler."""


class Conf(_config.ConfigNamespace):
    """Configuration parameters for the Astroquery logger."""

    log_level = _config.ConfigItem(
        "INFO",
        "Threshold for the logging messages. Logging "
        "messages that are less severe than this level "
        "will be ignored. The levels are ``'DEBUG'``, "
        "``'INFO'``, ``'WARNING'``, ``'ERROR'``.",
    )
    use_color = _config.ConfigItem(True, "Whether to color terminal log output.")
    log_warnings = _config.ConfigItem(True, "Whether to log `warnings.warn` calls.")
    log_exceptions = _config.ConfigItem(
        False, "Whether to log exceptions before raising them."
    )
    log_to_file = _config.ConfigItem(
        False, "Whether to always log messages to a log file."
    )
    log_file_path = _config.ConfigItem(
        "",
        "The file to log messages to.  If empty string is given, "
        "it defaults to a file ``'astropy.log'`` in "
        "the astropy config directory.",
    )
    log_file_level = _config.ConfigItem(
        "INFO", "Threshold for logging messages to `log_file_path`."
    )
    log_file_format = _config.ConfigItem(
        "%(asctime)r, %(origin)r, %(levelname)r, %(message)r",
        "Format for log file entries.",
    )
    log_file_encoding = _config.ConfigItem(
        "",
        "The encoding (e.g., UTF-8) to use for the log file.  If empty string "
        "is given, it defaults to the platform-preferred encoding.",
    )


conf = Conf()
Logger = logging.getLoggerClass()


class AstroqueryLogger(Logger):
    """Astroquery's logger with origin tracking and capture helpers."""

    def makeRecord(
        self, name, level, pathname, lineno, msg, args, exc_info,
        func=None, extra=None, sinfo=None,
    ):
        if extra is None:
            extra = {}
        if "origin" not in extra:
            current_module = find_current_module(1, finddiff=[True, "logging"])
            extra["origin"] = (
                current_module.__name__ if current_module is not None else "unknown"
            )
        return Logger.makeRecord(
            self, name, level, pathname, lineno, msg, args, exc_info,
            func=func, extra=extra, sinfo=sinfo,
        )

    _showwarning_orig = None

    def _showwarning(self, *args, **kwargs):
        if not isinstance(args[0], AstropyWarning):
            return self._showwarning_orig(*args, **kwargs)

        warning = args[0]
        if type(warning) not in (AstropyWarning, AstropyUserWarning):
            message = f"{warning.__class__.__name__}: {warning}"
        else:
            message = str(warning)

        module_path = Path(args[2]).with_suffix("")
        module_name = None
        for module in sys.modules.values():
            try:
                path = Path(getattr(module, "__file__", "")).with_suffix("")
            except Exception:
                continue
            if path == module_path:
                module_name = module.__name__
                break

        if module_name is not None:
            self.warning(message, extra={"origin": module_name})
        else:
            self.warning(message)

    def warnings_logging_enabled(self):
        """Return whether ``warnings.warn`` calls are captured."""
        return self._showwarning_orig is not None

    def enable_warnings_logging(self):
        """Redirect subsequent Astropy warnings to this logger."""
        if self.warnings_logging_enabled():
            raise LoggingError("Warnings logging has already been enabled")
        self._showwarning_orig = warnings.showwarning
        warnings.showwarning = self._showwarning

    def disable_warnings_logging(self):
        """Restore normal handling for ``warnings.warn`` calls."""
        if not self.warnings_logging_enabled():
            raise LoggingError("Warnings logging has not been enabled")
        if warnings.showwarning != self._showwarning:
            raise LoggingError(
                "Cannot disable warnings logging: warnings.showwarning was not set "
                "by this logger, or has been overridden"
            )
        warnings.showwarning = self._showwarning_orig
        self._showwarning_orig = None

    _excepthook_orig = None

    def _excepthook(self, exception_type, value, traceback):
        if traceback is None:
            module = None
        else:
            final_traceback = traceback
            while final_traceback.tb_next is not None:
                final_traceback = final_traceback.tb_next
            module = inspect.getmodule(final_traceback)

        message = (
            f"{exception_type.__name__}: {value}"
            if value.args else exception_type.__name__
        )
        if module is not None:
            self.error(message, extra={"origin": module.__name__})
        else:
            self.error(message)
        self._excepthook_orig(exception_type, value, traceback)

    def exception_logging_enabled(self):
        """Return whether uncaught exceptions are captured."""
        if _WITHIN_IPYTHON:
            from IPython import get_ipython
            return _AstroqueryIPythonException in get_ipython().custom_exceptions
        return self._excepthook_orig is not None

    def enable_exception_logging(self):
        """Log uncaught exceptions before the interpreter displays them."""
        if self.exception_logging_enabled():
            raise LoggingError("Exception logging has already been enabled")

        if _WITHIN_IPYTHON:
            from IPython import get_ipython

            def ipython_exception_handler(shell, exception_type, value, traceback,
                                          traceback_offset=None):
                self._excepthook(exception_type, value, traceback)
                shell.showtraceback(
                    (exception_type, value, traceback), tb_offset=traceback_offset
                )

            get_ipython().set_custom_exc(
                (BaseException, _AstroqueryIPythonException),
                ipython_exception_handler,
            )
            self._excepthook_orig = lambda exception_type, value, traceback: None
        else:
            self._excepthook_orig = sys.excepthook
            sys.excepthook = self._excepthook

    def disable_exception_logging(self):
        """Restore normal uncaught-exception handling."""
        if not self.exception_logging_enabled():
            raise LoggingError("Exception logging has not been enabled")

        if _WITHIN_IPYTHON:
            from IPython import get_ipython
            get_ipython().set_custom_exc((), None)
        else:
            if sys.excepthook != self._excepthook:
                raise LoggingError(
                    "Cannot disable exception logging: sys.excepthook was not set "
                    "by this logger, or has been overridden"
                )
            sys.excepthook = self._excepthook_orig
            self._excepthook_orig = None

    def enable_color(self):
        """Enable colorized terminal output."""
        conf.use_color = True

    def disable_color(self):
        """Disable colorized terminal output."""
        conf.use_color = False

    @contextmanager
    def log_to_file(self, filename, filter_level=None, filter_origin=None):
        """Temporarily write log records to ``filename``."""
        encoding = conf.log_file_encoding or None
        handler = logging.FileHandler(filename, encoding=encoding)
        if filter_level is not None:
            handler.setLevel(filter_level)
        if filter_origin is not None:
            handler.addFilter(FilterOrigin(filter_origin))
        handler.setFormatter(logging.Formatter(conf.log_file_format))
        self.addHandler(handler)
        try:
            yield
        finally:
            handler.close()
            self.removeHandler(handler)

    @contextmanager
    def log_to_list(self, filter_level=None, filter_origin=None):
        """Temporarily capture log records in a list."""
        handler = ListHandler()
        if filter_level is not None:
            handler.setLevel(filter_level)
        if filter_origin is not None:
            handler.addFilter(FilterOrigin(filter_origin))
        self.addHandler(handler)
        try:
            yield handler.log_list
        finally:
            self.removeHandler(handler)

    def _set_defaults(self):
        """Reset this logger to its configured initial state."""
        if self.warnings_logging_enabled():
            self.disable_warnings_logging()
        if self.exception_logging_enabled():
            self.disable_exception_logging()

        for handler in self.handlers[:]:
            self.removeHandler(handler)

        self.setLevel(conf.log_level)
        self.addHandler(StreamHandler())

        if conf.log_to_file:
            log_file_path = conf.log_file_path
            try:
                if not log_file_path:
                    log_file_path = _config.get_config_dir_path("astroquery") / "astroquery.log"
                else:
                    log_file_path = Path(log_file_path).expanduser()
                encoding = conf.log_file_encoding or None
                handler = logging.FileHandler(log_file_path, encoding=encoding)
            except OSError as error:
                warnings.warn(
                    f"log file {log_file_path!r} could not be opened for writing: {error}",
                    RuntimeWarning,
                )
            else:
                handler.setFormatter(logging.Formatter(conf.log_file_format))
                handler.setLevel(conf.log_file_level)
                self.addHandler(handler)

        if conf.log_warnings:
            self.enable_warnings_logging()
        if conf.log_exceptions:
            self.enable_exception_logging()


class StreamHandler(logging.StreamHandler):
    """Write lower-severity records to stdout and others to stderr."""

    def emit(self, record):
        stream = sys.stdout if record.levelno <= logging.INFO else sys.stderr

        if record.levelno < logging.DEBUG or not conf.use_color:
            print(record.levelname, end="", file=stream)
        else:
            from astropy.utils.console import color_print

            if record.levelno < logging.INFO:
                color_print(record.levelname, "magenta", end="", file=stream)
            elif record.levelno < logging.WARNING:
                color_print(record.levelname, "green", end="", file=stream)
            elif record.levelno < logging.ERROR:
                color_print(record.levelname, "brown", end="", file=stream)
            else:
                color_print(record.levelname, "red", end="", file=stream)

        if record.args:
            record.message = f"{record.msg % record.args} [{record.origin:s}]"
        else:
            record.message = f"{record.msg} [{record.origin:s}]"
        print(": " + record.message, file=stream)


class FilterOrigin:
    """Filter records to origins beginning with a specified value."""

    def __init__(self, origin):
        self.origin = origin

    def filter(self, record):
        return record.origin.startswith(self.origin)


class ListHandler(logging.Handler):
    """Capture records in ``log_list``."""

    def __init__(self):
        super().__init__()
        self.log_list = []

    def emit(self, record):
        self.log_list.append(record)


def _config_to_logger_conf(config):
    """Apply legacy ``[logger]`` configuration values to this logger."""
    if not config.has_section("logger"):
        return

    option_names = (
        "log_level", "use_color", "log_warnings", "log_exceptions", "log_to_file",
        "log_file_path", "log_file_level", "log_file_format", "log_file_encoding",
    )
    for option_name in option_names:
        if config.has_option("logger", option_name):
            setattr(conf, option_name, config.get("logger", option_name))


def _init_log(config=None):
    """Initialize and return Astroquery's independent logger instance."""
    original_logger_class = logging.getLoggerClass()
    logging.setLoggerClass(AstroqueryLogger)
    try:
        logger = logging.getLogger("astroquery")
        if config is not None:
            _config_to_logger_conf(config)
        logger._set_defaults()
    finally:
        logging.setLoggerClass(original_logger_class)

    return logger
