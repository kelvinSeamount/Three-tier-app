# Stage 1: BUILD stage — compile the React app
# "builder" is a temporary container just for building.
# Think of it as a prep kitchen that never serves customers.
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# Build the production React app (creates /app/dist)
RUN npm run build

# Stage 2: SERVE stage — serve with Nginx
# We throw away the builder and only keep the compiled output.
# Result: a much smaller final image (no node_modules bloat).
FROM nginx:alpine

# Copy our custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the compiled React app from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
