#include <cstring>
#include <cstdio>
#include <fstream>

#include "expat.h"

#include "util.hpp"
#include "pack.hpp"

using namespace std;
using namespace prga;

static void XMLCALL
startElement(void * userData, const XML_Char * name, const XML_Char ** attrs) {
    AbstractPackingManager * mgr = static_cast<AbstractPackingManager *>(userData);
    string name_(name);
    AbstractPackingManager::AttributeMap attrs_;

    for (int i = 0; attrs[i]; i += 2) {
        attrs_.emplace(attrs[i], attrs[i + 1]);
    }

    mgr->_xml_start_element_handler(name_, attrs_);
}

static void XMLCALL
endElement(void * userData, const XML_Char * name) {
    AbstractPackingManager * mgr = static_cast<AbstractPackingManager *>(userData);
    string name_(name);

    mgr->_xml_end_element_handler(name_);
}

static void XMLCALL
characterDataHandler(void * userData, const XML_Char * data, int length) {
    AbstractPackingManager * mgr = static_cast<AbstractPackingManager *>(userData);
    mgr->_xml_character_data_handler(string(data, length));
}

const string AbstractPackingManager::_Constants::str_block("block");
const string AbstractPackingManager::_Constants::str_name("name");
const string AbstractPackingManager::_Constants::str_instance("instance");
const string AbstractPackingManager::_Constants::str_mode("mode");
const string AbstractPackingManager::_Constants::str_inputs("inputs");
const string AbstractPackingManager::_Constants::str_outputs("outputs");
const string AbstractPackingManager::_Constants::str_clocks("clocks");
const string AbstractPackingManager::_Constants::str_port("port");
const string AbstractPackingManager::_Constants::str_attributes("attributes");
const string AbstractPackingManager::_Constants::str_parameters("parameters");
const string AbstractPackingManager::_Constants::str_rotation("port_rotation_map");
const string AbstractPackingManager::_Constants::str_extio_i("extio_i[0]");
const string AbstractPackingManager::_Constants::str_extio_o("extio_o[0]");
const string AbstractPackingManager::_Constants::str_open("open");
const string AbstractPackingManager::_Constants::str_wire("wire");

const regex AbstractPackingManager::_Constants::regex_instance("^(\\w+)\\[(\\d+)\\]$");
const regex AbstractPackingManager::_Constants::regex_connection(
        "^(\\w+(?:\\[0\\])?\\.\\w+\\[\\d+\\])->.*$");

AbstractPackingManager::AbstractPackingManager(const ConfigDatabase * config_db,
        const SynthResultManager * synth_mgr):
    _config_db(config_db), _synth_mgr(synth_mgr),
    _state(AbstractPackingManager::PARSER_STATE_INIT),
    _substate(AbstractPackingManager::PARSER_SUBSTATE_NONE),
    _cur_block(nullptr), _cur_instance(nullptr), _cur_lut(nullptr), _cur_port(nullptr),
    _ignore_level(0), _buffer(), _filename(), _lineno(-1)
{}

