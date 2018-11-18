# My Kernel Char Driver

obj-m += mydriver.o

KERNELSRC=/lib/modules/$(shell uname -r)
INSTALL_MOD_PATH=$(KERNELSRC)/build
KERNELMAKEMAINARG=$(INSTALL_MOD_PATH) M=$(PWD)

all:
	make -C $(KERNELMAKEMAINARG) modules

clean:
	make -C $(KERNELMAKEMAINARG) clean
