SRC_DIR := ../src

TARGET_DESIGN := gate
PRGA_SCRIPT := $(SRC_DIR)/build.py
VERILOG_SRC := $(SRC_DIR)/$(TARGET_DESIGN).v
TESTBENCH_SRC := $(SRC_DIR)/$(TARGET_DESIGN).tb.v
POST_SYNTHESIS_TB_SRC := $(SRC_DIR)/$(TARGET_DESIGN).psyn.tb.sv
IMPLEMENTATION_SRC := $(SRC_DIR)/$(TARGET_DESIGN).impl.v
YOSYS_SCRIPT := $(SRC_DIR)/synth.ys
VPR_IOBINDING := $(SRC_DIR)/io.pads
FIX_IO_SCRIPT := $(SRC_DIR)/fix_io.py

YOSYS_BLIF := $(TARGET_DESIGN).blif

VPR_ARCHDEF := archdef.vpr.xml
VPR_RRGRAPH := rrgraph.vpr.xml
VPR_CONFIGDB := config.pb
VPR_PACK := $(TARGET_DESIGN).net
VPR_PACK_FIXED := $(TARGET_DESIGN).fixed.net
VPR_PLACE := $(TARGET_DESIGN).place
VPR_ROUTE := $(TARGET_DESIGN).route
ARCH_WIDTH := 4
ARCH_HEIGHT := 4
VPR_CHAN_WIDTH := 4
POST_SYNTHESIS_SRC := $(TARGET_DESIGN)_post_synthesis.v
POST_SYNTHESIS_SDF := $(TARGET_DESIGN)_post_synthesis.sdf

# COMP := vcs
# FLAGS := -full64

COMP := iverilog
FLAGS := -g2005 -gspecify

LOGIC_SIM := lsim
LOGIC_SIM_WAVEFORM := $(LOGIC_SIM).vcd
LOGIC_SIM_LOG = $(LOGIC_SIM).log
POST_SYNTHESIS_SIM := psim
POST_SYNTHESIS_SIM_WAVEFORM := $(POST_SYNTHESIS_SIM).vcd
POST_SYNTHESIS_SIM_LOG = $(POST_SYNTHESIS_SIM).log
IMPLEMENTATION_SIM := isim
IMPLEMENTATION_SIM_WAVEFORM := $(IMPLEMENTATION_SIM).vcd
IMPLEMENTATION_SIM_LOG := $(IMPLEMENTATION_SIM).log

BITSTREAM_MEMH := $(TARGET_DESIGN).memh
FPGA_FILES := $(VPR_ARCHDEF) $(VPR_RRGRAPH) $(VPR_CONFIGDB)
VPR_PNR := $(VPR_PLACE) $(VPR_ROUTE)
POST_SYNTHESIS_FILES := $(POST_SYNTHESIS_SRC) $(POST_SYNTHESIS_SDF)

.PHONY: default
default: verify

fpga: $(FPGA_FILES)

synth: $(YOSYS_BLIF)

pnr: $(VPR_PNR)

bitstream: $(BITSTREAM_MEMH)

verify: $(LOGIC_SIM_LOG) $(IMPLEMENTATION_SIM_LOG)

waveform: $(LOGIC_SIM_WAVEFORM) $(IMPLEMENTATION_SIM_WAVEFORM)

disp: $(VPR_PNR)
	vpr $(VPR_ARCHDEF) $(YOSYS_BLIF) --net_file $(VPR_PACK_FIXED) \
		--place_file $(VPR_PLACE) \
		--route_file $(VPR_ROUTE) --route_chan_width $(VPR_CHAN_WIDTH) --read_rr_graph $(VPR_RRGRAPH) \
		--analysis --disp on

clean:
	rm -rf $(FPGA_FILES) $(YOSYS_BLIF) rtl $(VPR_PACK) $(VPR_PACK_FIXED) $(VPR_PNR) *.rpt *.log
	rm -rf $(LOGIC_SIM) $(IMPLEMENTATION_SIM) $(POST_SYNTHESIS_SIM) *.vcd *.log
	rm -rf *.rpt *.log csrc *.daidir *.memh ucli.key *_post_synthesis.* DVEfiles *.vpd *.tcl

$(FPGA_FILES): $(PRGA_SCRIPT)
	python $^

