# only run when it's never run before
if [ ! -z ${PRGA_SETTINGS_DONE} ]; then
    echo "prga.settings already sourced."
else
    # get the directory of this script
    DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/.. >/dev/null && pwd )"

    export PYTHONPATH=$DIR/prga-builder
    export PATH=$VTR_ROOT/vpr:$DIR/bin:$PATH
fi
