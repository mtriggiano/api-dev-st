import psutil
import time
from datetime import datetime
from zoneinfo import ZoneInfo

ARGENTINA_TIMEZONE = 'America/Argentina/Buenos_Aires'
ARGENTINA_TZ = ZoneInfo(ARGENTINA_TIMEZONE)

class SystemMonitor:
    """Monitor del sistema para obtener métricas en tiempo real"""
    
    def __init__(self):
        self._last_net_io = None
        self._last_net_time = None
    
    def get_cpu_info(self):
        """Obtiene información de CPU"""
        return {
            'percent': round(psutil.cpu_percent(interval=1), 2),
            'count': psutil.cpu_count(),
            'count_logical': psutil.cpu_count(logical=True),
            'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            'per_cpu': [round(x, 2) for x in psutil.cpu_percent(interval=1, percpu=True)]
        }
    
    def get_memory_info(self):
        """Obtiene información de memoria RAM"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'total_gb': round(mem.total / (1024**3), 2),
            'available_gb': round(mem.available / (1024**3), 2),
            'used_gb': round(mem.used / (1024**3), 2),
            'percent': round(mem.percent, 2),
            'swap_total_gb': round(swap.total / (1024**3), 2),
            'swap_used_gb': round(swap.used / (1024**3), 2),
            'swap_percent': round(swap.percent, 2)
        }
    
    def get_disk_info(self):
        """Obtiene información de discos"""
        partitions = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total_gb': round(usage.total / (1024**3), 2),
                    'used_gb': round(usage.used / (1024**3), 2),
                    'free_gb': round(usage.free / (1024**3), 2),
                    'percent': round(usage.percent, 2)
                })
            except PermissionError:
                continue
        
        return partitions
    
    def get_network_info(self):
        """Obtiene información de red con velocidad actual"""
        net_io = psutil.net_io_counters()
        current_time = time.time()
        
        result = {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'mb_sent': round(net_io.bytes_sent / (1024**2), 2),
            'mb_recv': round(net_io.bytes_recv / (1024**2), 2),
            'speed_mbps_sent': 0,
            'speed_mbps_recv': 0
        }
        
        # Calcular velocidad si tenemos medición anterior
        if self._last_net_io and self._last_net_time:
            time_delta = current_time - self._last_net_time
            if time_delta > 0:
                bytes_sent_delta = net_io.bytes_sent - self._last_net_io.bytes_sent
                bytes_recv_delta = net_io.bytes_recv - self._last_net_io.bytes_recv
                
                result['speed_mbps_sent'] = round((bytes_sent_delta / time_delta) / (1024**2), 2)
                result['speed_mbps_recv'] = round((bytes_recv_delta / time_delta) / (1024**2), 2)
        
        self._last_net_io = net_io
        self._last_net_time = current_time
        
        return result
    
    def get_system_info(self):
        """Obtiene información general del sistema"""
        import platform
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime_seconds = (datetime.now() - boot_time).total_seconds()
        server_now = datetime.now(ARGENTINA_TZ)
        uname = platform.uname()
        
        return {
            'hostname': uname.node,
            'platform': uname.system,
            'platform_release': uname.release,
            'platform_version': uname.version,
            'architecture': uname.machine,
            'boot_time': boot_time.isoformat(),
            'server_datetime': server_now.isoformat(),
            'server_timezone': ARGENTINA_TIMEZONE,
            'uptime_seconds': int(uptime_seconds),
            'uptime_formatted': self._format_uptime(uptime_seconds)
        }
    
    def _format_uptime(self, seconds):
        """Formatea el uptime en formato legible"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        
        return " ".join(parts) if parts else "< 1m"
    
    def get_all_metrics(self):
        """Obtiene todas las métricas del sistema"""
        current_time = datetime.now(ARGENTINA_TZ)
        return {
            'timestamp': current_time.isoformat(),
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info(),
            'disk': self.get_disk_info(),
            'network': self.get_network_info(),
            'system': self.get_system_info()
        }
