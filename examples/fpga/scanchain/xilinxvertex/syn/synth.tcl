# get the path to the current dir
set generic_script_root [file dirname [file normalize [info script]]]

# bring yosys commands into our script!
yosys -import

# coarse synthesis
synth -flatten -noalumacc -run coarse

# print coarse synthesis report
stat -width

# memory map
opt -full
memory_map

# print memory map report
stat -width

# techmap onto library cells read with `read_verilog` above
techmap -map [file join $generic_script_root m_xor2.techmap.v]
techmap -map [file join $generic_script_root m_adder.techmap.v]
dffsr2dff; dff2dffe
techmap -map [file join $generic_script_root m_dffe.techmap.v]
opt -full

# print techmap report
stat -width

# LUT map
techmap     ;# generic techmap onto basic logic elements
abc9 -luts 5:5
opt -full

# print LUT map report
stat -width

# post-LUTmap commands
opt -full
clean

# Transforms FF types with clock enable and/or synchronous reset into their base type
dffunmap
 
# print final report
stat -width

# final check
check -noinit