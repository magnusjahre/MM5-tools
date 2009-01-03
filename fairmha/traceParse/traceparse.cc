
#include "traceparse.hh"

using namespace std;

#define BUFFER_SIZE 512

int main(int argc, char** argv){
    
    if(argc != 4){
        cout << "Usage: traceparse sharedfilename alonefilename outfile\n";
        exit(0);
    }
    
    cout << "\nParsing trace files, input:\n";
    
    char* sharedfile = argv[1];
    char* alonefile = argv[2];
    char* outfile = argv[3];
    
    cout << "Shared file:   " << sharedfile << "\n";
    cout << "Alone file:    " << alonefile << "\n";
    cout << "Output file:   " << outfile << "\n\n";
    
    cout << "Parsing file " << sharedfile << "...\n";
    readTrace(sharedfile, true);
    
    cout << "Done!\nParsing " << alonefile << "...\n";
    readTrace(alonefile, false);
    
    cout << "Done!\nComputing interference...\n";
    computeInterference();
    
    cout << "Done!\nWriting output file...\n";
    writeInterferenceFile(outfile);
    cout << "Done!\n";
    
    return 0;
}

void readTrace(char* filename, bool shared){
    
    char buffer[BUFFER_SIZE];
    
    bool first = true;
    ifstream tracefile(filename);
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


void computeInterference(){
    
    // remove all adresses that do not occur in both
    std::map<Addr, std::list<Latencies> >::iterator sharedIt = sharedLatencies.begin();
    int erasedFromShared = 0;
    while(sharedIt != sharedLatencies.end()){
        std::map<Addr, std::list<Latencies> >::iterator tmpIt = aloneLatencies.find(sharedIt->first);
        if(tmpIt != aloneLatencies.end()){
            sharedIt++;
        }
        else{
            std::map<Addr, std::list<Latencies> >::iterator eraseIt = sharedIt++;
            sharedLatencies.erase(eraseIt);
            erasedFromShared++;
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
            std::map<Addr, std::list<Latencies> >::iterator eraseIt = aloneIt++;
            sharedLatencies.erase(eraseIt);
            erasedFromAlone++;
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
    
}


void writeInterferenceFile(char* filename){
    
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