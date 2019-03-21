FPGA_FILES := arch.vpr.xml rrg.vpr.xml config.db ctx.pickled

.PHONY: all
all: $(FPGA_FILES)

$(FPGA_FILES): build.py
	python $<

.PHONY: clean
clean:
	rm -rf $(FPGA_FILES) rtl
