# ---- LedgerIQ frontend (build → static, served by nginx) ----

# Stage 1: build the SPA
FROM node:20-alpine AS build
WORKDIR /app

# In the dockerized stack the browser calls the API same-origin via the
# reverse proxy, so the API base is a relative path.
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: serve the built assets
FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
