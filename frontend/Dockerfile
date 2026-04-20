FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# Vite only inlines NEXT_PUBLIC_* at build time; keep it aligned with
# the VITE_API_URL build arg so Docker Hub builds get the right URL.
ENV NEXT_PUBLIC_API_URL=${VITE_API_URL}

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
