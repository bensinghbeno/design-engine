CC=gcc -D_C_UTIL -Wl,-rpath,${LIB_RUNTIME_DIR}
LIB_RUNTIME_DIR=../libs/

utils: sources/utils.c headers/utils.h
	$(CC)  -D_C_UTIL -I./headers/ -I/usr/include/dbus-1.0/  -I /usr/lib/x86_64-linux-gnu/dbus-1.0/include/ -I /usr/include/glib-2.0/ -I /usr/lib/x86_64-linux-gnu/glib-2.0/include/ -c -Wall -Werror -fpic sources/utils.c
	mv utils.o bin/utils.o

lutils: utils
	$(CC)  -shared -o libs/libutils.so bin/utils.o

dbusinterface: sources/dbusinterface.c headers/dbusinterface.h 
	$(CC)   -I./headers/ -I/usr/include/dbus-1.0/  -I /usr/lib/x86_64-linux-gnu/dbus-1.0/include/ -I /usr/include/glib-2.0/ -I /usr/lib/x86_64-linux-gnu/glib-2.0/include/ -c -Wall -Werror -fpic sources/dbusinterface.c
	mv dbusinterface.o bin/dbusinterface.o

ldbusinterface: dbusinterface
	$(CC)  -shared -o libs/libdbusinterface.so bin/dbusinterface.o



serverdbusapplication: sources/serverdbusapplication.c ldbusinterface lutils
	$(CC)  -I./sources/ -I./headers/ -I/usr/include/ -I/usr/include/dbus-1.0/  -I /usr/lib/x86_64-linux-gnu/dbus-1.0/include/ -I /usr/include/glib-2.0/ -I /usr/lib/x86_64-linux-gnu/glib-2.0/include/ -L./libs/ -Wall -o bin/serverdbusapplication.out sources/serverdbusapplication.c   -ldbus-1 -L./libs/ -ldbusinterface -L./libs/ -lutils -lpthread 
	

clientdbusapplication: sources/clientdbusapplication.c ldbusinterface lutils
	$(CC)  -I./sources/ -I./headers/ -I/usr/include/dbus-1.0/  -I /usr/lib/x86_64-linux-gnu/dbus-1.0/include/ -I /usr/include/glib-2.0/ -I /usr/lib/x86_64-linux-gnu/glib-2.0/include/ -Wall -o bin/clientdbusapplication.out         sources/clientdbusapplication.c  -ldbus-1 -L./libs/ -ldbusinterface -ldbus-1 -L./libs/ -ldbusinterface -L./libs/ -lutils -lpthread 

all: clientdbusapplication serverdbusapplication
	export LD_LIBRARY_PATH=../libs/

clean: 
	rm -rf bin/*.o bin/*.out libs/*.so
