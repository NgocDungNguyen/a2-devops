/*
 * RMIT Store — runtime configuration.
 * ---------------------------------------------------------------------------
 * This file is NOT bundled. Vite copies everything in public/ into dist/
 * unchanged and unhashed, so after `npm run build` it sits next to
 * index.html as dist/config.js and can be edited on the server.
 *
 * That is the whole point: the same built artifact deploys to development,
 * staging and production. You never rebuild the frontend to change where the
 * API lives.
 *
 * How you would set it in each deployment:
 *
 *   Single host (client and API behind one nginx)
 *       leave it as "/api" — nginx proxies /api/ to gunicorn, the browser
 *       sees one origin, and CORS never comes up.
 *
 *   Split hosts (client and API on separate EC2 instances)
 *       API_BASE_URL: "http://<api-instance-ip>:8000/api"
 *       and add that client origin to CORS_ALLOWED_ORIGINS on the server.
 *       Working out why this is suddenly necessary is the exercise.
 *
 *   Containers
 *       docker run -v ./config.js:/usr/share/nginx/html/config.js:ro ...
 *
 *   Kubernetes
 *       mount a ConfigMap at /usr/share/nginx/html/config.js, or render this
 *       file from a template with envsubst in the image's entrypoint.
 *
 *   Blue/green
 *       one image, two config files.
 */

window.__APP_CONFIG__ = {
  // Where the API lives, as seen by the *browser*, not by the server.
  API_BASE_URL: '/api'
}
