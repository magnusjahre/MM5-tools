
#include "traceparse.hh"

using namespace std;

#define BUFFER_SIZE 512

int main(int argc, char** argv){
    
    if(argc != 6){
        cout << "Usage: traceparse sharedfilename alonefilename outfile statsfile statskey\n";
        exit(0);
    }
    
    cout << "\nParsing trace files, input:\n";
    
    char* sharedfile = argv[1];
    char* alonefile = argv[2];
    char* outfile = argv[3];
    char* statsfile = argv[4];
    char* statskey = argv[5];
    
    cout << "Shared file:   " << sharedfile << "\n";
    cout << "Alone file:    " << alonefile << "\n";
    cout << "Output file:   " << outfile << "\n";
    cout << "Stats file:    " << statsfile<< "\n";
    cout << "Stats key:     " << statskey << "\n\n";
    
    cout << "Parsing file " << sharedfile << "...\n";
    readTrace(sharedfile, true);
    
    cout << "Done!\nParsing " << alonefile << "...\n";
    readTrace(alonefile, false);
    
    cout << "Done!\nComputing interference...\n";
    int reqs = computeInterference(statsfile, statskey);
    
    cout << "Done!\nWriting output file...\n";
    writeInterferenceFile(outfile, reqs);
    cout << "Done!\n";
    
    return 0;
}

void readTrace(char* filename, bool shared){
    
    char buffer[BUFFER_SIZE];
    
    bool first = true;
    ifstream tracefile(filename);
    assert(tracefile.good());
    while(!tracefile.getline(buffer, BUFFER_SIZE).eof())
    {
        if(first){
            first = false;
            continue;
        }
        
        Latencies lats(buffer);
        if(shared) sharedLatencies[lats.address].push_back(lats);
        else aloneLatencies[lats.address].push_back(lats);
    }
    
    tracefile.close();
}


int computeInterference(char* statsfile, char* statskey){
    
    // remove all adresses that do not occur in both
    std::map<Addr, std::list<Latencies> >::iterator sharedIt = sharedLatencies.begin();
    int erasedFromShared = 0;
    while(sharedIt != sharedLatencies.end()){
        std::map<Addr, std::list<Latencies> >::iterator tmpIt = aloneLatencies.find(sharedIt->first);
        if(tmpIt != aloneLatencies.end()){
            sharedIt++;
        }
        else{
            erasedFromShared += sharedIt->second.size();
            std::map<Addr, std::list<Latencies> >::iterator eraseIt = sharedIt;
            sharedIt++;
            sharedLatencies.erase(eraseIt);
        }
    }
    cout << "Erased " << erasedFromShared << " elements from shared\n";
    
    std::map<Addr, std::list<Latencies> >::iterator aloneIt = aloneLatencies.begin();
    int erasedFromAlone = 0;
    while(aloneIt != aloneLatencies.end()){
        std::map<Addr, std::list<Latencies> >::iterator tmpIt = sharedLatencies.find(aloneIt->first);
        if(tmpIt != sharedLatencies.end()){
            aloneIt++;
        }
        else{
            erasedFromAlone += aloneIt->second.size();
            std::map<Addr, std::list<Latencies> >::iterator eraseIt = aloneIt;
            aloneIt++;
            aloneLatencies.erase(eraseIt);
        }
    }
    cout << "Erased " << erasedFromAlone << " elements from alone\n";
    
    sharedIt = sharedLatencies.begin();
    aloneIt = aloneLatencies.begin();
    int sharedElementsErased = 0;
    int aloneElementsErased = 0;
    int addrsLeft = 0;
    int sharedElementsLeft = 0;
    int aloneElementsLeft = 0;
    for( ; sharedIt != sharedLatencies.end() && aloneIt != aloneLatencies.end() ; sharedIt++,aloneIt++){
        assert(sharedIt->first == aloneIt->first);
        
        addrsLeft++;
        
        if(sharedIt->second.size() > aloneIt->second.size()){
            list<Latencies>::iterator tmpIt = sharedIt->second.begin();
            unsigned int pos = 0;
            for( ; tmpIt != sharedIt->second.end(); pos++){
                if(pos >= aloneIt->second.size()){
                    tmpIt = sharedIt->second.erase(tmpIt);
                    sharedElementsErased++;
                }
                else{
                    tmpIt++;
                }
            }
        }
        else if(sharedIt->second.size() < aloneIt->second.size()){
            list<Latencies>::iterator tmpIt = aloneIt->second.begin();
            unsigned int pos = 0;
            for( ; tmpIt != aloneIt->second.end(); pos++){
                if(pos >= sharedIt->second.size()){
                    tmpIt = aloneIt->second.erase(tmpIt);
                    aloneElementsErased++;
                }
                else{
                    tmpIt++;
                }
            }
        }
        
        sharedElementsLeft += sharedIt->second.size();
        aloneElementsLeft += aloneIt->second.size();
        
        assert(sharedIt->second.size() == aloneIt->second.size());
    }
    
    cout << "Erased " << sharedElementsErased << " shared elements and " << aloneElementsErased << " alone elements due to different request counts for one address\n";
    cout << sharedElementsLeft << " shared elements left and " << aloneElementsLeft << " alone elements left\n";
    cout << addrsLeft << " addresses left after pruning\n";

    int w = 60;
    ofstream stats(statsfile, ios_base::app);
    stats << setw(w);
    stats << statskey;
    stats << setw(w);
    stats << erasedFromShared;
    stats << setw(w);
    stats << erasedFromAlone;
    stats << setw(w);
    stats << sharedElementsErased;
    stats << setw(w);
    stats << aloneElementsErased;
    stats << setw(w);
    stats << sharedElementsLeft;
    stats << setw(w);
    stats << aloneElementsLeft;
    stats << setw(w);
    stats << addrsLeft;
    stats << "\n";
    stats.flush();
    stats.close();
    
    sharedIt = sharedLatencies.begin();
    aloneIt = aloneLatencies.begin();

    for( ; sharedIt != sharedLatencies.end(); sharedIt++,aloneIt++){
      list<Latencies>::iterator sharedListIt = sharedIt->second.begin();
      list<Latencies>::iterator aloneListIt = aloneIt->second.begin();
      
      assert(sharedIt->first == aloneIt->first);
      assert(interference.find(sharedIt->first) == interference.end());
      
      for( ; sharedListIt != sharedIt->second.end() ; sharedListIt++,aloneListIt++){
	interference[sharedIt->first].push_back(Latencies(*sharedListIt,*aloneListIt));
      }
      assert(aloneListIt == aloneIt->second.end());
    }
    assert(aloneIt == aloneLatencies.end());

    assert(sharedElementsLeft == aloneElementsLeft);
    return sharedElementsLeft;
}

