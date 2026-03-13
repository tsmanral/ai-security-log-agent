import os
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Local imports
try:
    from database import insert_log, init_db
    from log_parser import parse_syslog_sshd
except ImportError:
    from agent.database import insert_log, init_db
    from agent.log_parser import parse_syslog_sshd

logger = logging.getLogger(__name__)

class LogFileHandler(FileSystemEventHandler):
    """Event handler for monitoring changes to log files."""
    def __init__(self, watch_file: Path):
        self.watch_file = watch_file
        self.file_pos = 0
        super().__init__()
        
        # Read initial file if exists
        self._process_existing()

    def _process_existing(self):
        """Process any existing lines in the file before tailing."""
        if not self.watch_file.exists():
            return
            
        with open(self.watch_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                self._process_line(line)
            # Update position
            self.file_pos = f.tell()

    def _process_line(self, line: str):
        """Parse and store a single log line."""
        line = line.strip()
        if not line:
            return
            
        parsed_event = parse_syslog_sshd(line)
        if parsed_event:
            insert_log(parsed_event)
            logger.debug(f"Inserted event: {parsed_event.get('event_type')} from {parsed_event.get('src_ip')}")

    def on_modified(self, event):
        """Called when a file or directory is modified."""
        if os.path.abspath(event.src_path) == os.path.abspath(self.watch_file):
            # The monitored file was modified, let's tail the new lines
            try:
                with open(self.watch_file, 'r') as f:
                    f.seek(self.file_pos)
                    lines = f.readlines()
                    for line in lines:
                        self._process_line(line)
                    self.file_pos = f.tell()
            except IOError as e:
                logger.error(f"Error reading {self.watch_file}: {e}")

def collect_historical_logs(log_file: Path) -> int:
    """Read a log file from start to finish and parse it."""
    count = 0
    if not log_file.exists():
        logger.warning(f"Log file not found at {log_file}")
        return count
        
    logger.info(f"Processing historical logs from {log_file}...")
    with open(log_file, 'r') as f:
        for line in f:
            parsed_event = parse_syslog_sshd(line.strip())
            if parsed_event:
                insert_log(parsed_event)
                count += 1
                
    logger.info(f"Completed processing historical logs. {count} events stored.")
    return count

def start_collector(log_file: Path):
    """Start real-time monitoring of a log file."""
    # Ensure tables exist
    init_db()
    
    # Process historical lines first
    collect_historical_logs(log_file)
    
    logger.info(f"Starting real-time collector on {log_file}")
    event_handler = LogFileHandler(log_file)
    observer = Observer()
    
    # Start watching the directory
    observer.schedule(event_handler, path=str(log_file.parent), recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Log collector stopped by user.")
    observer.join()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Test path
    target_log = Path(__file__).parent.parent / "logs" / "generated_auth.log"
    
    if target_log.exists():
        start_collector(target_log)
    else:
        logger.error(f"Cannot find log file: {target_log}. Run generate_ssh_logs.py first.")
