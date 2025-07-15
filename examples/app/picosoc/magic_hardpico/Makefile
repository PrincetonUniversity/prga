SHELL := /bin/bash

COMP ?= vcs
CONFIG := config/config.${COMP}.yaml
CONFIG_POSTPROCESS := config/config.yaml
PROJECTS := app tests

$(PROJECTS): $(CONFIG_POSTPROCESS)
	python -O -m prga.tools.wizard $<

$(CONFIG_POSTPROCESS): $(CONFIG)
	
s=yosys-config --datdir && bash -c 'sed "s/%YOSYS_DATDIR%/${1//\//\\/}/g" config/config.vcs.yaml > config/config.yaml' bash "$s"


clean:
	rm -rf $(PROJECTS) $(CONFIG_POSTPROCESS)
