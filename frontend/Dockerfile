# ─────────────────────────────────────────────────────────────────────────────
# AlphaSync — Frontend Dockerfile (React + Vite)
# Build: docker build -t alphasync-frontend ./frontend
# ─────────────────────────────────────────────────────────────────────────────

# ── Estágio 1: build ──────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Instala dependências
COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile

# Copia código e faz build
COPY . .

# Aceita a URL da API em build-time (pode ser sobrescrita por variável)
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build


# ── Estágio 2: servidor estático (nginx) ──────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Remove config padrão do nginx
RUN rm /etc/nginx/conf.d/default.conf

# Config específica para SPA (React Router)
COPY --from=builder /app/dist /usr/share/nginx/html

RUN printf 'server {\n\
    listen 80;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
    location /health {\n\
        return 200 "ok";\n\
        add_header Content-Type text/plain;\n\
    }\n\
    gzip on;\n\
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml image/svg+xml;\n\
    gzip_min_length 1000;\n\
}\n' > /etc/nginx/conf.d/frontend.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s \
    CMD wget -qO- http://localhost/health || exit 1
