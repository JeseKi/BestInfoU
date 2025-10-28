FROM node:23-alpine AS builder
WORKDIR /app

COPY package.json pnpm-lock.yaml* ./
RUN npm install -g pnpm
RUN pnpm install
COPY . .
COPY .env .
RUN pnpm run build

FROM python:3.10-slim
WORKDIR /app
COPY .env .
COPY requirements.txt .
RUN pip install uv
RUN uv pip install --no-cache-dir -r requirements.txt --system

COPY src/server/ ./src/server/
COPY --from=builder /app/dist ./dist

EXPOSE 8000
CMD ["python", "run.py"]