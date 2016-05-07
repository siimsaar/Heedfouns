# Starts Redis, webserver and application on localhost

redis-server &
gunicorn -k gevent --worker-connections 1000 --timeout 240 --log-level debug -b 192.168.0.11:5000 app:app
