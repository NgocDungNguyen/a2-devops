# Stage 1: Build Vue application
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build production frontend
RUN npm run build


# Stage 2: Serve with Nginx
FROM nginx:alpine

# Delete default Nginx content
RUN rm -rf /usr/share/nginx/html/*

# Copy built Vue files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy our Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
