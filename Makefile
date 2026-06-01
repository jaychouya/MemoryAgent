# MemoryAgent Build Makefile

.PHONY: build clean run test

# Default target
all: build

# Build DMG
build:
	@echo "Building MemoryAgent DMG..."
	python build_dmg.py

# Build with py2app (alternative)
build-app:
	@echo "Building MemoryAgent.app with py2app..."
	python setup_py2app.py py2app

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build dist *.egg-info *.spec
	rm -rf MemoryAgent.app
	rm -rf dmg_staging
	rm -f *.dmg

# Run the application
run:
	@echo "Starting MemoryAgent..."
	python src/main.py

# Run tests
test:
	@echo "Running tests..."
	python -m pytest tests/ -v

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	pip install py2app pyinstaller

# Create assets directory
assets:
	@echo "Creating assets directory..."
	mkdir -p assets
	@echo "Please add icon.icns to assets/ directory"

# Package for distribution
package: build
	@echo "Packaging complete!"
	@ls -lh *.dmg 2>/dev/null || echo "No DMG file found"
