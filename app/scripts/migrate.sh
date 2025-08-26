#!/usr/bin/env sh
set -e

# нормалізуємо переводи рядків, якщо потрібно
# (не обов'язково на кожен запуск, але не завадить)
# for f in alembic/*.py alembic/versions/*.py; do
#   [ -f "$f" ] && sed -i 's/\r$//' "$f"
# done

# >>> головне: додаємо /app у PYTHONPATH
export PYTHONPATH="/app:${PYTHONPATH}"

CMD="$1"; shift || true

case "$CMD" in
  makemigrations)
    # створити ревізію з автогенерацією
    alembic -c alembic.ini revision --autogenerate -m "$*"
    ;;
  migrate|upgrade)
    alembic -c alembic.ini upgrade head
    ;;
  downgrade)
    alembic -c alembic.ini downgrade -1
    ;;
  history)
    alembic -c alembic.ini history
    ;;
  *)
    echo "Usage: $0 {makemigrations <message>|migrate|upgrade|downgrade|history}"
    exit 1
    ;;
esac
