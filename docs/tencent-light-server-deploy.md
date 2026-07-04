# Tencent Cloud Lightweight Server Deploy Notes

This public website is a static artifact. Deploy `docs/` only.

Do not expose the local portal backend:

- `portal/backend` and FastAPI port `5174` are for local skill management on `127.0.0.1`.
- `portal/frontend` and Vite port `5173` are for local portal UI development on `127.0.0.1`.
- The public site reads generated JSON from `docs/data/` and graph images from `docs/assets/`.

## Build Locally

```bash
bin/deploy-docs
```

The command must finish with:

- `docs/data/skills.json`
- `docs/data/domains.json`
- `docs/data/problem-workflows.json`
- `docs/assets/skills-graph.png`
- `state audit drift=false`

## One-command Publish

Preview the exact file changes first:

```bash
bin/deploy-tencent-static --target tencent:/var/www/skills-manager/ --dry-run
```

Apply the publish after the preview looks correct:

```bash
bin/deploy-tencent-static --target tencent:/var/www/skills-manager/ --apply
```

The script rebuilds `docs/`, runs the publish state audit, then syncs `docs/` with `rsync -avz --delete`.
It excludes build-only sources and runtime caches such as `docs/_src/`, `docs/superpowers/`, `__pycache__/`, and `*.pyc`.

## Manual Upload

```bash
rsync -av --delete docs/ tencent:/var/www/skills-manager/
```

## Nginx Example

```nginx
server {
    listen 80;
    server_name skills.example.com;

    root /var/www/skills-manager;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /data/ {
        add_header Cache-Control "no-cache";
        try_files $uri =404;
    }

    location /assets/ {
        add_header Cache-Control "public, max-age=86400";
        try_files $uri =404;
    }
}
```

## Smoke Check

```bash
curl -I http://skills.example.com/zh/index.html
curl -I http://skills.example.com/data/skills.json
curl -I http://skills.example.com/assets/skills-graph.png
```

Expected: all return `200`.