AbstractPackingManager::ParsePackingResultStatus AbstractPackingManager::parse_packing_result(const char * filename) {
    TRACE("[PACK] Packing result parsing started");
    _filename = filename;

    if (nullptr == _config_db) {
        ERROR("[PACK] Config database is nullptr");
        return PARSE_PACKING_RESULT_NULL_CONFIG_DB;
    }

    if (nullptr == _synth_mgr) {
        ERROR("[PACK] Synthesized result manager is nullptr");
        return PARSE_PACKING_RESULT_NULL_SYNTH_MGR;
    }

    XML_Parser parser = XML_ParserCreate(nullptr);

    if (!parser) {
        ERROR("[PACK] Couldn't allocate memory for parser");
        return PARSE_PACKING_RESULT_XML_ERROR;
    }

    ifstream stream(filename);
    if (!stream) {
        ERROR("[PACK] Packing result file error: {}", _filename);
        return PARSE_PACKING_RESULT_FILE_ERROR;
    }

    XML_SetUserData(parser, dynamic_cast<AbstractPackingManager *>(this));
    XML_SetElementHandler(parser, startElement, endElement);
    XML_SetCharacterDataHandler(parser, characterDataHandler);

    int done = 0;
    string line;
    _lineno = 0;
    do {
        ++_lineno;
        getline(stream, line);
        done = stream.eof();

        if (XML_Parse(parser, line.c_str(), line.size(), done) == XML_STATUS_ERROR) {
            ERROR("[PACK] {}:{} XML Error: {}",
                    _filename, _lineno,
                    XML_ErrorString(XML_GetErrorCode(parser)));
            XML_ParserFree(parser);
            return PARSE_PACKING_RESULT_XML_ERROR;
        }
    } while (_state < PARSER_STATE_VALID_BOUNDARY && !done);

    XML_ParserFree(parser);

    switch (_state) {
        case PARSER_STATE_FORMAT_ERROR:
            return PARSE_PACKING_RESULT_FORMAT_ERROR;
        case PARSER_STATE_INTERNAL_ERROR:
            return PARSE_PACKING_RESULT_INTERNAL_ERROR;
        case PARSER_STATE_MISSING_IN_CONFIG_DB:
            return PARSE_PACKING_RESULT_MISSING_IN_CONFIG_DB;
        case PARSER_STATE_MISSING_IN_SYNTH_MGR:
            return PARSE_PACKING_RESULT_MISSING_IN_SYNTH_MGR;
        case PARSER_STATE_DONE:
            break;
        default:
            ERROR("[PACK] Parsing stopped at an invalid state");
            return PARSE_PACKING_RESULT_INCOMPLETE;
    }

    TRACE("[PACK] Packing result parsing done");
    return PARSE_PACKING_RESULT_SUCCESS;
}

AbstractPackingManager::ParsePackingResultStatus AbstractPackingManager::parse_packing_result(const string & filename) {
    return parse_packing_result(filename.c_str());
}

