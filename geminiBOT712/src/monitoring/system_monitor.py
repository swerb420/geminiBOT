# src/monitoring/system_monitor.py
# Monitors the health of the host system (CPU, RAM, Disk).

import psutil
import asyncio
from utils.logger import get_logger
from .alert_manager import send_system_alert

logger = get_logger(__name__)

class SystemMonitor:
    """Monitors the health of the VPS itself."""
    def __init__(self, cpu_threshold=90.0, mem_threshold=90.0, disk_threshold=95.0):
        self.cpu_threshold = cpu_threshold
        self.mem_threshold = mem_threshold
        self.disk_threshold = disk_threshold

    async def run(self, interval_seconds: int = 300):
        """Runs the monitoring checks at a specified interval."""
        logger.info("System Health Monitor started.")
        while True:
            # Run synchronous checks in a non-blocking way
            await self.check_health()
            await asyncio.sleep(interval_seconds)
            
    async def check_health(self):
        """Wrapper for running all synchronous health checks."""
        try:
            # CPU Check
            cpu_usage = psutil.cpu_percent(interval=1)
            logger.info(f"System Health - CPU Usage: {cpu_usage}%")
            if cpu_usage > self.cpu_threshold:
                await send_system_alert(f"CPU usage is critical: {cpu_usage}%", "CRITICAL")

            # Memory Check
            mem = psutil.virtual_memory()
            mem_usage = mem.percent
            logger.info(f"System Health - Memory Usage: {mem_usage}%")
            if mem_usage > self.mem_threshold:
                await send_system_alert(f"Memory usage is critical: {mem_usage}%", "CRITICAL")

            # Disk Check
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            logger.info(f"System Health - Disk Usage: {disk_usage}%")
            if disk_usage > self.disk_threshold:
                await send_system_alert(f"Disk space is critical: {disk_usage}% full", "CRITICAL")
        except Exception as e:
            logger.error(f"Error during system health check: {e}", exc_info=True)

```python