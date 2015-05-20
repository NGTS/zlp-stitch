SOURES := $(wildcard src/*.cpp)
HEADERS := $(wildcard include/*.h)
OBJECTS := $(SOURES:.cpp=.o)

RUN := zlp-stitch

CXX := icpc
CFLAGS := -I/usr/local/tclap/include
LDFLAGS :=
COMMON := -g -Wall -Wextra -O0 -std=c++11

all: $(RUN)

$(RUN): $(OBJECTS)
	$(CXX) $< -o $@ $(LDFLAGS) $(COMMON)

%.o: %.cpp
	$(CXX) -c $< -o $@ $(CFLAGS) $(COMMON)