void AbstractPackingManager::_xml_start_element_handler(const string & name,
        const AbstractPackingManager::AttributeMap & attrs) {
    TRACE("[PACK] {}:{} <{}> start, state: {}, {}", _filename, _lineno, name, _state, _substate);

    if (_state > PARSER_STATE_VALID_BOUNDARY) {
        return;
    }

    static const int    SUBSTATE_FLAG_TRANSITION    = 1 << 0,
                        SUBSTATE_FLAG_IGNORE        = 1 << 1,
                        SUBSTATE_FLAG_ROTATION      = 1 << 2;
    int substate_flags = 0;

    // main finite state machine
    switch (_state) {
        case PARSER_STATE_INIT:     // just initialized
            assert(!_cur_block && !_cur_instance && !_cur_port && !_cur_lut);
            if (name.compare(_Constants::str_block) != 0) {
                ERROR("[PACK] {}:{} Expecting <block> element ({} found)", _filename, _lineno, name);
                _state = PARSER_STATE_FORMAT_ERROR;
                return;
            }
            _state = PARSER_STATE_IDLE;
            break;
        case PARSER_STATE_IDLE:     // waiting for the next block
            assert(!_cur_block && !_cur_instance && !_cur_port && !_cur_lut);
            if (name.compare(_Constants::str_inputs) == 0 ||
                    name.compare(_Constants::str_outputs) == 0 ||
                    name.compare(_Constants::str_clocks) == 0) {
                _state = PARSER_STATE_IGNORE;   // ignore top-level ports
                _ignore_level = 1;
            } else if (name.compare(_Constants::str_block) == 0) {
                _enter_block(attrs);
            } else {
                ERROR("[PACK] {}:{} Unexpected element: {})", _filename, _lineno, name);
                _state = PARSER_STATE_FORMAT_ERROR;
                return;
            }
            break;
        case PARSER_STATE_BLOCK:    // processing a block instance
            assert(_cur_block && !_cur_instance && !_cur_lut);
            if (_substate == PARSER_SUBSTATE_NONE &&
                    name.compare(_Constants::str_block) == 0) {
                _enter_instance(attrs);
            } else {
                substate_flags |= SUBSTATE_FLAG_TRANSITION;
            }
            break;
        case PARSER_STATE_LUT:
            assert(_cur_block && _cur_instance && _cur_lut);
            if (_substate == PARSER_SUBSTATE_NONE &&
                    name.compare(_Constants::str_block) == 0) {
                _state = PARSER_STATE_LUT_INNER;
            } else {
                substate_flags |= SUBSTATE_FLAG_TRANSITION;
            }
            break;
        case PARSER_STATE_MULTIMODE:
            assert(_cur_block && _cur_instance && !_cur_lut);
            if (_substate == PARSER_SUBSTATE_NONE &&
                    name.compare(_Constants::str_block) == 0) {
                _state = PARSER_STATE_MULTIMODE_INNER;
            } else {
                substate_flags |= SUBSTATE_FLAG_TRANSITION;
            }
            break;
        case PARSER_STATE_LUT_INNER:
            assert(_cur_block && _cur_instance  && _cur_lut);
            substate_flags |= SUBSTATE_FLAG_TRANSITION | SUBSTATE_FLAG_ROTATION | SUBSTATE_FLAG_IGNORE;
            break;
        case PARSER_STATE_LUT_WIRE:
        case PARSER_STATE_MULTIMODE_INNER:
        case PARSER_STATE_CUSTOM:
            assert(_cur_block && _cur_instance && !_cur_lut);
            substate_flags |= SUBSTATE_FLAG_TRANSITION | SUBSTATE_FLAG_IGNORE;
            break;
        case PARSER_STATE_IGNORE:
            _ignore_level += 1;
            break;
        default:
            ERROR("[PACK] Invalid parser state");
            _state = PARSER_STATE_INTERNAL_ERROR;
            return;
    }

    if ( !(substate_flags & SUBSTATE_FLAG_TRANSITION) ) {
        return;
    }

    // sub-state transitions
    switch (_substate) {
        case PARSER_SUBSTATE_NONE: // not in any child element in a block/instance
            if (name.compare(_Constants::str_inputs) == 0) {
                _substate = PARSER_SUBSTATE_INPUTS;
            } else if (name.compare(_Constants::str_outputs) == 0) {
                _substate = PARSER_SUBSTATE_OUTPUTS;
            } else if (name.compare(_Constants::str_clocks) == 0) {
                _substate = PARSER_SUBSTATE_CLOCKS;
            } else if (substate_flags & SUBSTATE_FLAG_IGNORE) {
                _substate = PARSER_SUBSTATE_IGNORE;
                _ignore_level = 1;
            } else {
                ERROR("[PACK] {}:{} Unexpected element: {}", _filename, _lineno, name);
                _state = PARSER_STATE_FORMAT_ERROR;
                return;
            }
            break;
        case PARSER_SUBSTATE_INPUTS:
            if (name.compare(_Constants::str_port) == 0) {
                _substate = PARSER_SUBSTATE_INPUT_PORT;
                if (_state == PARSER_STATE_LUT || 
                        _state == PARSER_STATE_LUT_WIRE ||
                        _state == PARSER_STATE_MULTIMODE ||
                        _state == PARSER_STATE_CUSTOM) {
                    _enter_port(attrs);
                }
            } else if ((substate_flags & SUBSTATE_FLAG_ROTATION) &&
                    name.compare(_Constants::str_rotation) == 0) {
                _substate = PARSER_SUBSTATE_ROTATION;
            } else {
                ERROR("[PACK] {}:{} Unexpected element: {}", _filename, _lineno, name);
                _state = PARSER_STATE_FORMAT_ERROR;
                return;
            }
            _buffer.clear();
            break;
        case PARSER_SUBSTATE_OUTPUTS:
            if (name.compare(_Constants::str_port) == 0) {
                _substate = PARSER_SUBSTATE_OUTPUT_PORT;
                if (_state == PARSER_STATE_BLOCK) {
                    _enter_port(attrs);
                }
            } else {
                ERROR("[PACK] {}:{} Unexpected element: {}", _filename, _lineno, name);
                _state = PARSER_STATE_FORMAT_ERROR;
                return;
            }
            _buffer.clear();
            break;
        case PARSER_SUBSTATE_CLOCKS:
            if (name.compare(_Constants::str_port) == 0) {
                _substate = PARSER_SUBSTATE_CLOCK_PORT;
                if (_state == PARSER_STATE_MULTIMODE || 
                        _state == PARSER_STATE_CUSTOM) {
                    _enter_port(attrs);
                }
            } else {
                ERROR("[PACK] {}:{} Unexpected element: {}", _filename, _lineno, name);
                _state = PARSER_STATE_FORMAT_ERROR;
                return;
            }
            _buffer.clear();
            break;
        case PARSER_SUBSTATE_INPUT_PORT:
        case PARSER_SUBSTATE_OUTPUT_PORT:
        case PARSER_SUBSTATE_CLOCK_PORT:
        case PARSER_SUBSTATE_ROTATION:
            ERROR("[PACK] {}:{} Unexpected element: {}", _filename, _lineno, name);
            _state = PARSER_STATE_FORMAT_ERROR;
            return;
        case PARSER_SUBSTATE_IGNORE:
            _ignore_level += 1;
            return;
        default:
            ERROR("[PACK] Invalid parser sub-state");
            _state = PARSER_STATE_INTERNAL_ERROR;
            return;
    }
}