$(YOSYS_BLIF): $(VERILOG_SRC) $(YOSYS_SCRIPT)
	yosys -o $@ $^

$(VPR_PACK): $(VPR_ARCHDEF) $(YOSYS_BLIF)
	vpr $^ --pack --constant_net_method route

$(VPR_PACK_FIXED): $(VPR_PACK)
	python $(FIX_IO_SCRIPT) -x $(ARCH_WIDTH) -y $(ARCH_HEIGHT) -b $(VPR_IOBINDING) -i $< -o $@

$(VPR_PNR): $(VPR_ARCHDEF) $(YOSYS_BLIF) $(VPR_RRGRAPH) $(VPR_PACK_FIXED) $(VPR_IOBINDING)
	vpr $(VPR_ARCHDEF) $(YOSYS_BLIF) --net_file $(VPR_PACK_FIXED) \
		--place --fix_pins $(VPR_IOBINDING) \
		--route --route_chan_width $(VPR_CHAN_WIDTH) --read_rr_graph $(VPR_RRGRAPH)

$(BITSTREAM_MEMH): $(YOSYS_BLIF) $(VPR_CONFIGDB) $(VPR_PACK_FIXED) $(VPR_PNR)
	prga-bitgen-bitchain -c $(VPR_CONFIGDB) -b $(YOSYS_BLIF) -n $(VPR_PACK_FIXED) -p $(VPR_PLACE) -r $(VPR_ROUTE) \
		--output_memh=$@ --verbose=trace

$(POST_SYNTHESIS_FILES): $(VPR_PNR)
	vpr $(VPR_ARCHDEF) $(YOSYS_BLIF) --net_file $(VPR_PACK_FIXED) \
		--place_file $(VPR_PLACE) \
		--route_file $(VPR_ROUTE) --route_chan_width $(VPR_CHAN_WIDTH) --read_rr_graph $(VPR_RRGRAPH) \
		--analysis --gen_post_synthesis_netlist on

$(LOGIC_SIM): $(TESTBENCH_SRC) $(VERILOG_SRC)
	$(COMP) $(FLAGS) -o $@ $< -v $(VERILOG_SRC)

$(POST_SYNTHESIS_SIM): $(POST_SYNTHESIS_TB_SRC) $(POST_SYNTHESIS_SRC)
	$(COMP) $(FLAGS) -o $@ $< -v $(POST_SYNTHESIS_SRC) \
		-v /tigress/angl/vtr/vtr_flow/primitives.v

$(IMPLEMENTATION_SIM): $(TESTBENCH_SRC) $(IMPLEMENTATION_SRC) fpga
	$(COMP) $(FLAGS) -o $@ $< -v $(IMPLEMENTATION_SRC) $(addprefix -v ,$(wildcard rtl/*.v))

$(LOGIC_SIM_LOG): $(LOGIC_SIM)
	./$< | tee $@
	grep "all tests passed" $@ || (echo "logic simulation failed"; exit 1)

$(POST_SYNTHESIS_SIM_LOG): $(POST_SYNTHESIS_SIM) $(POST_SYNTHESIS_SDF)
	./$< +sdf=$(POST_SYNTHESIS_SDF) | tee $@
	grep "all tests passed" $@ || (echo "post synthesis simulation failed"; exit 1)

$(IMPLEMENTATION_SIM_LOG): $(IMPLEMENTATION_SIM) $(BITSTREAM_MEMH)
	./$< +bitstream_memh=$(BITSTREAM_MEMH) +max_cycle=50000 | tee $@
	grep "all tests passed" $@ || (echo "implementation simulation failed"; exit 1)

$(LOGIC_SIM_WAVEFORM): $(LOGIC_SIM)
	./$< +dump=$@

$(POST_SYNTHESIS_SIM_WAVEFORM): $(POST_SYNTHESIS_SIM) $(POST_SYNTHESIS_SDF)
	./$< +dump=$@ +sdf=$(POST_SYNTHESIS_SDF)

$(IMPLEMENTATION_SIM_WAVEFORM): $(IMPLEMENTATION_SIM) $(BITSTREAM_MEMH)
	./$< +bitstream_memh=$(BITSTREAM_MEMH) +max_cycle=50000 +dump=$@
