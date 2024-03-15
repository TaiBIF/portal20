# Frontend Code (ReactJS) Build Process

## Dockerfile

- use [Multi-stage builds | Docker Docs](https://docs.docker.com/build/building/multi-stage/)
- copy minified javascript file from build stage (node:18-alpine) to final stage (python3.10-slim-buster), folder: `/frontend`

## docker compose up script
- copy '/frontend/*' to static/js
