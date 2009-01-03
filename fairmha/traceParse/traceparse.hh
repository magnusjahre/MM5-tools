
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <map>
#include <list>
#include <string>
#include <sstream>
#include <map>

#include <cassert>

typedef unsigned long long Addr;

struct Latencies{
    
  public:
    
    Addr address;
    int at_tick;
    int ic_entry;
    int ic_transfer;
    int ic_delivery;
    int bus_entry;
    int bus_transfer;
    int cache_capacity;
    
    Latencies(char* line);
    
    Addr toAddr(char* number);
    
    std::string toString();
};

std::map<Addr, std::list<Latencies> > aloneLatencies;
std::map<Addr, std::list<Latencies> > sharedLatencies;
std::map<Addr, std::list<Latencies> > interference;

int main(int argc, char** argv);

void readTrace(char* filename, bool shared);

void computeInterference();

void writeInterferenceFile(char* filename);
