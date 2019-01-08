PICKLED_CONTEXT := arch.pickled
FPGA_FILES := archdef.vpr.xml rrgraph.vpr.xml config.db $(PICKLED_CONTEXT)
SIM_MAKEFILE := Makefile.sim
SIM_PROJ := $(SIM_MAKEFILE) testbench.v synth.ys
TARGET_SRC := ../gate.v
HOST_SRC := ../gate_host.v
IO_BINDINGS := ../io.pads

.PHONY: default fpga simproj
default: all

fpga: $(FPGA_FILES)

simproj: $(SIM_PROJ)

all: fpga simproj
	make -f $(SIM_MAKEFILE)

clean:
	if [ -f $(SIM_MAKEFILE) ]; then make -f $(SIM_MAKEFILE) clean; fi
	rm -rf $(FPGA_FILES) $(SIM_PROJ) rtl

$(FPGA_FILES): ../build.py
	python $^

$(SIM_PROJ): $(FPGA_FILES)
	python -m prga.tools.simproj $(PICKLED_CONTEXT) $(TARGET_SRC) $(HOST_SRC) $(IO_BINDINGS) \
		-m $(SIM_MAKEFILE)
