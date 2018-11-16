CC=gcc
CFLAGS=-I.

mydriver.o: mydriver.c
	$(CC) -c mydriver.c

mydriver: mydriver.o
	$(CC) -o mydriver mydriver.o


clean:
	rm -rf *.o
	rm -rf mydriver
