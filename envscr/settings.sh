function find_binary() {
    binary="$1"
    shift
    $binary -h 2>&1 >/dev/null
    if [ "$?" != 0 ]; then
        echo "[Error] Binary not found: $binary"
        echo $@
        return 1
    fi
    return 0
}

find_binary vpr "Check out VPR from " \
    "https://github.com/verilog-to-routing/vtr-verilog-to-routing, " \
    "compile it and find 'vpr' under \$VTR_ROOT/vpr/"
if [ "$?" != 0 ]; then exit 1; fi

find_binary genfasm "Check out VPR from " \
    "https://github.com/verilog-to-routing/vtr-verilog-to-routing, " \
    "compile it and find 'genfasm' under \$VTR_ROOT/build/utils/fasm/"
if [ "$?" != 0 ]; then exit 1; fi

find_binary "yosys" "Check out Yosys from " \
    "http://www.clifford.at/yosys/, compile and install it"
if [ "$?" != 0 ]; then exit 1; fi

rm vpr_stdout.log

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/.. >/dev/null && pwd )"
export PRGA_ROOT=$DIR
if [[ ":$PYTHONPATH:" != *":$DIR/prga.py:"* ]]; then
    export PYTHONPATH="$DIR/prga.py${PYTHONPATH:+":$PYTHONPATH"}"
fi
