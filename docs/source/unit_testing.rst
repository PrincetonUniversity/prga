************
UNIT TESTING
************
PRGA provides a pass which automatically generate unit tests for the Verilog Modules used in the FPGA Fabric along with a route testing.

The tests use `cocotb <https://cocotb.readthedocs.io/>`_, a framework for testing VHDL/Verilog designs using python.

Requirements
------------
* `Context` object which was used for descibing the FPGA Architecture
* 'RTL' and 'Translation' passes must be executed along with the 'Tester' pass

.. code-block:: python

    from prga import *
    from prga.core.context import Context
    from prga.passes.test import Tester
    ctx = Context.unpickle("ctx.pkl") # Unpickle the Context file

    flow = Flow(
            TranslationPass(),
            VerilogCollection('rtl'),
            Tester('rtl','unit_tests') # 'rtl' is the name of the directory holding the Verilog source files 
            )
    flow.run(ctx, Scanchain.new_renderer())

Example
-------
`PRGA <https://github.com/crusader2000/prga/>`_ repository contains a few examples of custom FPGAs. To check out unit testing, follow these commands

.. code-block:: bash

    cd prga/examples/fpga/tiny/k4_N2_8x8/
    make
    make unit_test

This will create 2 directories 'rtl' and 'unit_tests'
'rtl' contains all the source Verilog files

::

    cbox_tile_clb_e0.v  clb.v               sbox_nw_w_ex_w.v    sw3.v
    cbox_tile_clb_w0.v  cluster.v           sbox_se_e_ex_es.v   sw48.v
    cbox_t_io_e_w0.v    flipflop.v          sbox_se_e_ex_e.v    sw4.v
    cbox_t_io_n_s0.v    include             sbox_se_W_ex_s.v    sw5.v
    cbox_t_io_s_n0.v    iob.v               sbox_se_W.v         sw6.v
    cbox_t_io_w_e0.v    lut4.v              sbox_se_Ww_ex_sw.v  sw7.v
    cfg_data_d16.v      sbox_ne_n_ex_ne.v   sbox_sw_N_ex_w.v    sw8.v
    cfg_data_d1.v       sbox_ne_n_ex_n.v    sbox_sw_Nn_ex_nw.v  sw9.v
    cfg_data_d2.v       sbox_ne_S_ex_e.v    sbox_sw_N.v         tile_clb.v
    cfg_data_d3.v       sbox_ne_Ss_ex_es.v  sbox_sw_s_ex_s.v    t_io_e.v
    cfg_data_d4.v       sbox_ne_S.v         sbox_sw_s_ex_sw.v   t_io_n.v
    cfg_data_d5.v       sbox_nw_Ee_ex_ne.v  subarray.v          t_io_s.v
    cfg_data_d6.v       sbox_nw_E_ex_n.v    sw10.v              t_io_w.v
    cfg_delim.v         sbox_nw_E.v         sw20.v              top.v
    cfg_e_reg.v         sbox_nw_w_ex_nw.v   sw2.v


'unit_tests' contains cocotb tests for individual modules

::

    test_cbox_tile_clb_e0  test_route_1           test_sbox_sw_s_ex_sw
    test_cbox_tile_clb_w0  test_sbox_ne_n_ex_n    test_subarray
    test_cbox_t_io_e_w0    test_sbox_ne_n_ex_ne   test_sw10
    test_cbox_t_io_n_s0    test_sbox_ne_S         test_sw2
    test_cbox_t_io_s_n0    test_sbox_ne_S_ex_e    test_sw20
    test_cbox_t_io_w_e0    test_sbox_ne_Ss_ex_es  test_sw3
    test_cfg_data_d1       test_sbox_nw_E         test_sw4
    test_cfg_data_d16      test_sbox_nw_Ee_ex_ne  test_sw48
    test_cfg_data_d2       test_sbox_nw_E_ex_n    test_sw5
    test_cfg_data_d3       test_sbox_nw_w_ex_nw   test_sw6
    test_cfg_data_d4       test_sbox_nw_w_ex_w    test_sw7
    test_cfg_data_d5       test_sbox_se_e_ex_e    test_sw8
    test_cfg_data_d6       test_sbox_se_e_ex_es   test_sw9
    test_cfg_delim         test_sbox_se_W         test_tile_clb
    test_cfg_e_reg         test_sbox_se_W_ex_s    test_t_io_e
    test_clb               test_sbox_se_Ww_ex_sw  test_t_io_n
    test_cluster           test_sbox_sw_N         test_t_io_s
    test_flipflop          test_sbox_sw_N_ex_w    test_t_io_w
    test_iob               test_sbox_sw_Nn_ex_nw  test_top
    test_lut4              test_sbox_sw_s_ex_s

To run the cocotb tests, cd into any directory and run make.

Example:

.. code-block:: bash

    cd unit_tests/test_cluster
    make

To test routes,  
.. code-block:: bash

    cd unit_tests/test_route_1
    make