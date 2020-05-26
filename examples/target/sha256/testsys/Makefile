SIM ?= vcs

FPGA_DIR := $(shell pwd)/../../../fpga/system/pktchain_axilite_32x32N8K6

TOPLEVEL_LANG = verilog
# TOPLEVEL = wrap
# VERILOG_SOURCES = $(shell pwd)/wrap.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/backbone.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/pktchain_axilite_intf.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/pktchain_axilite_intf_be_cfg.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/pktchain_axilite_intf_be_uprot.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/pktchain_axilite_intf_fe.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/pktchain_dispatcher.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/pktchain_frame_assemble.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/pktchain_frame_disassemble.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/pktchain_gatherer.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/pktchain_router.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/pktchain_clasp.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_async_fifo.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_byteaddressable_reg.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_fifo.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_fifo_lookahead_buffer.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_fifo_resizer.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_fifo_adapter.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_ram_1r1w.v
# VERILOG_SOURCES += $(FPGA_DIR)/rtl/prga_ram_1r1w_dc.v
TOPLEVEL = prga_system
VERILOG_SOURCES = $(FPGA_DIR)/rtl/*.v
MODULE = test
ifeq ($(SIM),vcs)
COMPILE_ARGS = +incdir+$(FPGA_DIR)/rtl/include +lint=all +warn=all
else
COMPILE_ARGS = -I$(FPGA_DIR)/rtl/include
endif

COCOTB_SHARE_DIR := $(shell cocotb-config --share)
COCOTB_PY_DIR := $(shell cocotb-config --prefix)

export COCOTB_SHARE_DIR
export COCOTB_PY_DIR

include $(shell cocotb-config --makefiles)/Makefile.inc
include $(shell cocotb-config --makefiles)/Makefile.sim
