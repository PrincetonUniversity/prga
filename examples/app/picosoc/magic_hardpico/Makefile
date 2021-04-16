COMP ?= vcs
CONFIG := config/config.${COMP}.yaml
CONFIG_POSTPROCESS := config/config.yaml
PROJECTS := app tests

$(PROJECTS): $(CONFIG_POSTPROCESS)
	python -O -m prga.tools.wizard $<

$(CONFIG_POSTPROCESS): $(CONFIG)
	s=`yosys-config --datdir` && sed "s/%YOSYS_DATDIR%/$${s//\//\\/}/g" $< > $@

clean:
	rm -rf $(PROJECTS) $(CONFIG_POSTPROCESS)
