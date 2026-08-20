FROM node:20-alpine

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --silent

COPY frontend/ ./

# NEXT_PUBLIC_* values are inlined into the client bundle at build time, not
# read at runtime. Without this build arg the image would ship hardcoded
# http://localhost:8000 and the deployed frontend could never reach the API.
ARG NEXT_PUBLIC_API_BASE=http://localhost:8000
ARG NEXT_PUBLIC_APP_ENV=production
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE \
    NEXT_PUBLIC_APP_ENV=$NEXT_PUBLIC_APP_ENV

RUN npm run build

USER node

EXPOSE 3000

CMD ["npm", "run", "start"]
