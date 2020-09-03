# ============================================================================
# -- Set-up ------------------------------------------------------------------
# ============================================================================
FPGA_DIR := $(shell pwd)/../../../fpga/system/pktchain_axilite_32x32N8K6
TOPLEVEL_LANG := verilog
MODULE := test_ureg
TESTSUITE ?= system
SIM ?= vcs

BUDDY_DIR := $(shell pwd)/../system_pktchain_axilite_32x32N8K6
BITSTREAM := sha256_ureg.memh

$(BUDDY_DIR)/$(BITSTREAM):
	$(MAKE) -C $(BUDDY_DIR) bitgen

$(BITSTREAM): $(BUDDY_DIR)/$(BITSTREAM)
	cp $< $@

CUSTOM_SIM_DEPS := $(BITSTREAM)

# -- Select Test-Suite -------------------------------------------------------
ifeq ($(TESTSUITE),system)

TOPLEVEL = prga_system
TESTCASE = full_system
VERILOG_SOURCES = $(FPGA_DIR)/rtl/*.v

else ifeq ($(TESTSUITE),app)

TOPLEVEL = app
TESTCASE = uprot
VERILOG_SOURCES = $(shell pwd)/src/app.v
VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_sysintf.v
VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_ctrl.v
VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_sax.v
VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_uprot.v
VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_mprot.v
VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_ecc_parity.v
VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_clkdiv.v
VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_async_fifo.v
VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_byteaddressable_reg.v
VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_fifo.v
VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_fifo_lookahead_buffer.v
VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_fifo_resizer.v
VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_fifo_adapter.v
VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_ram_1r1w.v
VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_ram_1r1w_dc.v
VERILOG_SOURCES += $(shell pwd)/../testbench/sha256_ureg.v
VERILOG_SOURCES += $(shell pwd)/../sha256/src/rtl/sha256_core.v
VERILOG_SOURCES += $(shell pwd)/../sha256/src/rtl/sha256_k_constants.v
VERILOG_SOURCES += $(shell pwd)/../sha256/src/rtl/sha256_w_mem.v

else

$(error "Unknown testsuite: $(TESTSUITE)")

endif

# -- Select Simulator --------------------------------------------------------
ifeq ($(SIM),vcs)

COMPILE_ARGS = +incdir+$(FPGA_DIR)/rtl/include +lint=all +warn=all
EXTRA_ARGS = +vcs+loopdetect +vcs+loopreport

else

COMPILE_ARGS = -I$(FPGA_DIR)/rtl/include

endif

# ============================================================================
# -- Cocotb ------------------------------------------------------------------
# ============================================================================
COCOTB_SHARE_DIR := $(shell cocotb-config --share)
COCOTB_PY_DIR := $(shell cocotb-config --prefix)

export COCOTB_SHARE_DIR
export COCOTB_PY_DIR

# include $(shell cocotb-config --makefiles)/Makefile.inc
include $(shell cocotb-config --makefiles)/Makefile.sim

.DEFAULT_GOAL := sim
