INSTALL_PATH := /usr/local/bin/transcribe
SCRIPT_PATH  := $(abspath transcribe.py)

.PHONY: install uninstall

install:
	@printf '#!/usr/bin/env bash\nexec uv run --script $(SCRIPT_PATH) "$$@"\n' | sudo tee $(INSTALL_PATH) > /dev/null
	sudo chmod +x $(INSTALL_PATH)
	@echo "✓ Installed $(INSTALL_PATH)"

uninstall:
	sudo rm -f $(INSTALL_PATH)
	@echo "✓ Removed $(INSTALL_PATH)"
