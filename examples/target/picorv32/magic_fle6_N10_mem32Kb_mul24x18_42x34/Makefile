CONFIG := config/config.yaml
PROJECTS := design tests

$(PROJECTS): $(CONFIG)
	python -O -m prga.tools.wizard $<

clean:
	rm -rf $(PROJECTS)
