SIM = icarus
TOPLEVEL_LANG = verilog

VERILOG_SOURCES = $(PWD)/fifo.v $(PWD)/ram_1r1w.v
# TOPLEVEL is the name of the toplevel module in the Verilog or VHDL file_
TOPLEVEL=fifo
# MODULE is the name of the python testfile
MODULE=fifo_cocotb

include $(shell cocotb-config --makefiles)/Makefile.inc
include $(shell cocotb-config --makefiles)/Makefile.sim