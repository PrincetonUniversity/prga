#include "util.hpp"
#include "synth.hpp"

using namespace std;
using namespace blifparse;

LutInstance::LutInstance():
    _bitstream()
{
}

LutInstance::LutParseStatus LutInstance::populate(const unsigned int & num_nets,
        const vector<vector<LogicValue>> & so_cover) {
    auto num_inputs = num_nets - 1;
    auto rule_type = LogicValue::UNKOWN;
    _bitstream = vector<bool>(1 << num_inputs, false);

    for (auto & entry : so_cover) {
        if (num_nets != entry.size()) {
            return LUT_PARSE_STATUS_NETS_AND_TRUTH_TABLE_MISMATCH;
        }

        if (rule_type == LogicValue::UNKOWN) {
            switch (entry.back()) {
                case LogicValue::TRUE:
                    rule_type = LogicValue::TRUE;
                    break;
                case LogicValue::FALSE:
                    rule_type = LogicValue::FALSE;
                    _bitstream = vector<bool>(1 << num_inputs, true);
                    break;
                default:
                    return LUT_PARSE_STATUS_INVALID_TRUTH_TABLE_SYMBOL;
            }
        } else if (rule_type != entry.back()) {
            return LUT_PARSE_STATUS_INCONSISTENT_TRUTH_TABLE_ENTRY;
        }

        vector<int> indices(1, 0);
        for (unsigned int bit = 0; bit < num_inputs; ++bit) {
            // XXX: endianness of this?
            switch (entry[bit]) {
                case LogicValue::TRUE:
                    for (auto & idx : indices) {
                        idx |= 1 << bit;
                    }
                    break;
                case LogicValue::FALSE:
                    break;
                case LogicValue::DONT_CARE:
                    {
                        vector<int> indices_dup(indices);
                        for (auto & idx : indices) {
                            idx |= 1 << bit;
                        }
                        indices.reserve(2 * indices.size());
                        indices.insert(indices.end(), indices_dup.begin(), indices_dup.end());
                        break;
                    }
                default:
                    return LUT_PARSE_STATUS_INVALID_TRUTH_TABLE_SYMBOL;
            }
        }

        for (auto & idx : indices) {
            _bitstream[idx] = (rule_type == LogicValue::TRUE) ? true : false;
        }
    }

    return LUT_PARSE_STATUS_SUCCESS;
}

vector<bool> LutInstance::rotate(const vector<int> & rotation_map) const {
    int new_size = 1 << rotation_map.size();
    auto new_ = vector<bool>(new_size, false);

    for (int new_idx = 0; new_idx < new_size; ++new_idx) {
        int old_idx = 0, new_bit = 0;
        for (auto old_bit : rotation_map) {
            if (old_bit >= 0) {
                old_idx |= ((new_idx & (1 << new_bit)) ? 1 : 0) << old_bit;
            }
            ++new_bit;
        }
        new_[new_idx] = _bitstream[old_idx];
    }
    return new_;
}

const vector<bool> & LutInstance::get_bitstream() const {
    return _bitstream;
}

SynthResultManager::SynthResultManager(): 
    _luts(), _state(PARSER_STATE_INIT), _lineno(-1), _filename("BLIF FILE")
{}

const LutInstance * SynthResultManager::get_lut(const string & name) const {
    auto it = _luts.find(name);
    return (it == _luts.end()) ? nullptr : &(it->second);
}

const map<string, LutInstance> & SynthResultManager::get_luts() const {
    return _luts;
}

SynthResultManager::ParseBLIFReturnStatus SynthResultManager::parse_blif(const char * filename) {
    _state = PARSER_STATE_INIT;
    blif_parse_filename(filename, *this);
    switch (_state) {
        case PARSER_STATE_INIT:
        case PARSER_STATE_PARSE_STARTED:
        case PARSER_STATE_MODEL_BEGAN:
        case PARSER_STATE_MODEL_ENDED:
            ERROR("[BLIF] {}: {} BLIF parser ended in non-finished state", _filename, _lineno);
            return PARSE_BLIF_STATUS_INCOMPLETE;
        case PARSER_STATE_PARSE_FINISHED:
            return PARSE_BLIF_STATUS_SUCCESS;
        case PARSER_STATE_MULTIPLE_MODELS:
            return PARSE_BLIF_STATUS_MULTIPLE_MODELS;
        case PARSER_STATE_LUT_NAME_CONFLICTS:
            return PARSE_BLIF_STATUS_LUT_NAME_CONFLICTS;
        case PARSER_STATE_PARSER_ERROR:
            return PARSE_BLIF_STATUS_PARSER_ERROR;
        case PARSER_STATE_INVALID_STATE:
        default:
            ERROR("[BLIF] {}:{} Invalid BLIF parser state transition", _filename, _lineno);
            return PARSE_BLIF_STATUS_INVALID_STATE;
    }
}

