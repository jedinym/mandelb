CFLAGS += -Wall -Wextra -std=c99
all: mandelb.so

lib/mandelb.o: mandelb.c
	cc $(CFLAGS) -c mandelb.c -o lib/mandelb.o

mandelb.so: lib/mandelb.o
	cc $(CFLAGS) -fPIC -shared -o lib/mandelb.so lib/mandelb.o