void AbstractPackingManager::_xml_end_element_handler(const string & name) {
    TRACE("[PACK] {}:{} <{}> end, state: {}, {}", _filename, _lineno, name, _state, _substate);

    if (_state > PARSER_STATE_VALID_BOUNDARY) {
        return;
    }

    static const int    SUBSTATE_FLAG_TRANSITION    = 1 << 0;
    int substate_flags = 0;

    // main state machine
    switch (_state) {
        case PARSER_STATE_IDLE:
            _state = PARSER_STATE_DONE;
            break;
        case PARSER_STATE_IGNORE:
            _ignore_level -= 1;
            if (0 == _ignore_level) {
                _state = PARSER_STATE_IDLE;
            }
            break;
        case PARSER_STATE_BLOCK:
            if (_substate == PARSER_SUBSTATE_NONE) {
                _cur_block = nullptr;
                _state = PARSER_STATE_IDLE;
            } else {
                substate_flags |= SUBSTATE_FLAG_TRANSITION;
            }
            break;
        case PARSER_STATE_LUT:
        case PARSER_STATE_LUT_WIRE:
        case PARSER_STATE_MULTIMODE:
        case PARSER_STATE_CUSTOM:
            if (_substate == PARSER_SUBSTATE_NONE) {
                _cur_instance = nullptr;
                _cur_lut = nullptr;
                _state = PARSER_STATE_BLOCK;
            } else {
                substate_flags |= SUBSTATE_FLAG_TRANSITION;
            }
            break;
        case PARSER_STATE_LUT_INNER:
            if (_substate == PARSER_SUBSTATE_NONE) {
                _state = PARSER_STATE_LUT;
            } else {
                substate_flags |= SUBSTATE_FLAG_TRANSITION;
            }
            break;
        case PARSER_STATE_MULTIMODE_INNER:
            if (_substate == PARSER_SUBSTATE_NONE) {
                _state = PARSER_STATE_MULTIMODE;
            } else {
                substate_flags |= SUBSTATE_FLAG_TRANSITION;
            }
            break;
        default:
            ERROR("[PACK] Invalid parser state");
            _state = PARSER_STATE_INTERNAL_ERROR;
            return;
    }

    if ( !(substate_flags & SUBSTATE_FLAG_TRANSITION) ) {
        return;
    }

    switch (_substate) {
        case PARSER_SUBSTATE_INPUTS:
        case PARSER_SUBSTATE_OUTPUTS:
        case PARSER_SUBSTATE_CLOCKS:
            _substate = PARSER_SUBSTATE_NONE;
            break;
        case PARSER_SUBSTATE_IGNORE:
            _ignore_level -= 1;
            if (0 == _ignore_level) {
                _substate = PARSER_SUBSTATE_NONE;
            }
            break;
        case PARSER_SUBSTATE_INPUT_PORT:
            if (_state == PARSER_STATE_LUT ||
                    _state == PARSER_STATE_LUT_WIRE ||
                    _state == PARSER_STATE_MULTIMODE ||
                    _state == PARSER_STATE_CUSTOM) {
                auto connections = _process_port_connections();
                _select_port_connections(connections);
                if (_state == PARSER_STATE_LUT_WIRE) {
                    _configure_lut(_process_lut_wire(connections));
                }
            }
            _cur_port = nullptr;
            _substate = PARSER_SUBSTATE_INPUTS;
            break;
        case PARSER_SUBSTATE_ROTATION:
            _configure_lut(_process_lut_rotation());
            _cur_port = nullptr;
            _substate = PARSER_SUBSTATE_INPUTS;
            break;
        case PARSER_SUBSTATE_OUTPUT_PORT:
            if (_state == PARSER_STATE_BLOCK) {
                _select_port_connections(_process_port_connections());
            }
            _cur_port = nullptr;
            _substate = PARSER_SUBSTATE_OUTPUTS;
            break;
        case PARSER_SUBSTATE_CLOCK_PORT:
            if (_state == PARSER_STATE_MULTIMODE ||
                    _state == PARSER_STATE_CUSTOM) {
                _select_port_connections(_process_port_connections());
            }
            _cur_port = nullptr;
            _substate = PARSER_SUBSTATE_CLOCKS;
            break;
        default:
            ERROR("[PACK] Invalid parser sub-state");
            _state = PARSER_STATE_INTERNAL_ERROR;
            return;
    }
}