SynthResultManager::ParseBLIFReturnStatus SynthResultManager::parse_blif(const string & filename) {
    return parse_blif(filename.c_str());
}

void SynthResultManager::start_parse() {
    if (_state > PARSER_STATE_VALID_BOUNDARY) {
        return;
    }
    
    if (_state != PARSER_STATE_INIT) {
        _state = PARSER_STATE_INVALID_STATE;
    } else {
        _state = PARSER_STATE_PARSE_STARTED;
    }
}

void SynthResultManager::filename(string fname) {
    _filename = fname;
}

void SynthResultManager::lineno(int line_num) {
    if (_state < PARSER_STATE_VALID_BOUNDARY) {
        _lineno = line_num;
    }
}

void SynthResultManager::begin_model(string model_name) {
    if (_state > PARSER_STATE_VALID_BOUNDARY) {
        return;
    }
    
    if (_state == PARSER_STATE_MODEL_ENDED) {
        ERROR("[BLIF] {}:{} Multiple models defined in one BLIF. Not supported by VPR", _filename, _lineno);
        _state = PARSER_STATE_MULTIPLE_MODELS;
    } else if (_state != PARSER_STATE_PARSE_STARTED) {
        _state = PARSER_STATE_INVALID_STATE;
    } else {
        _state = PARSER_STATE_MODEL_BEGAN;
    }
}

void SynthResultManager::inputs(vector<string> inputs) {
    (void)inputs;
}

void SynthResultManager::outputs(vector<string> outputs) {
    (void)outputs;
}

void SynthResultManager::names(vector<string> nets,
        vector<vector<LogicValue> > so_cover) {
    if (_state > PARSER_STATE_VALID_BOUNDARY) {
        return;
    }

    auto name = nets.back();
    if (nets.size() <= 1) {
        WARN("[BLIF] {}:{} .names tag with no inputs: {}", _filename, _lineno, name);
    } else if (_luts.find(name) != _luts.end()) {
        ERROR("[BLIF] {}:{} Two LUTs drive the same net: {}", _filename, _lineno, name);
        _state = PARSER_STATE_LUT_NAME_CONFLICTS;
        return;
    }

    switch (_luts[name].populate(nets.size(), so_cover)) {
        case LutInstance::LUT_PARSE_STATUS_SUCCESS:
            return;
        case LutInstance::LUT_PARSE_STATUS_NETS_AND_TRUTH_TABLE_MISMATCH:
            ERROR("[BLIF] {}:{} Number of bits in the truth table mismatches with number of nets: {}",
                    _filename, _lineno, name);
            _state = PARSER_STATE_PARSER_ERROR;
            break;
        case LutInstance::LUT_PARSE_STATUS_INCONSISTENT_TRUTH_TABLE_ENTRY:
            ERROR("[BLIF] {}:{} Mixed usage of true & false truth table entries: {}",
                    _filename, _lineno, name);
            _state = PARSER_STATE_PARSER_ERROR;
            break;
        case LutInstance::LUT_PARSE_STATUS_INVALID_TRUTH_TABLE_SYMBOL:
            ERROR("[BLIF] {}:{} Invalid symbol found in .names tag: {}",
                    _filename, _lineno, name);
            _state = PARSER_STATE_PARSER_ERROR;
            break;
        default:
            CRITICAL("[BLIF] {}:{} Unknown return value from LUT instance populate",
                    _filename, _lineno, name);
            _state = PARSER_STATE_PARSER_ERROR;
            break;
    }
}

void SynthResultManager::latch(string input,
        string output,
        LatchType type,
        string control,
        LogicValue init) {
    (void)input;
    (void)output;
    (void)type;
    (void)control;
    (void)init;
}

void SynthResultManager::subckt(string model,
        vector<string> ports,
        vector<string> nets) {
    (void)model;
    (void)ports;
    (void)nets;
}

void SynthResultManager::blackbox() {}

void SynthResultManager::end_model() {
    if (_state > PARSER_STATE_VALID_BOUNDARY) {
        return;
    }
    
    if (_state != PARSER_STATE_MODEL_BEGAN) {
        _state = PARSER_STATE_INVALID_STATE;
    } else {
        _state = PARSER_STATE_MODEL_ENDED;
    }
}

void SynthResultManager::finish_parse() {
    if (_state > PARSER_STATE_VALID_BOUNDARY) {
        return;
    }
    
    if (_state != PARSER_STATE_MODEL_ENDED) {
        _state = PARSER_STATE_INVALID_STATE;
    } else {
        _state = PARSER_STATE_PARSE_FINISHED;
    }
}

void SynthResultManager::parse_error(const int curr_lineno,
        const string & near_text,
        const string & msg) {
    if (_state > PARSER_STATE_VALID_BOUNDARY) {
        return;
    }
    
    ERROR("[BLIF] {}:{} Parser error: {}", _filename, _lineno, msg);
    _state = PARSER_STATE_PARSER_ERROR;
}
