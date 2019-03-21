FPGA_DIR := ../../../fpga/naive/naive_L2
PICKLED_CONTEXT := $(FPGA_DIR)/ctx.pickled
FPGA_FILES := $(addprefix $(FPGA_DIR)/,arch.vpr.xml rrg.vpr.xml config.db) $(PICKLED_CONTEXT)
SIM_MAKEFILE := Makefile.sim
SIM_PROJ := $(SIM_MAKEFILE) testbench.v synth.ys
TARGET_SRCS := ../gate.v
HOST_SRCS := ../gate_host.v
IO_BINDINGS := io.pads

.PHONY: all simproj
all: $(SIM_PROJ)
	make -f $(SIM_MAKEFILE)

simproj: $(SIM_PROJ)

clean:
	if [ -f $(SIM_MAKEFILE) ]; then make -f $(SIM_MAKEFILE) clean; fi
	rm -rf $(SIM_PROJ)

$(FPGA_FILES):
	make -C $(FPGA_DIR)

$(SIM_PROJ): $(FPGA_FILES)
	python -m prga.tools.simproj -a $(PICKLED_CONTEXT) -v $(TARGET_SRCS) -x $(HOST_SRCS) -b $(IO_BINDINGS) \
		-m $(SIM_MAKEFILE) --fpga_prefix $(FPGA_DIR)

%:
	if [ -f $(SIM_MAKEFILE) ]; then make -f $(SIM_MAKEFILE) $@; \
		else echo "make: *** No rule to make target '$@'.  Stop." && exit 1; fi