void AbstractPackingManager::_xml_character_data_handler(const string & data) {
    switch (_substate) {
        case PARSER_SUBSTATE_INPUT_PORT:
        case PARSER_SUBSTATE_OUTPUT_PORT:
        case PARSER_SUBSTATE_CLOCK_PORT:
        case PARSER_SUBSTATE_ROTATION:
            _buffer.append(data);
            break;
        default:
            break;
    }
}

void AbstractPackingManager::_enter_block(const AbstractPackingManager::AttributeMap & attrs) {
    // get the block type of this instance
    const auto type_it = attrs.find(_Constants::str_instance);
    if (type_it == attrs.end()) {
        ERROR("[PACK] {}:{} Expecting 'instance' attribute in <block> element", _filename, _lineno);
        _state = PARSER_STATE_FORMAT_ERROR;
        return;
    }
    const auto & raw_instance = type_it->second;

    // use regex to extract the block type
    smatch type_matched;
    if (!regex_match(raw_instance, type_matched, _Constants::regex_instance)) {
        ERROR("[PACK] {}:{} 'instance' attribute does not match with regex: {}", _filename, _lineno, raw_instance);
        _state = PARSER_STATE_FORMAT_ERROR;
        return;
    }
    const string & type = type_matched[1];

    _cur_block = _config_db->get_block(type);
    if (!_cur_block) {
        ERROR("[PACK] {}:{} No config database for block '{}'", _filename, _lineno, type);
        _state = PARSER_STATE_MISSING_IN_CONFIG_DB;
        return;
    }

    _state = PARSER_STATE_BLOCK;
    _substate = PARSER_SUBSTATE_NONE;

    _enter_block_impl(attrs);
}

