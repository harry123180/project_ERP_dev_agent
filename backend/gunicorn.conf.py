import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 2

# Logging
accesslog = '/app/logs/access.log'
errorlog = '/app/logs/error.log'
loglevel = os.getenv('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'erp-backend'

# Server mechanics
daemon = False
pidfile = '/app/erp-backend.pid'
user = None
group = None
tmp_upload_dir = None

# SSL (optional)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Preload application for better performance
preload_app = True

# Enable automatic worker restarts
reload = False
reload_engine = 'auto'
reload_extra_files = []

# StatsD integration (optional)
# statsd_host = 'localhost:8125'
# statsd_prefix = 'erp'
