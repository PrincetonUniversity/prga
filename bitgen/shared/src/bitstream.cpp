#include <fstream>
#include <cstdint>
#include <set>

#include "util.hpp"
#include "bitstream.hpp"

using namespace std;

AbstractBitstream::AbstractBitstream(const ConfigDatabase * config_db,
        const AbstractPackingManager * pack_mgr):
    _config_db(config_db), _pack_mgr(pack_mgr)
{
}

AbstractBitstream::ParsePlacingResultStatus AbstractBitstream::parse_placing_result(const char * filename) {
    if (nullptr == _config_db) {
        ERROR("[PLACE] Config database is nullptr");
        return PARSE_PLACING_RESULT_NULL_CONFIG_DB;
    }

    if (nullptr == _pack_mgr) {
        ERROR("[PLACE] Packing result manager is nullptr");
        return PARSE_PLACING_RESULT_NULL_PACK_MGR;
    }

    ifstream stream(filename);
    if (!stream) {
        ERROR("[PLACE] Placing result file error: {}", filename);
        return PARSE_PLACING_RESULT_BAD_FILE;
    }

    string buffer;
    int placed = 0, lineno = 0;
    while (getline(stream, buffer)) {
        ++lineno;
        smatch line_matched;
        if (!regex_match(buffer, line_matched, _Constants::regex_placing_line)) {
            continue;
        }
        const string & name = line_matched[1];
        uint32_t x = stoul(line_matched[2]),
                y = stoul(line_matched[3]),
                subblock = stoul(line_matched[4]);
        TRACE("[PLACE] {}:{} Placing '{}' at ({}, {}, {})", filename, lineno, name, x, y, subblock);
        if (!_place_block_instance(name, x, y, subblock)) {
            return PARSE_PLACING_RESULT_PLACING_FAILED;
        }
        ++placed;
    }

    if (placed != _pack_mgr->get_num_block_instances()) {
        ERROR("[PLACE] {} blocks found in packing result, {} placed",
                _pack_mgr->get_num_block_instances(), placed);
        return PARSE_PLACING_RESULT_MISMATCH_WITH_PACKING_RESULT;
    } else {
        TRACE("[PLACE] {} blocks placed", placed);
    }

    return PARSE_PLACING_RESULT_SUCCESS;
}

AbstractBitstream::ParsePlacingResultStatus AbstractBitstream::parse_placing_result(const string & filename) {
    return parse_placing_result(filename.c_str());
}

