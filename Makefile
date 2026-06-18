# MemoryAgent Build Makefile

.PHONY: build build-mac build-win clean run dev test install

# Default target
all: build

# Build for current platform
build:
	@echo "Building MemoryAgent..."
	@if [ "$$(uname)" = "Darwin" ]; then \
		$(MAKE) build-mac; \
	else \
		$(MAKE) build-win; \
	fi

# Build DMG for macOS
build-mac:
	@echo "Building MemoryAgent DMG for macOS..."
	python build_dmg.py

# Build ZIP for Windows
build-win:
	@echo "Building MemoryAgent ZIP for Windows..."
	python build_windows.py

# Build with py2app (alternative for macOS)
build-app:
	@echo "Building MemoryAgent.app with py2app..."
	python setup_py2app.py py2app

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build dist *.egg-info *.spec
	rm -rf MemoryAgent.app
	rm -rf dmg_staging
	rm -f *.dmg *.zip
	rm -f MemoryAgent.bat MemoryAgent.ps1 README_WINDOWS.txt

# Run the application
run:
	@echo "Starting MemoryAgent..."
	python src/main.py

# One-command local dev (backend + frontend)
dev:
	@bash scripts/dev.sh

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
	@echo "Please add icon.icns (macOS) or icon.ico (Windows) to assets/ directory"

# Package for distribution
package: build
	@echo "Packaging complete!"
	@ls -lh *.dmg *.zip *.msi 2>/dev/null || echo "No package files found"

# Build MSI for Windows (requires WiX Toolset)
build-msi:
	@echo "Building MSI installer..."
	python build_msi.py

# Create GitHub Release
release:
	@echo "Creating GitHub Release..."
	./create_release.sh
