#!/bin/bash

echo "Starting MikroTik Billing System Frontend..."

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start the frontend
echo "Starting frontend development server..."
echo "Dashboard will open at http://localhost:3000"
npm start
