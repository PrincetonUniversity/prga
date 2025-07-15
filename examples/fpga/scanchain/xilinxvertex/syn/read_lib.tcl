# get the path to the current dir
set generic_script_root [file dirname [file normalize [info script]]]

# bring yosys commands into our script!
yosys -import

# read techmap libraries
read_verilog -lib [file join $generic_script_root m_xor2.lib.v]
read_verilog -lib [file join $generic_script_root m_adder.lib.v]
read_verilog -lib [file join $generic_script_root m_mux2.lib.v]
read_verilog -lib [file join $generic_script_root m_dffe.lib.v]
