dbusinterface: sources/dbusinterface.c headers/dbusinterface.h
	gcc  -I./headers/ -I/usr/include/dbus-1.0/  -I /usr/lib/x86_64-linux-gnu/dbus-1.0/include/ -I /usr/include/glib-2.0/ -I /usr/lib/x86_64-linux-gnu/glib-2.0/include/ -c -Wall -Werror -fpic sources/dbusinterface.c
	mv dbusinterface.o bin/dbusinterface.o

ldbusinterface: dbusinterface
	gcc -shared -o libs/libdbusinterface.so bin/dbusinterface.o

utils: sources/utils.c headers/utils.h
	gcc -D_C_UTIL -I./headers/ -c -Wall -Werror -fpic sources/utils.c
	mv utils.o bin/utils.o

lutils: utils
	gcc -shared -o libs/utils.so bin/utils.o

serverdbusapplication: sources/serverdbusapplication.c ldbusinterface lutils
	LD_LIBRARY_PATH=. gcc -I./sources/ -I./headers/ -I/usr/include/dbus-1.0/  -I /usr/lib/x86_64-linux-gnu/dbus-1.0/include/ -I /usr/include/glib-2.0/ -I /usr/lib/x86_64-linux-gnu/glib-2.0/include/ -L./libs/ -Wall -o bin/serverdbusapplication.out sources/serverdbusapplication.c sources/dbusinterface.c -ldbus-1 -ldbusinterface -lutils

clientdbusapplication: sources/clientdbusapplication.c ldbusinterface
	LD_LIBRARY_PATH=. gcc -I./sources/ -I./headers/ -I/usr/include/dbus-1.0/  -I /usr/lib/x86_64-linux-gnu/dbus-1.0/include/ -I /usr/include/glib-2.0/ -I /usr/lib/x86_64-linux-gnu/glib-2.0/include/ -L./libs/ -Wall -o bin/clientdbusapplication.out         sources/clientdbusapplication.c sources/dbusinterface.c -ldbus-1 -ldbusinterface

all: clientdbusapplication serverdbusapplication


clean: 
	rm -rf bin/*.o bin/*.out libs/*.so