void AbstractPackingManager::_enter_instance(const AbstractPackingManager::AttributeMap & attrs) {
    // get the instance type of this instance
    const auto type_it = attrs.find(_Constants::str_instance);
    if (type_it == attrs.end()) {
        ERROR("[PACK] {}:{} Expecting 'instance' attribute in <block> element", _filename, _lineno);
        _state = PARSER_STATE_FORMAT_ERROR;
        return;
    }
    const auto & raw_instance = type_it->second;

    // use regex to extract the block type
    smatch type_matched;
    if (!regex_match(raw_instance, type_matched, _Constants::regex_instance)) {
        ERROR("[PACK] {}:{} 'instance' attribute does not match with regex: {}", _filename, _lineno, raw_instance);
        _state = PARSER_STATE_FORMAT_ERROR;
        return;
    }
    const string & type = type_matched[1];

    _cur_instance = _cur_block->get_instance(type);
    if (!_cur_instance) {
        ERROR("[PACK] {}:{} No config database for instance '{}'", _filename, _lineno, type);
        _state = PARSER_STATE_MISSING_IN_CONFIG_DB;
        return;
    }

    // get the name of this instance
    auto name_it = attrs.find(_Constants::str_name);
    if (name_it == attrs.end()) {
        ERROR("[PACK] {}:{} Expecting 'name' attribute in <block> element", _filename, _lineno);
        _state = PARSER_STATE_FORMAT_ERROR;
        return;
    }
    auto & name = name_it->second; 

    switch (_cur_instance->get_type()) {
        case common::Instance::LUT:
            _enter_lut(name, attrs);
            break;
        case common::Instance::MULTIMODE:
            _enter_multimode(name, attrs);
            break;
        case common::Instance::NON_CONFIGURABLE:
            _enter_custom(name, attrs);
            break;
        default:
            ERROR("[PACK] {}:{} Invalid config type", _filename, _lineno);
            _state = PARSER_STATE_INTERNAL_ERROR;
            return;
    }
}

void AbstractPackingManager::_enter_lut(const string & name,
        const AbstractPackingManager::AttributeMap & attrs) {
    if (_Constants::str_open.compare(name) == 0) {
        auto mode_it = attrs.find(_Constants::str_mode);
        if (mode_it == attrs.end() || _Constants::str_wire.compare(mode_it->second) != 0) {
            TRACE("[PACK] {}:{} Unused LUT", _filename, _lineno);
            _state = PARSER_STATE_LUT;
        } else {
            TRACE("[PACK] {}:{} LUT used as wire", _filename, _lineno);
            _state = PARSER_STATE_LUT_WIRE;
        }
    } else {
        _cur_lut = _synth_mgr->get_lut(name);
        if (!_cur_lut) {
            ERROR("[PACK] {}:{} No lut instance named '{}'", _filename, _lineno, name);
            _state = PARSER_STATE_MISSING_IN_SYNTH_MGR;
            return;
        }
        _state = PARSER_STATE_LUT;
    }
    _substate = PARSER_SUBSTATE_NONE;
    _enter_lut_impl(name, attrs);
}

void AbstractPackingManager::_enter_multimode(const string & name,
        const AbstractPackingManager::AttributeMap & attrs) {
    if (_Constants::str_open.compare(name) == 0) {
        TRACE("[PACK] {}:{} Unused instance", _filename, _lineno);
        _state = PARSER_STATE_MULTIMODE;
        _substate = PARSER_SUBSTATE_NONE;
        _enter_multimode_impl(name, attrs);
    } else {
        // get the mode of this multi-mode model instance
        auto mode_it = attrs.find(_Constants::str_mode);
        if (mode_it == attrs.end()) {
            ERROR("[PACK] {}:{} Expecting 'mode' attribute in <block> element", _filename, _lineno);
            _state = PARSER_STATE_FORMAT_ERROR;
            return;
        }
        auto & mode = mode_it->second;

        _state = PARSER_STATE_MULTIMODE;
        _substate = PARSER_SUBSTATE_NONE;
        _enter_multimode_impl(name, attrs);
        _select_mode(mode);
    }
}

