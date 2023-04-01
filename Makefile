CC = gcc
BASICFLAGS = -std=gnu11 -Wall -Wextra -Wpedantic
OPTFLAGS = -g
EXFLAGS = -DWITH_GPIB=0
CFLAGS = $(BASICFLAGS) $(OPTFLAGS) $(EXFLAGS)
LDLIBS = -lm

TGTLIST = hp4195util

all: $(TGTLIST)

hp4195util:	hp4195util.c

clean:
	rm -f *.o
	rm -f $(TGTLIST)
