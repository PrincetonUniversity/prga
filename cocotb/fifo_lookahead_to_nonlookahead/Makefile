SIM = icarus
TOPLEVEL_LANG = verilog

VERILOG_SOURCES = $(PWD)/fifo_wrapper.v $(PWD)/fifo.v $(PWD)/ram_1r1w.v $(PWD)/fifo_lookahead_buffer.v
# TOPLEVEL is the name of the toplevel module in the Verilog or VHDL file_
TOPLEVEL=fifo_wrapper
# MODULE is the name of the python testfile
MODULE=fifo_cocotb

include $(shell cocotb-config --makefiles)/Makefile.inc
include $(shell cocotb-config --makefiles)/Makefile.sim