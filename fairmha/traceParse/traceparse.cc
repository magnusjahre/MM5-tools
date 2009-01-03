
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
    
    cout << "Shared file: " << sharedfile << "\n";
    cout << "Alone file: " << alonefile << "\n";
    cout << "Output file: " << outfile << "\n\n";
    
    
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
    int linecnt = 0;
    
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
        
        linecnt++;
        if(linecnt % 1000000 == 0) cout << linecnt << " lines parsed\n";
    }
    
    tracefile.close();
}


void computeInterference(){
    
}


void writeInterferenceFile(char* filename){
    
}

void fatal(const char* message){
    cerr << message << "\n";
    exit(0);
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