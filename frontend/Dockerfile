# State 1: Build the react app
FROM node:20-bullseye AS build

WORKDIR /app

#  Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps

# Copy source code
COPY . .

# Inject vite env variables
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build the app
RUN npm run build

# Stage 2: Serve the app with Nginx
FROM nginx:alpine

# Copy built files from Stage 1
COPY --from=build /app/dist/public /usr/share/nginx/html

# Copy custom nginx config if exist (optional)
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 5001

CMD ["nginx", "-g", "daemon off;"]