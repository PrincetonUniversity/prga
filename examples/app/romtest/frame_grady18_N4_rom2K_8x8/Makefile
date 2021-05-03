COMP ?= vcs
CONFIG := config/config.${COMP}.yaml
PROJECTS := app tests

$(PROJECTS): $(CONFIG)
	python -O -m prga.tools.wizard $<

clean:
	rm -rf $(PROJECTS)