void writeInterferenceFile(char* filename, int numReqs){
    
  map<int,Latencies> reqsPerInterferenceVal;

  std::map<Addr, std::list<Latencies> >::iterator intIt = interference.begin();
  for( ; intIt != interference.end(); intIt++){
    list<Latencies>::iterator intListIt = intIt->second.begin();
    for( ; intListIt != intIt->second.end() ; intListIt++){
      intListIt->updateIntMap(reqsPerInterferenceVal);
    }
  }

  int w = 20;
  ofstream intFile(filename);
  intFile << setw(w);
  intFile << "# Interference";
  intFile << setw(w);
  intFile << "IC Entry";
  intFile << setw(w);
  intFile << "IC Transfer";
  intFile << setw(w);
  intFile << "IC Delivery";
  intFile << setw(w);
  intFile << "Bus Entry";
  intFile << setw(w);
  intFile << "Bus Transfer";
  intFile << setw(w);
  intFile << "Cache Capacity";
  intFile << "\n";

  map<int,Latencies>::iterator mapIt =  reqsPerInterferenceVal.begin();
  for( ; mapIt != reqsPerInterferenceVal.end() ; mapIt++){

//     InterferenceFactors tmpFac(mapIt->second, numReqs, mapIt->first);
    InterferenceFactors tmpFac(mapIt->second);

    intFile << setw(w);
    intFile << mapIt->first;
    intFile << setw(w);
    intFile << tmpFac.ic_entry;
    intFile << setw(w);
    intFile << tmpFac.ic_transfer;
    intFile << setw(w);
    intFile << tmpFac.ic_delivery;
    intFile << setw(w);
    intFile << tmpFac.bus_entry;
    intFile << setw(w);
    intFile << tmpFac.bus_transfer;
    intFile << setw(w);
    intFile << tmpFac.cache_capacity;
    intFile << "\n";
  }

  intFile.flush();
  intFile.close();
}

Latencies::Latencies(){
 address = 0;
 at_tick = 0;
 ic_entry = 0;
 ic_transfer = 0;
 ic_delivery = 0;
 bus_entry = 0;
 bus_transfer = 0;
 cache_capacity = 0;
}
   

Latencies::Latencies(char* line){
    
    int pos = 0;
    int bufferpos = 0;
    char buffer[BUFFER_SIZE];
    int addrBufferPos = 0;
    Addr addrBuffer[8];
    
    while(line[pos] != '\0'){
        switch(line[pos]){
            case ';':{
                buffer[bufferpos] = '\0';
                bufferpos = 0;
                addrBuffer[addrBufferPos] = toAddr(buffer);
                addrBufferPos++;
                break;
            }
            case ' ':{
                // ignore spaces
                break;
            }
            default:{
                buffer[bufferpos] = line[pos];
                bufferpos++;
                break;
            }
        }
        pos++;
        assert(pos < BUFFER_SIZE);
    }
    
    buffer[bufferpos] = '\0';
    addrBuffer[addrBufferPos] = toAddr(buffer);
    
    at_tick = addrBuffer[0];
    address = addrBuffer[1];
    ic_entry = addrBuffer[3];
    ic_transfer = addrBuffer[4];
    ic_delivery = addrBuffer[5];
    bus_entry = addrBuffer[6];
    bus_transfer = addrBuffer[7];
    cache_capacity = 0;
}