AbstractBitstream::ParseRoutingResultStatus AbstractBitstream::parse_routing_result(const char * filename) {
    if (nullptr == _config_db) {
        ERROR("[ROUTE] Config database is nullptr");
        return PARSE_ROUTING_RESULT_NULL_CONFIG_DB;
    }

    ifstream stream(filename);
    if (!stream) {
        ERROR("[ROUTE] Routing result file error: {}", filename);
        return PARSE_ROUTING_RESULT_BAD_FILE;
    }

    _RoutingParserState state = ROUTING_PARSER_STATE_INIT;

    string buffer, cur_net;
    smatch line_matched;
    int routed = 0, lineno = 0;
    uint64_t prev_node, cur_node;
    set<uint64_t> connected;
    while (getline(stream, buffer)) {
        ++lineno;
        if (buffer.find_first_not_of(" \t\n\v\f\r") == string::npos) {
            continue;
        }
        switch (state) {
            case ROUTING_PARSER_STATE_INIT:
                if (regex_match(buffer, line_matched, _Constants::regex_routing_net_line)) {
                    TRACE("[ROUTE] {}:{} Parsing net {}", filename, lineno, cur_net);
                    cur_net = line_matched[1];
                    state = ROUTING_PARSER_STATE_NET;
                } else if (regex_match(buffer, line_matched, _Constants::regex_routing_global_line)) {
                    TRACE("[ROUTE] {}:{} Parsing global net {}", filename, lineno, cur_net);
                    cur_net = line_matched[1];
                    state = ROUTING_PARSER_STATE_GLOBAL;
                } else {
                    TRACE("[ROUTE] {}:{} Ignoring random text", filename, lineno);
                }
                break;
            case ROUTING_PARSER_STATE_GLOBAL:
                if (regex_match(buffer, line_matched, _Constants::regex_routing_net_line)) {
                    TRACE("[ROUTE] {}:{} Parsing net {}", filename, lineno, cur_net);
                    cur_net = line_matched[1];
                    state = ROUTING_PARSER_STATE_NET;
                } else if (regex_match(buffer, line_matched, _Constants::regex_routing_global_line)) {
                    TRACE("[ROUTE] {}:{} Parsing global net {}", filename, lineno, cur_net);
                    cur_net = line_matched[1];
                    state = ROUTING_PARSER_STATE_GLOBAL;
                } else if (regex_match(buffer, line_matched, _Constants::regex_routing_global_node_line)) {
                    break;
                } else {
                    ERROR("[ROUTE] {}:{} Expecting global node or next net", filename, lineno);
                    return PARSE_ROUTING_RESULT_FORMAT_ERROR;
                }
                break;
            case ROUTING_PARSER_STATE_NET:
                connected.clear();
                if (regex_match(buffer, line_matched, _Constants::regex_routing_node_line)) {
                    if (_Constants::str_source.compare(line_matched[2]) == 0) {
                        state = ROUTING_PARSER_STATE_SOURCE;
                    } else {
                        ERROR("[ROUTE] {}:{} Expecting 'SOURCE' node, got '{}'", filename, lineno, line_matched[2].str());
                        return PARSE_ROUTING_RESULT_FORMAT_ERROR;
                    }
                    prev_node = stoull(line_matched[1]);
                    connected.insert(prev_node);
                } else {
                    ERROR("[ROUTE] {}:{} Expecting 'SOURCE' node", filename, lineno);
                    return PARSE_ROUTING_RESULT_FORMAT_ERROR;
                }
                break;
            case ROUTING_PARSER_STATE_SOURCE:
                if (regex_match(buffer, line_matched, _Constants::regex_routing_node_line)) {
                    if (_Constants::str_opin.compare(line_matched[2]) == 0) {
                        state = ROUTING_PARSER_STATE_OPIN;
                    } else {
                        ERROR("[ROUTE] {}:{} Expecting 'OPIN' node, got '{}'", filename, lineno, line_matched[2].str());
                        return PARSE_ROUTING_RESULT_FORMAT_ERROR;
                    }
                    cur_node = stoull(line_matched[1]);
                    if (!_route_connection(prev_node, cur_node)) {
                        return PARSE_ROUTING_RESULT_ROUTING_FAILED;
                    }
                    connected.insert(cur_node);
                    prev_node = cur_node;
                } else {
                    ERROR("[ROUTE] {}:{} Expecting 'OPIN' node", filename, lineno);
                    return PARSE_ROUTING_RESULT_FORMAT_ERROR;
                }
                break;
            case ROUTING_PARSER_STATE_OPIN:
            case ROUTING_PARSER_STATE_SEGMENT:
                if (regex_match(buffer, line_matched, _Constants::regex_routing_node_line)) {
                    if (_Constants::str_chanx.compare(line_matched[2]) == 0 ||
                            _Constants::str_chany.compare(line_matched[2]) == 0) {
                        state = ROUTING_PARSER_STATE_SEGMENT;
                    } else if (_Constants::str_ipin.compare(line_matched[2]) == 0) {
                        state = ROUTING_PARSER_STATE_IPIN;
                    } else {
                        ERROR("[ROUTE] {}:{} Expecting 'CHANX', 'CHANY', or 'IPIN' node, got '{}'", filename, lineno, line_matched[2].str());
                        return PARSE_ROUTING_RESULT_FORMAT_ERROR;
                    }
                    cur_node = stoull(line_matched[1]);
                    if (!_route_connection(prev_node, cur_node)) {
                        return PARSE_ROUTING_RESULT_ROUTING_FAILED;
                    }
                    connected.insert(cur_node);
                    prev_node = cur_node;
                } else {
                    ERROR("[ROUTE] {}:{} Expecting 'CHANX', 'CHANY', or 'IPIN' node", filename, lineno);
                    return PARSE_ROUTING_RESULT_FORMAT_ERROR;
                }
                break;
            case ROUTING_PARSER_STATE_IPIN:
                if (regex_match(buffer, line_matched, _Constants::regex_routing_node_line)) {
                    if (_Constants::str_sink.compare(line_matched[2]) == 0) {
                        state = ROUTING_PARSER_STATE_SINK;
                    } else {
                        ERROR("[ROUTE] {}:{} Expecting 'SINK' node, got '{}'", filename, lineno, line_matched[2].str());
                        return PARSE_ROUTING_RESULT_FORMAT_ERROR;
                    }
                    cur_node = stoull(line_matched[1]);
                    if (!_route_connection(prev_node, cur_node)) {
                        return PARSE_ROUTING_RESULT_ROUTING_FAILED;
                    }
                    connected.insert(cur_node);
                    prev_node = cur_node;
                } else {
                    ERROR("[ROUTE] {}:{} Expecting 'SINK' node", filename, lineno);
                    return PARSE_ROUTING_RESULT_FORMAT_ERROR;
                }
                break;
            case ROUTING_PARSER_STATE_SINK:
                if (regex_match(buffer, line_matched, _Constants::regex_routing_net_line)) {
                    ++routed;
                    TRACE("[ROUTE] {}:{} Parsing net {}", filename, lineno, cur_net);
                    cur_net = line_matched[1];
                    state = ROUTING_PARSER_STATE_NET;
                } else if (regex_match(buffer, line_matched, _Constants::regex_routing_global_line)) {
                    ++routed;
                    TRACE("[ROUTE] {}:{} Parsing global net {}", filename, lineno, cur_net);
                    cur_net = line_matched[1];
                    state = ROUTING_PARSER_STATE_GLOBAL;
                } else if (regex_match(buffer, line_matched, _Constants::regex_routing_node_line)) {
                    if (_Constants::str_opin.compare(line_matched[2]) == 0) {
                        state = ROUTING_PARSER_STATE_OPIN;
                    } else if (_Constants::str_chanx.compare(line_matched[2]) == 0 ||
                            _Constants::str_chany.compare(line_matched[2]) == 0) {
                        state = ROUTING_PARSER_STATE_SEGMENT;
                    } else {
                        ERROR("[ROUTE] {}:{} Expecting 'OPIN', 'CHANX', or 'CHANY' node, got '{}'", filename, lineno, line_matched[2].str());
                        return PARSE_ROUTING_RESULT_FORMAT_ERROR;
                    }
                    prev_node = stoull(line_matched[1]);
                    if (connected.find(prev_node) == connected.end()) {
                        ERROR("[ROUTE] {}:{} Node '{}' is not connected in this net", filename, lineno, prev_node);
                        return PARSE_ROUTING_RESULT_FORMAT_ERROR;
                    }
                } else {
                    ERROR("[ROUTE] {}:{} Expecting 'OPIN', 'CHANX', or 'CHANY' node or next net", filename, lineno);
                    return PARSE_ROUTING_RESULT_FORMAT_ERROR;
                }
                break;
            default:
                ERROR("[ROUTE] Invalid parser state");
                return PARSE_ROUTING_RESULT_ROUTING_FAILED;
        }
    }

    TRACE("[ROUTE] # nets routed: {}", routed);

    return PARSE_ROUTING_RESULT_SUCCESS;
}

