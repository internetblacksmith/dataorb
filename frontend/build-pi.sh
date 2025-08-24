#!/bin/bash
# Lightweight build script for Raspberry Pi with limited RAM

echo "Building frontend for Pi with memory constraints..."

# Set memory limits
export NODE_OPTIONS="--max-old-space-size=768"

# Disable source maps to save memory
export GENERATE_SOURCEMAP=false

# Build with minimal optimization
export INLINE_RUNTIME_CHUNK=false
export IMAGE_INLINE_SIZE_LIMIT=0

# Clear any previous builds
rm -rf build/

# Build
npm run build

echo "Build complete!"