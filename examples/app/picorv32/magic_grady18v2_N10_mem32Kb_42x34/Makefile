COMPILER ?= ivl
CONFIG := config/config.${COMPILER}.yaml
PROJECTS := app tests

$(PROJECTS): $(CONFIG)
	python -O -m prga.tools.wizard $<

clean:
	rm -rf $(PROJECTS)