AbstractBitstream::ParseRoutingResultStatus AbstractBitstream::parse_routing_result(const string & filename) {
    return parse_routing_result(filename.c_str());
}

const regex AbstractBitstream::_Constants::regex_placing_line("^(\\S+)\\s+(\\d+)\\s+(\\d+)\\s+(\\d+)\\s+#\\d+$");
const regex AbstractBitstream::_Constants::regex_routing_net_line("^Net\\s+\\d+\\s+\\((\\S+)\\)$");
const regex AbstractBitstream::_Constants::regex_routing_node_line("^Node:\\s+(\\d+)\\s+(SOURCE|OPIN|CHANX|CHANY|IPIN|SINK)\\s+.*$");
const regex AbstractBitstream::_Constants::regex_routing_global_line("^Net\\s+\\d+\\s+\\((\\S+)\\):\\s+global\\s+net\\s+connecting:$");
const regex AbstractBitstream::_Constants::regex_routing_global_node_line(
    "^Block\\s+(\\S+)\\s+\\(#\\d+\\)\\s+at\\s+\\(\\d+,\\d+\\),\\s+Pin\\s+class\\s+\\d+\\.$");

const string AbstractBitstream::_Constants::str_source("SOURCE");
const string AbstractBitstream::_Constants::str_opin("OPIN");
const string AbstractBitstream::_Constants::str_chanx("CHANX");
const string AbstractBitstream::_Constants::str_chany("CHANY");
const string AbstractBitstream::_Constants::str_ipin("IPIN");
const string AbstractBitstream::_Constants::str_sink("SINK");
