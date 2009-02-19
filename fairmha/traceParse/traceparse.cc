
#include "traceparse.hh"

using namespace std;

#define BUFFER_SIZE 512

int main(int argc, char** argv){
    
    if(argc != 6 && argc != 7){
        cout << "Usage: traceparse sharedfilename alonefilename outfile statsfile statskey [interferencefile]\n";
        exit(0);
    }
    
    cout << "\nParsing trace files, input:\n";
    
    char* sharedfile = argv[1];
    char* alonefile = argv[2];
    char* outfile = argv[3];
    char* statsfile = argv[4];
    char* statskey = argv[5];
    char* intEstimateFile = NULL;
    if(argc > 6){
      intEstimateFile = argv[6];
    }
    
    cout << "Shared file:       " << sharedfile << "\n";
    cout << "Alone file:        " << alonefile << "\n";
    cout << "Output file:       " << outfile << "\n";
    cout << "Stats file:        " << statsfile<< "\n";
    cout << "Stats key:         " << statskey << "\n\n";
    if(intEstimateFile != NULL){
      cout << "Interference file: " << statskey << "\n\n";
    }
    
    cout << "Parsing file " << sharedfile << "...\n";
    readTrace(sharedfile, &sharedLatencies);
    
    cout << "Done!\nParsing " << alonefile << "...\n";
    readTrace(alonefile, &aloneLatencies);

    if(intEstimateFile != NULL){
      cout << "Done!\nParsing " << intEstimateFile << "...\n";
      readTrace(intEstimateFile, &measuredInterference);
    }
    
    cout << "Done!\nComputing interference...\n";
    int reqs = computeInterference(statsfile, statskey);
    
    cout << "Done!\nWriting output file...\n";
    writeInterferenceFile(outfile, reqs);
    if(intEstimateFile != NULL){
      writeInterferenceErrors((char*) "interferencetrace.txt");
    }

    cout << "Done!\n";
    
    return 0;
}

void readTrace(char* filename, std::map<Addr, std::list<Latencies> >* target){
    
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
        //if(shared) sharedLatencies[lats.address].push_back(lats);
        //else aloneLatencies[lats.address].push_back(lats);
	(*target)[lats.address].push_back(lats);
    }
    
    tracefile.close();
}


