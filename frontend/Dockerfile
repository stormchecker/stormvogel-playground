# Use an official Node.js runtime as a parent image
FROM node:18-alpine

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the Svelte application
RUN npm run build

# Expose the port the app runs on
EXPOSE 80

# Serve the application using a simple web server
RUN npm install -g serve
CMD ["serve", "-s", "public", "-l", "80"]
