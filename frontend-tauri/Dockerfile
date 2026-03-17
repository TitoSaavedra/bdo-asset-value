FROM node:20-alpine AS build

WORKDIR /app

COPY frontend-tauri/package.json frontend-tauri/pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile --prod=false

COPY frontend-tauri/ ./
RUN pnpm build

FROM nginx:1.27-alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY frontend-tauri/nginx/default.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80