Latencies::Latencies(Latencies& shared, Latencies& alone){
  at_tick = 0;
  address = shared.address;
  
  ic_entry = shared.ic_entry - alone.ic_entry;
  ic_transfer = shared.ic_transfer - alone.ic_transfer;
  ic_delivery = shared.ic_delivery - alone.ic_delivery;

  if(shared.bus_transfer != 0 && alone.bus_transfer == 0){
    // cache capacity interference
    cache_capacity = shared.bus_transfer + shared.bus_entry;
    bus_entry = 0;
    bus_transfer = 0;
  }
  else if(shared.bus_transfer != 0 && alone.bus_transfer != 0){
    // cache miss in both
    cache_capacity = 0;
    bus_entry = shared.bus_entry - alone.bus_entry;
    bus_transfer = shared.bus_transfer - alone.bus_transfer;
  }
  else if(shared.bus_transfer == 0 && alone.bus_transfer != 0){
    cache_capacity = -(alone.bus_transfer + alone.bus_entry);
    bus_entry = 0;
    bus_transfer = 0;
  }
  else{
    cache_capacity = 0;
    bus_entry = 0;
    bus_transfer = 0;
  }
}

std::string Latencies::toString(){
    stringstream ss;
    ss << "Tick:           " << at_tick << "\n";
    ss << "Address:        " << address << "\n";
    ss << "IC entry:       " << ic_entry << "\n";
    ss << "IC trans:       " << ic_transfer << "\n";
    ss << "IC delivery:    " << ic_delivery << "\n";
    ss << "Bus entry:      " << bus_entry << "\n";
    ss << "Bus Trans:      " << bus_transfer << "\n";
    ss << "Cache capacity: " << cache_capacity << "\n";
    
    return ss.str();
    
}

Addr Latencies::toAddr(char* number){
    Addr outAddr = 0;
    for(int pos = 0;number[pos] != '\0';outAddr *= 10,outAddr += number[pos]-'0',pos++);
    return outAddr;
}

void Latencies::updateIntMap(std::map<int,Latencies>& map){
  addValue(IC_ENTRY, ic_entry, map);
  addValue(IC_TRANSFER, ic_transfer, map);
  addValue(IC_DELIVERY, ic_delivery, map);
  addValue(BUS_ENTRY, bus_entry, map);
  addValue(BUS_TRANSFER, bus_transfer, map);
  addValue(CACHE_CAPACITY, cache_capacity, map);
}

void Latencies::addValue(I_TYPE type, int interferenceValue, std::map<int,Latencies>& map){
  if(map.find(interferenceValue) == map.end()){
    map[interferenceValue] = Latencies();
  }

  switch(type){
  case IC_ENTRY:
    map[interferenceValue].ic_entry += 1;
    break;
  case IC_TRANSFER:
    map[interferenceValue].ic_transfer += 1;
    break;
  case IC_DELIVERY:
    map[interferenceValue].ic_delivery += 1;
    break;
  case BUS_ENTRY:
    map[interferenceValue].bus_entry += 1;
    break;
  case BUS_TRANSFER:
    map[interferenceValue].bus_transfer += 1;
    break;
  case CACHE_CAPACITY:
    map[interferenceValue].cache_capacity += 1;
    break;
  default:
    assert(false);
  }
}

// InterferenceFactors::InterferenceFactors(Latencies lat, int numReqs, int intVal){
//   ic_entry       = computeIntFactor(lat.ic_entry, numReqs, intVal);
//   ic_transfer    = computeIntFactor(lat.ic_transfer, numReqs, intVal);
//   ic_delivery    = computeIntFactor(lat.ic_delivery, numReqs, intVal);
//   bus_entry      = computeIntFactor(lat.bus_entry, numReqs, intVal);
//   bus_transfer   = computeIntFactor(lat.bus_transfer, numReqs, intVal);
//   cache_capacity = computeIntFactor(lat.cache_capacity, numReqs, intVal);
// }

InterferenceFactors::InterferenceFactors(Latencies lat){
    ic_entry       = lat.ic_entry;
    ic_transfer    = lat.ic_transfer;
    ic_delivery    = lat.ic_delivery;
    bus_entry      = lat.bus_entry;
    bus_transfer   = lat.bus_transfer;
    cache_capacity = lat.cache_capacity;
}
