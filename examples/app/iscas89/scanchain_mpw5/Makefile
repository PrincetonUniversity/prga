tests=$(basename $(shell ls ../verilog | grep s))
curdir=$(abspath $(dir $(lastword $(MAKEFILE_LIST))))

all: result
	echo "bitgen: $$(grep bitgen $< | wc -l)"
	echo "place: $$(grep place $< | wc -l)"
	echo "pack: $$(grep pack $< | wc -l)"
	echo "syn: $$(grep syn $< | wc -l)"
	echo "fail: $$(grep fail $< | wc -l)"
	
result: $(tests)
	rm -f result
	for t in $(tests); do \
		if [ -f "$$t/app/bitgen.out" ]; then echo "$$t: bitgen" >> result; \
		elif [ -f "$$t/app/place.out" ]; then echo "$$t: place" >> result; \
		elif [ -f "$$t/app/pack.out" ]; then echo "$$t: pack" >> result; \
		elif [ -f "$$t/app/syn.eblif" ]; then echo "$$t: syn" >> result; \
		else echo "$$t: fail" >> result; \
		fi \
	done

$(tests) : % : $(curdir)/../../../fpga/scanchain/mpw5/ctx.pkl $(curdir)/../verilog/%.v
	mkdir -p $@
	touch $@
	d=$$( echo $@ | sed -e "s/[a-z]*$$//" ) \
	  && sed "s/%name%/$$d/" config/config.vcs.tmpl.yaml \
	  | sed -e "s/%file%/$@/" > $@/config.yaml
	cp config/io.partial $@
	cd $@ && python -O -m prga.tools.wizard config.yaml
	-$(MAKE) -C $@/app

clean:
	rm -rf $(tests)
