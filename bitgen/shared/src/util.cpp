#include <iomanip>
#include <sstream>
#include <string>

#include "util.hpp"

using namespace std;

shared_ptr<spdlog::logger> logger;

string bitstream_to_string(const vector<bool> & bitstream) {
    if (bitstream.empty()) {
        return string("0'h0");
    }
    stringstream ss;
    vector<int> content(bitstream.size()/4 +
            ((bitstream.size() % 4 == 0) ? 0 : 1), 0);
    for (unsigned int i = 0; i < bitstream.size(); ++i) {
        int idx = content.size() - 1 - i/4;
        content[idx] |= bitstream[i] ? (1 << (i % 4)) : 0;
    }
    ss << bitstream.size() << "'h";
    for (auto v : content) {
        ss << hex << v;
    }
    return ss.str();
}

vector<string> split(const string & str, const string & delim) {
    vector<string> tokens;
    size_t prev = 0;
    while (prev < str.length()) {
        size_t pos = str.find_first_of(delim, prev);
        if (pos == string::npos) {
            pos = str.length();
        }
        string token = str.substr(prev, pos - prev);
        if (!token.empty()) {
            tokens.push_back(token);
        }
        prev = pos + delim.length();
    }
    return tokens;
}
