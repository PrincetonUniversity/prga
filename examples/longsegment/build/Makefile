PICKLED_CONTEXT := ctx.pickled
FPGA_FILES := archdef.vpr.xml rrgraph.vpr.xml config.db $(PICKLED_CONTEXT)
SIM_MAKEFILE := Makefile.sim
SIM_PROJ := $(SIM_MAKEFILE) testbench.v synth.ys
TARGET_SRC := ../bcd2bin.v
HOST_SRC := ../bcd2bin_host.v
IO_BINDINGS := ../io.pads

.PHONY: all fpga simproj
default: all

all: $(FPGA_FILES) $(SIM_PROJ)
	make -f $(SIM_MAKEFILE)

fpga: $(FPGA_FILES)

simproj: $(SIM_PROJ)

clean:
	if [ -f $(SIM_MAKEFILE) ]; then make -f $(SIM_MAKEFILE) clean; fi
	rm -rf $(FPGA_FILES) $(SIM_PROJ) rtl

$(FPGA_FILES): ../build.py
	python $^

$(SIM_PROJ): $(FPGA_FILES)
	python -m prga.tools.simproj $(PICKLED_CONTEXT) $(TARGET_SRC) $(HOST_SRC) $(IO_BINDINGS) \
		-m $(SIM_MAKEFILE)
