FROM node:20-alpine

WORKDIR /workspace

# Copy configurations and install dependencies
COPY package.json ./
RUN npm install

# Copy source code files
COPY . .

# Expose Vite default server port
EXPOSE 5173

# Start development server
CMD ["npm", "run", "dev"]
