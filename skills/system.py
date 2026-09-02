import psutil
import time
import shutil
import os

start_time = time.time()

def get_telemetry() -> dict:
    cpu_usage = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    disk = shutil.disk_usage("/")

    uptime_seconds = int(time.time() - start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"

    processes = []
    procs_to_sample = []
    try:
        for proc in psutil.process_iter():
            try:
                proc.cpu_percent(interval=None)
                procs_to_sample.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception:
        pass

    time.sleep(0.1)

    for proc in procs_to_sample:
        try:
            processes.append({
                'pid': proc.pid,
                'name': proc.name(),
                'cpu_percent': proc.cpu_percent(interval=None),
                'memory_percent': proc.memory_percent()
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Sort processes by CPU percentage
    top_cpu_processes = sorted(processes, key=lambda p: p.get('cpu_percent') or 0, reverse=True)[:5]

    return {
        "cpu_percent": cpu_usage,
        "memory_percent": memory.percent,
        "memory_used_gb": round(memory.used / (1024**3), 2),
        "memory_total_gb": round(memory.total / (1024**3), 2),
        "disk_percent": round((disk.used / disk.total) * 100, 1),
        "disk_free_gb": round(disk.free / (1024**3), 2),
        "uptime": uptime_str,
        "top_processes": top_cpu_processes
    }

def get_system_status_summary() -> dict:
    telemetry = get_telemetry()
    spoken = f"CPU usage is currently {int(telemetry['cpu_percent'])} percent. RAM usage is at {int(telemetry['memory_percent'])} percent."
    return {
        "success": True,
        "telemetry": telemetry,
        "spoken_response": spoken
    }

def get_top_cpu_app() -> dict:
    telemetry = get_telemetry()
    top_proc = telemetry["top_processes"][0] if telemetry["top_processes"] else {"name": "Unknown", "cpu_percent": 0}
    proc_name = top_proc.get('name', 'Unknown process')
    cpu_p = top_proc.get('cpu_percent', 0)
    spoken = f"{proc_name} is using the most CPU at {cpu_p} percent."
    return {
        "success": True,
        "process": top_proc,
        "spoken_response": spoken
    }
