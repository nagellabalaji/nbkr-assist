import os

# Render sets PORT dynamically (defaults to 10000)
port = os.environ.get("PORT", "10000")
bind = f"0.0.0.0:{port}"

# Concurrency & timeout settings optimized for Render
workers = int(os.environ.get("WEB_CONCURRENCY", 2))
threads = 4
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")
