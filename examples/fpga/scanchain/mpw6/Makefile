include ../../Makefile.in

rtl/Flist.clb rtl/Flist.top: $(PICKLED_CTX)

rtl/tile_clb.pickled.v: rtl/Flist.clb
	cat $$(cat $<) > $@
	sed -i "/^\`include/d" $@

rtl/top.pickled.v: rtl/Flist.top
	cat $$(cat $<) > $@
	sed -i "/^\`include/d" $@

pickled: rtl/tile_clb.pickled.v rtl/top.pickled.v
