FROM python:3.12-slim

WORKDIR /app

# Set up python lib
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all of source code
COPY . .

# Group static files
# Set secret key
RUN SECRET_KEY=dummy python manage.py collectstatic --noinput

# Build identity, surfaced at GET /api/version/. Baked into the image (not
# injected at run time) so that during a canary/blue-green rollout each
# container reports the build it is actually running:
#   docker build --build-arg APP_VERSION=1.2.0 --build-arg GIT_COMMIT=$(git rev-parse --short HEAD) ...
ARG APP_VERSION=1.0.0
ARG GIT_COMMIT=unknown
ENV APP_VERSION=${APP_VERSION} \
    GIT_COMMIT=${GIT_COMMIT}

EXPOSE 8000

# start Gunicorn point to config.wsgi
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "config.wsgi:application"]
