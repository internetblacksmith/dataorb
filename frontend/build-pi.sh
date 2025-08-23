#!/bin/bash
# Build script optimized for Raspberry Pi with limited memory

echo "Building frontend for Raspberry Pi..."
echo "This may take several minutes on Pi Zero W/2W"

# Set Node options to increase heap size and optimize for low memory
export NODE_OPTIONS="--max-old-space-size=512"

# Clear npm cache to free up memory
npm cache clean --force

# Remove node_modules and reinstall if needed
if [ "$1" = "clean" ]; then
    echo "Performing clean build..."
    rm -rf node_modules
    rm -rf build
    npm install --production=false
fi

# Build with reduced parallelism to save memory
echo "Starting build with memory optimizations..."
npm run build

if [ $? -eq 0 ]; then
    echo "Build successful!"
    echo "Build output in ./build directory"
else
    echo "Build failed. Try running: ./build-pi.sh clean"
    echo "Or increase swap space on your Pi"
fi