void AbstractPackingManager::_enter_custom(const string & name,
        const AbstractPackingManager::AttributeMap & attrs) {
    if (_Constants::str_open.compare(name) == 0) {
        TRACE("[PACK] {}:{} Unused instance", _filename, _lineno);
    }

    _state = PARSER_STATE_CUSTOM;
    _substate = PARSER_SUBSTATE_NONE;

    _enter_custom_impl(name, attrs);
}

void AbstractPackingManager::_enter_port(const AbstractPackingManager::AttributeMap & attrs) {
    // get the name of this port
    auto name_it = attrs.find(_Constants::str_name);
    if (name_it == attrs.end()) {
        ERROR("[PACK] {}:{} Expecting 'name' attribute in <port> element", _filename, _lineno);
        _state = PARSER_STATE_FORMAT_ERROR;
        return;
    }
    auto & name = name_it->second; 

    if (_state == PARSER_STATE_BLOCK) {
        _cur_port = _cur_block->get_port(name);
    } else {
        _cur_port = _cur_instance->get_port(name);
    }

    if (!_cur_port) {
        ERROR("[PACK] {}:{} No config database for port '{}'", _filename, _lineno, name);
        _state = PARSER_STATE_MISSING_IN_CONFIG_DB;
        return;
    }

    _enter_port_impl(attrs);
}

vector<string> AbstractPackingManager::_process_port_connections() {
    auto tokens = split(_buffer, " ");
    _buffer.clear();
    for (unsigned int i = 0; i < tokens.size(); ++i) {
        if (_Constants::str_open.compare(tokens[i]) != 0) {
            smatch token_matched;
            if (!regex_match(tokens[i], token_matched, _Constants::regex_connection)) {
                CRITICAL("[PACK] 'port' content does not match regex: {}", tokens[i]);
                exit(1);
            }
            tokens[i] = token_matched[1];
        }
    }
    return tokens;
}

vector<bool> AbstractPackingManager::_process_lut_rotation() {
    auto tokens = split(_buffer, " ");
    _buffer.clear();
    vector<int> indices(tokens.size(), -1);
    for (unsigned int i = 0; i < tokens.size(); ++i) {
        if (_Constants::str_open.compare(tokens[i]) == 0) {
            indices[i] = -1;
        } else {
            indices[i] = stol(tokens[i]);
        }
    }
    return _cur_lut->rotate(indices);
}

vector<bool> AbstractPackingManager::_process_lut_wire(const vector<string> & connections) {
    unsigned int size = 1 << connections.size();
    vector<bool> bitstream(size, false);

    unsigned int key_index = 0;
    for (; key_index < connections.size(); ++key_index) {
        if (_Constants::str_open.compare(connections[key_index]) != 0) {
            break;
        }
    }
    if (key_index == connections.size()) {
        ERROR("[PACK] {}:{} LUT used as wire but all ports are open", _filename, _lineno);
        _state = PARSER_STATE_FORMAT_ERROR;
        return bitstream;
    }
    key_index = 1 << key_index;

    for (unsigned int i = 0; i < size; ++i) {
        bitstream[i] = (bool)(key_index & i);
    }
    return bitstream;
}

void AbstractPackingManager::_enter_block_impl(const AbstractPackingManager::AttributeMap & attrs) {
    (void)attrs;
}

void AbstractPackingManager::_enter_lut_impl(const string & name,
        const AbstractPackingManager::AttributeMap & attrs) {
    (void)name;
    (void)attrs;
}

void AbstractPackingManager::_enter_multimode_impl(const string & name,
        const AbstractPackingManager::AttributeMap & attrs) {
    (void)name;
    (void)attrs;
}

void AbstractPackingManager::_enter_custom_impl(const string & name,
        const AbstractPackingManager::AttributeMap & attrs) {
    (void)name;
    (void)attrs;
}

void AbstractPackingManager::_enter_port_impl(const AbstractPackingManager::AttributeMap & attrs) {
    (void)attrs;
}
