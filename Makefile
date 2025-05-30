# Makefile for Advanced StegoTool project

.PHONY: help install test run run-enhanced clean lint format check-deps demo

# Default target
help:
	@echo "🔐 Advanced StegoTool - Available Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install       Install dependencies"
	@echo "  make check-deps    Check if dependencies are installed"
	@echo ""
	@echo "Running Applications:"
	@echo "  make run           Run basic Streamlit app"
	@echo "  make run-enhanced  Run enhanced Streamlit app (recommended)"
	@echo ""
	@echo "Development & Testing:"
	@echo "  make test          Run all tests"
	@echo "  make test-image    Run image steganography tests"
	@echo "  make test-audio    Run audio steganography tests"
	@echo "  make test-video    Run video steganography tests"
	@echo "  make test-utils    Run utility tests"
	@echo "  make lint          Run linting (flake8)"
	@echo "  make format        Format code (black)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Clean temporary files and cache"
	@echo ""
	@echo "Demo & Examples:"
	@echo "  make demo          Run demo with sample data"

# Installation
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Installation complete!"

check-deps:
	@echo "🔍 Checking dependencies..."
	@python -c "import streamlit, cv2, numpy, cryptography, scipy; print('✅ All dependencies are installed!')"

# Running applications
run:
	@echo "🚀 Starting basic StegoTool..."
	streamlit run app.py

run-enhanced:
	@echo "🚀 Starting enhanced StegoTool..."
	streamlit run app_enhanced.py

# Testing
test:
	@echo "🧪 Running all tests..."
	python run_tests.py

test-image:
	@echo "🖼️  Running image steganography tests..."
	python run_tests.py image

test-audio:
	@echo "🎵 Running audio steganography tests..."
	python run_tests.py audio

test-video:
	@echo "🎬 Running video steganography tests..."
	python run_tests.py video

test-utils:
	@echo "⚙️  Running utility tests..."
	python run_tests.py utils

# Code quality
lint:
	@echo "🔍 Running linter..."
	flake8 steganography/ tests/ *.py --exclude=__pycache__,temp*

format:
	@echo "🎨 Formatting code..."
	black steganography/ tests/ *.py

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf temp/ temp_dev/ temp_test/ 2>/dev/null || true
	rm -rf .coverage htmlcov/ 2>/dev/null || true
	@echo "✅ Cleanup complete!"

# Demo
demo:
	@echo "🎬 Running demo..."
	@echo "This will create sample images, audio, and video files for testing"
	python -c "
import numpy as np
import cv2
from scipy.io import wavfile
import os

# Create demo directory
os.makedirs('demo_image/input', exist_ok=True)

# Create sample image
img = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
cv2.imwrite('demo_image/input/sample.png', img)

# Create sample audio
sample_rate = 44100
duration = 5.0
t = np.linspace(0, duration, int(sample_rate * duration))
audio = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
wavfile.write('demo_image/input/sample.wav', sample_rate, audio)

# Create sample video
width, height = 640, 480
fps = 24
frames = 120  # 5 seconds at 24fps

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('demo_image/input/sample.mp4', fourcc, fps, (width, height))

if out.isOpened():
    for i in range(frames):
        # Create a frame with moving colors
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :, 0] = (i * 255 // frames) % 256  # Blue
        frame[:, :, 1] = ((i + 40) * 255 // frames) % 256  # Green
        frame[:, :, 2] = ((i + 80) * 255 // frames) % 256  # Red
        out.write(frame)
    out.release()

print('✅ Demo files created in demo_image/input/')
print('  - sample.png (512x512 image)')
print('  - sample.wav (5 second audio)')
print('  - sample.mp4 (5 second video)')
"

# Development workflow
dev-setup: install
	@echo "🛠️  Setting up development environment..."
	pip install pytest pytest-cov black flake8
	@echo "✅ Development setup complete!"

dev-test: format lint test
	@echo "✅ Development check complete!"

# Quick start
quick-start: install demo run-enhanced

# Help for specific targets
install-help:
	@echo "📦 Install target:"
	@echo "  Installs all required Python packages from requirements.txt"

test-help:
	@echo "🧪 Test targets:"
	@echo "  test        - Run all test suites"
	@echo "  test-image  - Test image steganography functions"
	@echo "  test-audio  - Test audio steganography functions"
	@echo "  test-video  - Test video steganography functions"
	@echo "  test-utils  - Test utility and encryption functions" 