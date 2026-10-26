FROM node:20-alpine
WORKDIR /workspace/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
EXPOSE 5173
