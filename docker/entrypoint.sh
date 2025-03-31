#!/bin/sh
echo "Applying migrations"
until alembic -x run_seeds=true upgrade head
do
  echo "Waiting for applying migrations..."
  sleep 2
done
exec "$@"
