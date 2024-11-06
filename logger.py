import threading
import time


class Logger:
    def __init__(self):
        self.log_path = "latest.log"
        self.lock = threading.Lock()

        self.__init_logger_file()

    def __init_logger_file(self):
        open(self.log_path, "w").close()  # Create / clear file
        self.info("LOGGER", "Logger Initialized")

    def write(self, log_type, log_location, log_message):
        with self.lock:
            with open(self.log_path, "a") as log_file:
                data = f"{round(time.time())} - [{log_type}][{log_location}] {log_message}"

                log_file.write(data + "\n")
                print(data)

    def info(self, log_location, log_message):
        self.write("INFO", log_location, log_message)

    def warning(self, log_location, log_message):
        self.write("WARNING", log_location, log_message)

    def error(self, log_location, log_message):
        self.write("ERROR", log_location, log_message)

    def fatal(self, log_location, log_message):
        self.write("FATAL ERROR", log_location, log_message)
        exit("Logger Received Fatal Error - Check log file")

