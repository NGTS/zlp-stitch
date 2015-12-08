include Makefile.$(shell hostname -s)

SOURES := $(wildcard src/*.cpp)
OBJECTS := $(SOURES:.cpp=.o)

RUN := zlp-stitch

CFLAGS := -I${TCLAP}/include -I${CFITSIO}/include -Iinclude
LDFLAGS := -L${CFITSIO}/lib -lcfitsio
COMMON := -g -Wall -Wextra -O2 -std=c++11 -pthread

all: .deps $(RUN)

$(RUN): $(OBJECTS)
	$(CXX) $^ -o $@ $(LDFLAGS) $(COMMON)

%.o: %.cpp
	$(CXX) -c $< -o $@ -MMD -MP -MF .deps/$*.d $(CFLAGS) $(COMMON)

.deps:
	mkdir -p $@/src

-include .deps/src/*.d

.PHONY: clean

clean:
	rm -f src/*.o $(RUN)

.SECONDARY:
.SUFFIXES:
