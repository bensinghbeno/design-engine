obj-m += messagedriver.o

KERNEL_VERSION=$(shell uname -r)
KERNEL_SRC_DIR=/lib/modules/$(KERNEL_VERSION)

app:	myapp.c
	gcc -c myapp.c
	gcc -o myapp.out myapp.o

	
module:
	make -C $(KERNEL_SRC_DIR)/build M=$(PWD) modules

clean:
	make -C $(KERNEL_SRC_DIR)/build M=$(PWD) clean
	rm *.out

deploymodule:
	-sudo rmmod messagedriver
	sudo dmesg -C
	sudo insmod messagedriver.ko
	-sudo rm '/dev/messagedriver'
	sudo mknod /dev/messagedriver c 240 0 -m 777
	dmesg
