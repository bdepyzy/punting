# Poker Bot Makefile
# Compiler and flags
CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2
LDFLAGS = -lX11 -ltesseract -lleptonica

# Directories
SRC_DIR = src
INCLUDE_DIR = include
BUILD_DIR = build
BIN_DIR = bin
ASSETS_DIR = assets

# Source files
MAIN_SOURCES = $(SRC_DIR)/main.cpp
TESS_SOURCES = $(SRC_DIR)/tess.cpp
MAIN_OBJECTS = $(MAIN_SOURCES:$(SRC_DIR)/%.cpp=$(BUILD_DIR)/%.o)
TESS_OBJECTS = $(TESS_SOURCES:$(SRC_DIR)/%.cpp=$(BUILD_DIR)/%.o)
CAPTURE_TARGET = $(BIN_DIR)/capture
OCR_TARGET = $(BIN_DIR)/ocr

# Default target
all: $(CAPTURE_TARGET) $(OCR_TARGET)

# Create directories if they don't exist
$(BUILD_DIR) $(BIN_DIR):
	mkdir -p $@

# Link the capture executable
$(CAPTURE_TARGET): $(MAIN_OBJECTS) | $(BIN_DIR)
	$(CXX) $(MAIN_OBJECTS) -o $@ -lX11

# Link the OCR executable
$(OCR_TARGET): $(TESS_OBJECTS) | $(BIN_DIR)
	$(CXX) $(TESS_OBJECTS) -o $@ -ltesseract -lleptonica

# Compile source files to object files
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -I$(INCLUDE_DIR) -c $< -o $@

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR) $(BIN_DIR)
	rm -f *.png *.jpg *.jpeg

# Clean everything including generated images
clean-all: clean
	rm -f $(ASSETS_DIR)/images/*.png $(ASSETS_DIR)/images/*.jpg

# Run capture then OCR
run: $(CAPTURE_TARGET) $(OCR_TARGET)
	cd $(BIN_DIR) && ./capture && ./ocr

# Run only capture
capture: $(CAPTURE_TARGET)
	cd $(BIN_DIR) && ./capture

# Run only OCR
ocr: $(OCR_TARGET)
	cd $(BIN_DIR) && ./ocr

# Debug build
debug: CXXFLAGS += -g -DDEBUG
debug: $(CAPTURE_TARGET) $(OCR_TARGET)

# Install dependencies (example for Ubuntu/Debian)
install-deps:
	sudo apt-get update
	sudo apt-get install -y libx11-dev build-essential libtesseract-dev libleptonica-dev

# Create a release build
release: CXXFLAGS += -DNDEBUG
release: clean $(CAPTURE_TARGET) $(OCR_TARGET)

# Display help
help:
	@echo "Available targets:"
	@echo "  all         - Build both capture and OCR programs (default)"
	@echo "  clean       - Remove build artifacts"
	@echo "  clean-all   - Remove build artifacts and generated images"
	@echo "  run         - Build and run capture then OCR"
	@echo "  capture     - Build and run only the screen capture program"
	@echo "  ocr         - Build and run only the OCR program"
	@echo "  debug       - Build with debug symbols"
	@echo "  release     - Build optimized release version"
	@echo "  install-deps- Install required system dependencies"
	@echo "  help        - Show this help message"

.PHONY: all clean clean-all run capture ocr debug release install-deps help