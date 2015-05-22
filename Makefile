include Makefile.$(shell hostname -s)

SOURES := $(wildcard src/*.cpp)
HEADERS := $(wildcard include/*.h)
OBJECTS := $(SOURES:.cpp=.o)

RUN := zlp-stitch

CFLAGS := -I${TCLAP}/include -I${CFITSIO}/include -Iinclude
LDFLAGS := -L${CFITSIO}/lib -lcfitsio
COMMON := -g -Wall -Wextra -O2 -std=c++11 -pthread

all: $(RUN)

$(RUN): $(OBJECTS)
	$(CXX) $^ -o $@ $(LDFLAGS) $(COMMON)

%.o: %.cpp $(HEADERS) Makefile
	$(CXX) -c $< -o $@ $(CFLAGS) $(COMMON)

.PHONY: clean

clean:
	rm -f src/*.o $(RUN)
