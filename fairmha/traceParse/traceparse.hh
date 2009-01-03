
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <map>
#include <list>
#include <string>
#include <sstream>
#include <map>
#include <iomanip>

#include <cassert>

typedef unsigned long long Addr;

typedef enum{
  IC_ENTRY,
  IC_TRANSFER,
  IC_DELIVERY,
  BUS_ENTRY,
  BUS_TRANSFER,
  CACHE_CAPACITY
} I_TYPE;

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
    
    Latencies();

    Latencies(char* line);
    Latencies(Latencies& shared, Latencies& alone);
    
    Addr toAddr(char* number);
    
    std::string toString();

    void updateIntMap(std::map<int,Latencies>& map);

    void addValue(I_TYPE type, int interferenceValue, std::map<int,Latencies>& map);
};

struct InterferenceFactors{
  double ic_entry;
  double ic_transfer;
  double ic_delivery;
  double bus_entry;
  double bus_transfer;
  double cache_capacity;

  InterferenceFactors(Latencies lat, int numReqs, int intVal);

  inline double computeIntFactor(int numReqs, int totalReqs, int interference){
    return ((double) interference) * ( ((double) numReqs) / ((double) totalReqs) ); 
  }

};

std::map<Addr, std::list<Latencies> > aloneLatencies;
std::map<Addr, std::list<Latencies> > sharedLatencies;
std::map<Addr, std::list<Latencies> > interference;

int main(int argc, char** argv);

void readTrace(char* filename, bool shared);

int computeInterference();

void writeInterferenceFile(char* filename, int numReqs);
