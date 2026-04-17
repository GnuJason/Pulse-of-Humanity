bind = "0.0.0.0:10000"
workers = 1  # Single worker to prevent state conflicts
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
worker_class = "sync"


def post_fork(server, worker):
	from app import bootstrap_population_system

	bootstrap_population_system()