
#include <iostream>
#include <vector>
#include <fstream>
#include <cassert>
#include <cstdlib>
#include <fstream>
#include <cmath>
#include <sstream>

using namespace std;

#define BUFFER_SIZE 512

#define TRACE_LINE_ENTRIES 13

vector<string> readStringBuffer(char* buffer, int entries){
	vector<string> data(entries, "");

	int entryindex = 0;
	int charindex = 0;
	int bufferptr = 0;
	char tmpstorage[BUFFER_SIZE];
	while(buffer[charindex] != '\0'){
		if(buffer[charindex] == ';'){
			tmpstorage[bufferptr]  = '\0';
			data[entryindex] = string(tmpstorage);
			entryindex++;
			bufferptr = 0;
		}
		else{
			tmpstorage[bufferptr] = buffer[charindex];
			bufferptr++;
		}
		charindex++;
	}
	tmpstorage[bufferptr]  = '\0';
	data[entryindex] = string(tmpstorage);


	return data;
}

vector<int> readIntBuffer(char* buffer, int entries){
	vector<int> data(entries, 0);

	int entryindex = 0;
	int charindex = 0;
	int bufferptr = 0;
	char tmpstorage[BUFFER_SIZE];
	while(buffer[charindex] != '\0'){
		if(buffer[charindex] == ';'){
			tmpstorage[bufferptr]  = '\0';
			data[entryindex] = atoi(tmpstorage);
			entryindex++;
			bufferptr = 0;
		}
		else{
			tmpstorage[bufferptr] = buffer[charindex];
			bufferptr++;
		}
		charindex++;
	}
	tmpstorage[bufferptr]  = '\0';
	data[entryindex] = atoi(tmpstorage);


	return data;
}

vector<double> readFloatBuffer(char* buffer, int entries){
	vector<double> data(entries, 0);

	int entryindex = 0;
	int charindex = 0;
	int bufferptr = 0;
	char tmpstorage[BUFFER_SIZE];
	while(buffer[charindex] != '\0'){
		if(buffer[charindex] == ';'){
			tmpstorage[bufferptr]  = '\0';
			data[entryindex] = atof(tmpstorage);
			entryindex++;
			bufferptr = 0;
		}
		else{
			tmpstorage[bufferptr] = buffer[charindex];
			bufferptr++;
		}
		charindex++;
	}
	tmpstorage[bufferptr]  = '\0';
	data[entryindex] = atof(tmpstorage);


	return data;
}

void write2DDict(ofstream* resfile,
		         const char* name,
		         vector<int>* samplesizes,
		         vector<vector<double> >* storage,
		         vector<string>* headers){

	*resfile << "\n" << name << " = {\n";
	for(unsigned int i=0;i<samplesizes->size();i++){
		*resfile << (*samplesizes)[i] << ":{";
		for(int j=0;j<TRACE_LINE_ENTRIES-2;j++){
			*resfile << "'" << (*headers)[j+2] << "'" << ": " << (*storage)[i][j];
			if(j < TRACE_LINE_ENTRIES-3) *resfile << ", ";
		}
		*resfile << "}";
		if(i < samplesizes->size()-1) *resfile << ",";
		*resfile << "\n";
	}
	*resfile << "}\n\n";
}

void write1DDict(ofstream* resfile,
                const char* name,
                vector<int>* samplesizes,
                vector<unsigned long long>* storage){

	*resfile << "\n" << name << " = {\n";
	for(unsigned int i=0;i<samplesizes->size();i++){
		*resfile << (*samplesizes)[i] << ":" << (*storage)[i];
		if(i < samplesizes->size()-1) *resfile << ",";
		*resfile << "\n";
	}
	*resfile << "}\n\n";
}

