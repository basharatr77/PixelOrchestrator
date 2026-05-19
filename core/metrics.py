from prometheus_client import Counter, Gauge, Histogram, start_http_server
import time

# Define metrics
job_success = Counter('device_job_success_total', 'Successful jobs', ['job_type'])
job_failure = Counter('device_job_failure_total', 'Failed jobs', ['job_type'])
job_duration = Histogram('device_job_duration_seconds', 'Job duration', ['job_type'])
active_devices = Gauge('device_active_devices', 'Number of connected devices')
queue_depth = Gauge('device_job_queue_depth', 'Current job queue depth')
reconciliation_cycles = Counter('device_reconciliation_cycles_total', 'Number of reconciliation cycles')

def start_metrics_server(port=9090):
    start_http_server(port)
    print(f"Prometheus metrics available at http://localhost:{port}/metrics")
