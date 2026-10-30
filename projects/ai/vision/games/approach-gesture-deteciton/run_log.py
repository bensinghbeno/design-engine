"""Console mirroring and diagnostics for the most recent invocation."""

import logging
import shlex
import sys
import threading
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path


class ConsoleLog:
    def __init__(self, console, logfile, lock):
        self.console = console
        self.logfile = logfile
        self.lock = lock

    def write(self, text):
        with self.lock:
            self.console.write(text)
            self.logfile.write(text)
            self.logfile.flush()
        return len(text)

    def flush(self):
        with self.lock:
            self.console.flush()
            self.logfile.flush()

    def isatty(self):
        return False

    @property
    def encoding(self):
        return self.console.encoding


def run_logged(callback, path=None):
    path = Path(path) if path is not None else Path(__file__).with_name("last_run.log")
    logger = logging.getLogger("gesture_detection")
    previous_level = logger.level
    previous_propagate = logger.propagate
    previous_hook = threading.excepthook
    exit_code = 0
    with path.open("w", encoding="utf-8", buffering=1) as logfile:
        lock = threading.RLock()
        with redirect_stdout(ConsoleLog(sys.stdout, logfile, lock)), redirect_stderr(ConsoleLog(sys.stderr, logfile, lock)):
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(threadName)s] %(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            logger.propagate = False

            def thread_error(args):
                logger.error("Uncaught worker failure: %s", args.thread.name,
                             exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

            threading.excepthook = thread_error
            try:
                logger.info("Run started %s", datetime.now().astimezone().isoformat())
                logger.info("Command: %s", shlex.join([sys.executable, *sys.argv]))
                logger.info("Working directory: %s; log: %s", Path.cwd(), path.resolve())
                callback()
            except SystemExit as error:
                exit_code = error.code if isinstance(error.code, int) else (1 if error.code else 0)
                if error.code and not isinstance(error.code, int):
                    logger.error("%s", error.code)
            except KeyboardInterrupt:
                exit_code = 130
                logger.info("Interrupted by user")
            except Exception:
                exit_code = 1
                logger.exception("Run failed")
            finally:
                logger.info("Run ended; exit code=%s", exit_code)
                threading.excepthook = previous_hook
                logger.removeHandler(handler)
                handler.close()
                logger.setLevel(previous_level)
                logger.propagate = previous_propagate
    return exit_code