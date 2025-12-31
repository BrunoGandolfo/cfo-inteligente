# Etapa 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar package files primero (para cache)
COPY package*.json ./
RUN npm ci

# Copiar código y buildear
COPY . .

# ARG para recibir la URL de la API en build time
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Etapa 2: Producción con Nginx
FROM nginx:alpine

# Copiar build
COPY --from=builder /app/dist /usr/share/nginx/html

# Copiar config de nginx para SPA (redirigir todo a index.html)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
