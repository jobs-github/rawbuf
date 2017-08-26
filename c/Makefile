CC =   cc
CFLAGS =	-O0 -g3 -Wall -fmessage-length=0
LINK =	$(CC)

TARGET = bin/rawbuf

OBJS = bin/main.o \
    bin/perf_test.o \
    bin/sample_test.o \
    bin/rawbuf.o \
    bin/rawbuf_utils.o

INCS = -I include

DEPS = 

$(TARGET):	$(OBJS)

	$(LINK) -o $(TARGET) $(OBJS)

bin/main.o:	$(DEPS) src/main.c
	$(CC) -c $(CFLAGS) $(INCS) -o bin/main.o src/main.c

bin/perf_test.o:	$(DEPS) src/perf_test.c
	$(CC) -c $(CFLAGS) $(INCS) -o bin/perf_test.o src/perf_test.c

bin/sample_test.o:	$(DEPS) src/sample_test.c
	$(CC) -c $(CFLAGS) $(INCS) -o bin/sample_test.o src/sample_test.c

bin/rawbuf.o:	$(DEPS) include/rawbuf.c
	$(CC) -c $(CFLAGS) $(INCS) -o bin/rawbuf.o include/rawbuf.c

bin/rawbuf_utils.o:	$(DEPS) include/rawbuf_utils.c
	$(CC) -c $(CFLAGS) $(INCS) -o bin/rawbuf_utils.o include/rawbuf_utils.c

all:	$(TARGET)

clean:
	rm -f $(OBJS) $(TARGET)