int main(int argc, char** argv){

	if(argc != 7){
		cout << "Takes 6 args: estimate, alone, shared, samples, numSampleSizes, id\n";
		return 0;
	}

	char* estimatefilename = argv[1];
	char* alonefilename = argv[2];
	char* sharedfilename = argv[3];
	char* samplesizesinput = argv[4];
	int numSampleSizes = atoi(argv[5]);
	char* uniqueID = argv[6];

	cout << "\nComparing traces from:\n";
	cout << "Estimate:       " << estimatefilename << "\n";
	cout << "Alone latency:  " << alonefilename << "\n";
	cout << "Shared latency: " << sharedfilename << "\n";
	cout << "Sample sizes:   " << samplesizesinput << "\n\n";

	vector<int> samplesizes = readIntBuffer(samplesizesinput, numSampleSizes);

	ifstream efile(estimatefilename);
	ifstream afile(alonefilename);
	ifstream sfile(sharedfilename);

	assert(efile.good() && afile.good() && sfile.good());

	vector<vector<double> > sumEstimateBuffer(numSampleSizes, vector<double>(TRACE_LINE_ENTRIES-2, 0.0));
	vector<vector<double> > sumAloneBuffer(numSampleSizes, vector<double>(TRACE_LINE_ENTRIES-2, 0.0));
	vector<vector<double> > sumSharedBuffer(numSampleSizes, vector<double>(TRACE_LINE_ENTRIES-2, 0.0));

	vector<vector<double> > sqErrorSum(numSampleSizes, vector<double>(TRACE_LINE_ENTRIES-2, 0.0));
	vector<vector<double> > errorSum(numSampleSizes, vector<double>(TRACE_LINE_ENTRIES-2, 0.0));

	vector<vector<double> > sqRelativeErrorSum(numSampleSizes, vector<double>(TRACE_LINE_ENTRIES-2, 0.0));
	vector<vector<double> > relativeErrorSum(numSampleSizes, vector<double>(TRACE_LINE_ENTRIES-2, 0.0));

	vector<unsigned long long> numSamples(numSampleSizes, 0);

	vector<unsigned long long> lastSampleTick(numSampleSizes, 0);
	vector<unsigned long long> latencySum(numSampleSizes, 0);
	vector<unsigned long long> sqLatencySum(numSampleSizes, 0);

	vector<unsigned long long> maxLatencyBuffer(numSampleSizes, 0);

	int requests = 1;
	char abuffer[BUFFER_SIZE];
	char ebuffer[BUFFER_SIZE];
	char sbuffer[BUFFER_SIZE];

	bool areseof = afile.getline(abuffer, BUFFER_SIZE).eof();
	bool ereseof = efile.getline(ebuffer, BUFFER_SIZE).eof();
	bool sreseof = sfile.getline(sbuffer, BUFFER_SIZE).eof();

	vector<string> headers = readStringBuffer(abuffer, TRACE_LINE_ENTRIES);

	int remainingAlone = 0;
	int remainingShared = 0;
	int remainingSharedLatency = 0;

	while(!areseof && !ereseof){

		areseof = afile.getline(abuffer, BUFFER_SIZE).eof();
		ereseof = efile.getline(ebuffer, BUFFER_SIZE).eof();
		sreseof = sfile.getline(sbuffer, BUFFER_SIZE).eof();

		if(areseof || ereseof || sreseof) continue;

		vector<double> adata = readFloatBuffer(abuffer, TRACE_LINE_ENTRIES);
		vector<double> edata = readFloatBuffer(ebuffer, TRACE_LINE_ENTRIES);
		vector<double> sdata = readFloatBuffer(sbuffer, TRACE_LINE_ENTRIES);

		for(unsigned int i=0;i<samplesizes.size();i++){
			for(int j=0;j<TRACE_LINE_ENTRIES-2;j++){
				sumAloneBuffer[i][j] += adata[j+2];
				sumEstimateBuffer[i][j] += edata[j+2];
				sumSharedBuffer[i][j] += sdata[j+2];
			}

			if(requests % samplesizes[i] == 0){

				for(int j=0;j<TRACE_LINE_ENTRIES-2;j++){

					double aloneAvgLat  = (double) (sumAloneBuffer[i][j] / (double) samplesizes[i]);
					double estimate     = (double) (sumEstimateBuffer[i][j] / (double) samplesizes[i]);
					double sharedAvgLat = (double) (sumSharedBuffer[i][j] / (double) samplesizes[i]);

					double error = estimate - aloneAvgLat;
					double sqerror = pow(error, 2);

					errorSum[i][j] += error;
					sqErrorSum[i][j] += sqerror;

					if(sharedAvgLat > 0){
						double relativeError = abs(estimate -  aloneAvgLat) / ((double) sharedAvgLat);
						assert(!isinf(relativeError) && !isnan(relativeError));

						double sqRelativeError = pow(relativeError, 2);

						relativeErrorSum[i][j] += relativeError;
						sqRelativeErrorSum[i][j] += sqRelativeError;
					}
					else{
						assert(headers[j+2] != "Total");
					}

					sumAloneBuffer[i][j] = 0;
					sumEstimateBuffer[i][j] = 0;
					sumSharedBuffer[i][j] = 0;
				}

				if(lastSampleTick[i] != 0){
					assert((unsigned long long) edata[0] > lastSampleTick[i]);
					unsigned long long latency = edata[0] - lastSampleTick[i];

					latencySum[i] += latency;
					sqLatencySum[i] += pow(latency, 2);

					if(latency > maxLatencyBuffer[i]){
						maxLatencyBuffer[i] = latency;
					}
				}
				lastSampleTick[i] = edata[0];

				numSamples[i] += 1;
			}
		}

		if(requests % 1000000 == 0) cout << "Read " << requests << " lines\n";

		requests++;
	}

	if(!areseof) while(!afile.getline(abuffer, BUFFER_SIZE).eof()) remainingAlone++;
	if(!ereseof) while(!efile.getline(ebuffer, BUFFER_SIZE).eof()) remainingShared++;
	if(!sreseof) while(!sfile.getline(sbuffer, BUFFER_SIZE).eof()) remainingSharedLatency++;
	assert(remainingShared == remainingSharedLatency);

	int remainingReqs = remainingAlone > 0 ? remainingAlone : remainingShared;

	stringstream filename;
	filename << uniqueID << ".py";

	ofstream resfile(filename.str().c_str());

	write2DDict(&resfile, "sumError", &samplesizes, &errorSum, &headers);
	write2DDict(&resfile, "sumSquareError", &samplesizes, &sqErrorSum, &headers);
	write2DDict(&resfile, "sumRelativeError", &samplesizes, &relativeErrorSum, &headers);
	write2DDict(&resfile, "sumSquareRelativeError", &samplesizes, &sqRelativeErrorSum, &headers);

	write1DDict(&resfile, "numSamples", &samplesizes, &numSamples);

	write1DDict(&resfile, "sumLatency", &samplesizes, &latencySum);
	write1DDict(&resfile, "sumSquareLatency", &samplesizes, &sqLatencySum);

	resfile << "\nmaxlat = {\n";
	for(unsigned int i=0;i<samplesizes.size();i++){
		resfile << samplesizes[i] << ":" << (maxLatencyBuffer[i] == 0 ? -1 : maxLatencyBuffer[i]);
		if(i < samplesizes.size()-1) resfile << ",";
		resfile << "\n";
	}
	resfile << "}\n\n";

	resfile << "remainingReqs = " << remainingReqs << "\n\n";

	resfile << "expid = '" << uniqueID << "'\n\n";

	resfile.flush();
	resfile.close();

	return 0;
}
