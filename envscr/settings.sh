function find_binary() {
    binary="$1"
    shift
    /usr/bin/env $binary -h 2>&1 >/dev/null
    if [ "$?" != 0 ]; then
        echo "[Error] Binary not found: $binary"
        echo $@
        return 1
    fi
    return 0
}

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/.. >/dev/null && pwd )"
CWD=$PWD
cd $DIR/envscr

echo "[INFO] Checking the presence of Python Interpreter"
find_binary python "Check out Python from https://www.python.org/"
retval=$?
if [ "$retval" != 0 ]; then return $retval 2>/dev/null; exit $retval; fi

echo "[INFO] Checking the presence of PIP"
python -m pip 2>&1 >/dev/null
retval=$?
if [ "$?" != 0 ]; then
    echo "[Error] Python module not found: pip"
    echo "Checkout PIP from: https://pypi.org/project/pip/"
    return $retval 2>/dev/null
    exit $retval
fi

echo "[INFO] Checking if prga.py is installed"
python -c "from __future__ import absolute_import; import prga" 2>&1 >/dev/null
retval=$?
if [ "$retval" != 0 ]; then
    echo "[INFO] Installing prga.py"
    python -m pip install -e $DIR/prga.py --user
fi

echo "[INFO] Checking the presence of VPR"
find_binary vpr "Check out VPR from " \
    "https://github.com/verilog-to-routing/vtr-verilog-to-routing, " \
    "compile it and find 'vpr' under \$VTR_ROOT/vpr/"
retval=$?
if [ "$retval" != 0 ]; then return $retval 2>/dev/null; exit $retval; fi

echo "[INFO] Checking the presence of VPR utility: genfasm"
find_binary genfasm "Check out VPR from " \
    "https://github.com/verilog-to-routing/vtr-verilog-to-routing, " \
    "compile it and find 'genfasm' under \$VTR_ROOT/build/utils/fasm/"
retval=$?
if [ "$retval" != 0 ]; then return $retval 2>/dev/null; exit $retval; fi

echo "[INFO] Checking the presence of yosys"
find_binary yosys "Check out Yosys from " \
    "http://www.clifford.at/yosys/, compile and install it"
retval=$?
if [ "$retval" != 0 ]; then return $retval 2>/dev/null; exit $retval; fi

rm vpr_stdout.log
cd $CWD

echo "[INFO] Environmental setup succeeded!"
