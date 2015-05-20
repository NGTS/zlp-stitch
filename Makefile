SOURES := $(wildcard src/*.cpp)
HEADERS := $(wildcard include/*.h)
OBJECTS := $(SOURES:.cpp=.o)

RUN := zlp-stitch

CXX := icpc
CFLAGS := -I/usr/local/tclap/include -I/usr/local/cfitsio/include -Iinclude
LDFLAGS := -L/usr/local/cfitsio/lib -lcfitsio
COMMON := -g -Wall -Wextra -O0 -std=c++11 -pthread

all: $(RUN)

$(RUN): $(OBJECTS)
	$(CXX) $^ -o $@ $(LDFLAGS) $(COMMON)

%.o: %.cpp
	$(CXX) -c $< -o $@ $(CFLAGS) $(COMMON)
