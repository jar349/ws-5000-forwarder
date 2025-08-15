# gunicorn.conf.py
worker_class = "gthread"
workers = 2
threads = 4
bind = "0.0.0.0:8000"
timeout = 30
graceful_timeout = 15
keepalive = 15
accesslog = "-"
errorlog = "-"