int computeInterference(char* statsfile, char* statskey){
    
    // remove all adresses that do not occur in both
    std::map<Addr, std::list<Latencies> >::iterator sharedIt = sharedLatencies.begin();
    std::map<Addr, std::list<Latencies> >::iterator intIt = measuredInterference.begin();
    bool doInt = intIt != measuredInterference.end();

    int erasedFromShared = 0;
    int errAddrs = 0;
    while(sharedIt != sharedLatencies.end()){
        std::map<Addr, std::list<Latencies> >::iterator tmpIt = aloneLatencies.find(sharedIt->first);
        if(tmpIt != aloneLatencies.end()){
            sharedIt++;
	    if(doInt) intIt++;
        }
        else{
            erasedFromShared += sharedIt->second.size();
	    errAddrs++;
            std::map<Addr, std::list<Latencies> >::iterator eraseIt = sharedIt;
            sharedIt++;
            sharedLatencies.erase(eraseIt);
	    if(doInt){
	      std::map<Addr, std::list<Latencies> >::iterator eraseIntIt = intIt;
	      intIt++;
	      sharedLatencies.erase(eraseIntIt);
	    }
        }
    }
    cout << "Erased " << erasedFromShared << " elements from shared, " << errAddrs << " unique addresses\n";
    
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
    intIt = measuredInterference.begin();
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

	    list<Latencies>::iterator intErrIt = intIt->second.begin();
	    pos = 0;
            for( ; intErrIt != intIt->second.end(); pos++){
                if(pos >= aloneIt->second.size()){
                    intErrIt = sharedIt->second.erase(intErrIt);
                }
                else{
                    intErrIt++;
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
	
	if(doInt) intIt++;
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
    intIt = measuredInterference.begin();

    for( ; sharedIt != sharedLatencies.end(); sharedIt++,aloneIt++){
      list<Latencies>::iterator sharedListIt = sharedIt->second.begin();
      list<Latencies>::iterator aloneListIt = aloneIt->second.begin();
      list<Latencies>::iterator intListIt;
      if(doInt){
	intListIt = intIt->second.begin();
      }

      assert(sharedIt->first == aloneIt->first);
      assert(interference.find(sharedIt->first) == interference.end());
      
      for( ; sharedListIt != sharedIt->second.end() ; sharedListIt++,aloneListIt++){
	Latencies lats = Latencies(*sharedListIt,*aloneListIt);
	interference[sharedIt->first].push_back(lats);
	if(doInt){
	  intError[intIt->first].push_back(InterferenceErrors(*intListIt,lats));
	  intListIt++;
	}
      }
      assert(aloneListIt == aloneIt->second.end());

      if(doInt) intIt++;
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
  intFile << "Bus Queue";
  intFile << setw(w);
  intFile << "Bus Service";
  intFile << setw(w);
  intFile << "Cache Capacity";
  intFile << "\n";

  map<int,Latencies>::iterator mapIt =  reqsPerInterferenceVal.begin();
  for( ; mapIt != reqsPerInterferenceVal.end() ; mapIt++){
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
    intFile << tmpFac.bus_queue;
    intFile << setw(w);
    intFile << tmpFac.bus_service;
    intFile << setw(w);
    intFile << tmpFac.cache_capacity;
    intFile << "\n";
  }

  intFile.flush();
  intFile.close();
}

void writeInterferenceErrors(char* filename){

  int w = 20;
  ofstream intFile(filename);
  intFile << setw(w);
  intFile << "Address";
  intFile << setw(w);
  intFile << "IC Entry";
  intFile << setw(w);
  intFile << "IC Transfer";
  intFile << setw(w);
  intFile << "IC Delivery";
  intFile << setw(w);
  intFile << "Bus Entry";
  intFile << setw(w);
  intFile << "Bus Queue";
  intFile << setw(w);
  intFile << "Bus Service";
  intFile << setw(w);
  intFile << "Cache Capacity";
  intFile << "\n";

  map<Addr,std::list<InterferenceErrors> >::iterator intIt =  intError.begin();
  for( ; intIt != intError.end() ; intIt++){

    list<InterferenceErrors>::iterator elementIt = intIt->second.begin();

    for( ; elementIt != intIt->second.end() ; elementIt++){
      
      InterferenceErrors element = *elementIt;

      intFile << setw(w);
      intFile << intIt->first;
      intFile << setw(w);
      intFile << element.ic_entry;
      intFile << setw(w);
      intFile << element.ic_transfer;
      intFile << setw(w);
      intFile << element.ic_delivery;
      intFile << setw(w);
      intFile << element.bus_entry;
      intFile << setw(w);
      intFile << element.bus_queue;
      intFile << setw(w);
      intFile << element.bus_service;
      intFile << setw(w);
      intFile << element.cache_capacity;
      intFile << "\n";
    }
  }

  intFile.flush();
  intFile.close();
}

Latencies::Latencies(){
  address        = 0;
  at_tick        = 0;
  ic_entry       = 0;
  ic_transfer    = 0;
  ic_delivery    = 0;
  bus_entry      = 0;
  bus_service    = 0;
  bus_queue      = 0;
  cache_capacity = 0;
}
   

Latencies::Latencies(char* line){
    
    int pos = 0;
    int bufferpos = 0;
    char buffer[BUFFER_SIZE];
    int addrBufferPos = 0;
    Addr addrBuffer[9];
    
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
    bus_queue = addrBuffer[7];
    bus_service = addrBuffer[8];
    cache_capacity = 0;
}

Latencies::Latencies(Latencies& shared, Latencies& alone){
  at_tick = 0;
  address = shared.address;
  
  ic_entry = shared.ic_entry - alone.ic_entry;
  ic_transfer = shared.ic_transfer - alone.ic_transfer;
  ic_delivery = shared.ic_delivery - alone.ic_delivery;

  //FIXME: cache capacity estimation not implemented
  cache_capacity = 0;
  bus_entry = shared.bus_entry - alone.bus_entry;
  bus_queue = shared.bus_queue - alone.bus_queue;
  bus_service = shared.bus_service - alone.bus_service;

//   if(shared.bus_queue != 0 && alone.bus_queue == 0){
//     // cache capacity interference
//     cache_capacity = shared.bus_transfer + shared.bus_entry;
//     bus_entry = 0;
//     bus_transfer = 0;
//   }
//   else if(shared.bus_transfer != 0 && alone.bus_transfer != 0){
//     // cache miss in both
//     cache_capacity = 0;
//     bus_entry = shared.bus_entry - alone.bus_entry;
//     bus_transfer = shared.bus_transfer - alone.bus_transfer;
//   }
//   else if(shared.bus_transfer == 0 && alone.bus_transfer != 0){
//     cache_capacity = -(alone.bus_transfer + alone.bus_entry);
//     bus_entry = 0;
//     bus_transfer = 0;
//   }
//   else{
//     cache_capacity = 0;
//     bus_entry = 0;
//     bus_transfer = 0;
//   }
}

std::string Latencies::toString(){
    stringstream ss;
    ss << "Tick:           " << at_tick << "\n";
    ss << "Address:        " << address << "\n";
    ss << "IC entry:       " << ic_entry << "\n";
    ss << "IC trans:       " << ic_transfer << "\n";
    ss << "IC delivery:    " << ic_delivery << "\n";
    ss << "Bus entry:      " << bus_entry << "\n";
    ss << "Bus Queue:      " << bus_queue << "\n";
    ss << "Bus Service:    " << bus_service << "\n";
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
  addValue(BUS_QUEUE, bus_queue, map);
  addValue(BUS_SERVICE, bus_service, map);
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
  case BUS_QUEUE:
    map[interferenceValue].bus_queue += 1;
    break;
  case BUS_SERVICE:
    map[interferenceValue].bus_service += 1;
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
    bus_queue      = lat.bus_queue;
    bus_service    = lat.bus_service;
    cache_capacity = lat.cache_capacity;
}

InterferenceErrors::InterferenceErrors(Latencies a, Latencies m){
  ic_entry       = computeError(m.ic_entry, a.ic_entry);
  ic_transfer    = computeError(m.ic_transfer, a.ic_transfer);
  ic_delivery    = computeError(m.ic_delivery, a.ic_delivery);
  bus_entry      = computeError(m.bus_entry, a.bus_entry);
  bus_queue      = computeError(m.bus_queue, a.bus_queue);
  bus_service    = computeError(m.bus_service, a.bus_service);
  cache_capacity = computeError(m.cache_capacity, a.cache_capacity);
}
