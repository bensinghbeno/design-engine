obj-m += messagedriver.o

KERNEL_VERSION=$(shell uname -r)
KERNEL_SRC_DIR=/lib/modules/$(KERNEL_VERSION)


all:
	make -C $(KERNEL_SRC_DIR)/build M=$(PWD) modules

clean:
	make -C $(KERNEL_SRC_DIR)/build M=$(PWD) clean

test:
	-sudo rmmod messagedriver
	sudo dmesg -C
	sudo insmod messagedriver.ko
	dmesg
