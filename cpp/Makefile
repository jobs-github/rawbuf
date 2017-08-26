CXX =   g++
CXXFLAGS =	-O0 -g3 -Wall -fmessage-length=0
LINK =	$(CXX)

TARGET = bin/rawbuf

OBJS = bin/main.o \
    bin/perf_test.o \
    bin/sample_test.o \
	bin/rawbuf.o

INCS = -I include

DEPS = 

$(TARGET):	$(OBJS)

	$(LINK) -o $(TARGET) $(OBJS)

bin/main.o:	$(DEPS) src/main.cpp
	$(CXX) -c $(CXXFLAGS)  $(INCS) -o bin/main.o src/main.cpp

bin/perf_test.o:	$(DEPS) src/perf_test.cpp
	$(CXX) -c $(CXXFLAGS)  $(INCS) -o bin/perf_test.o src/perf_test.cpp

bin/sample_test.o:	$(DEPS) src/sample_test.cpp
	$(CXX) -c $(CXXFLAGS)  $(INCS) -o bin/sample_test.o src/sample_test.cpp

RAWBUF = include/rawbuf.cpp
bin/rawbuf.o:	$(DEPS) $(RAWBUF)
	$(CXX) -c $(CXXFLAGS)  $(INCS) -o bin/rawbuf.o $(RAWBUF)

all:	$(TARGET)

clean:
	rm -f $(OBJS) $(TARGET)