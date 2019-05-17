
all: run

run:
	uwsgi --socket 0.0.0.0:8050 --protocol=http -w wsgi:app
