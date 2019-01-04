#include "util.hpp"
#include "configdb.hpp"

#include "google/protobuf/io/coded_stream.h"
#include "google/protobuf/io/zero_copy_stream_impl.h"

#include <boost/utility.hpp>
#include <fstream>
#include <climits>

using namespace std;
using namespace google::protobuf::io;
using namespace boost;
using namespace prga;

PortBit::PortBit(): _index(0), _connections() {}

bool PortBit::populate(const uint32_t & index,
        const common::PortBit & bit) {
    if (!_connections.empty()) {
        ERROR("[CONFIG] 'PortBit' object already populated");
        return false;
    }

    _index = index;

    for (int i = 0; i < bit.connections_size(); ++i) {
        const auto & conn = bit.connections(i);
        auto result = _connections.emplace(conn.input(),
                (conn.has_action()) ? new common::BitConnection::ConnectionAction(conn.action()): nullptr);
        if (!result.second) {
            ERROR("[CONFIG] Duplicated connections '{}' for 'PortBit' object", conn.input());
            return false;
        }
    }

    return true;
}

const common::BitConnection::ConnectionAction * PortBit::get_connection_action(const string & name) const {
    const auto it = _connections.find(name);
    if (it != _connections.end()) {
        return it->second.get();
    } else if (name.compare("open") == 0) {
        return nullptr;
    } else {
        ERROR("[CONFIG] Bit no. {} does not have connection '{}'", _index, name);
        return nullptr;
    }
}

bool PortBit::is_hardwired() const {
    return _connections.size() <= 1;
}

Port::Port(): _name(), _bits() {}

bool Port::populate(const common::Port & port) {
    if (!_bits.empty()) {
        ERROR("[CONFIG] 'Port' object already populated");
        return false;
    }

    _name = port.name();

    for (int i = 0; i < port.bits_size(); ++i) {
        _bits.emplace_back();
        if (!_bits.back().populate(i, port.bits(i))) {
            return false;
        }
    }

    return true;
}

const PortBit * Port::get_bit(const uint32_t & index) const {
    if (index < 0 || index >= _bits.size()) {
        ERROR("[CONFIG] Port '{}' does not have bit no. {}", _name, index);
        return nullptr;
    } else {
        return &(_bits[index]);
    }
}

Instance::Instance(): _name(), _ports(), _modes(), _action(), _type() {}

bool Instance::populate(const common::Instance & instance) {
    if (!(_ports.empty() && _modes.empty() && !_action)) {
        ERROR("[CONFIG] 'Instance' object already populated");
        return false;
    }

    _name = instance.name();

    // ports
    for (int i = 0; i < instance.ports_size(); ++i) {
        const auto & port = instance.ports(i);
        auto result = _ports.emplace(port.name(), Port());
        if (!result.second) {
            ERROR("[CONFIG] Duplicated port '{}' in instance '{}'", port.name(), _name);
            return false;
        } else if (!result.first->second.populate(port)) {
            return false;
        }
    }

    // modes
    for (int i = 0; i < instance.modes_size(); ++i) {
        const auto & mode = instance.modes(i);
        auto result = _modes.emplace(mode.name(), nullptr);
        if (!result.second) {
            ERROR("[CONFIG] Duplicated mode '{}' in instance '{}'", mode.name(), _name);
            return false;
        }
        if (mode.has_action()) {
            result.first->second.reset(new common::Mode::ModeAction(mode.action()));
        }
    }

    // action
    if (instance.has_action()) {
        _action.reset(new common::Instance::InstanceAction(instance.action()));
    }

    // type
    _type = instance.type();

    return true;
}

const Port * Instance::get_port(const string & name) const {
    const auto it = _ports.find(name);
    if (it != _ports.end()) {
        return &(it->second);
    } else {
        ERROR("[CONFIG] Instance '{}' does not have port '{}'", _name, name);
        return nullptr;
    }
}

const common::Mode::ModeAction * Instance::get_mode_action(const string & name) const {
    const auto it = _modes.find(name);
    if (it != _modes.end()) {
        return it->second.get();
    } else {
        ERROR("[CONFIG] Instance '{}' does not have mode '{}'", _name, name);
        return nullptr;
    }
}

const common::Instance::InstanceAction * Instance::get_action() const {
    return _action.get();
}

const common::Instance::Type & Instance::get_type() const {
    return _type;
}

Block::Block(): _name(), _ports(), _instances(), _action() {}

bool Block::populate(const common::Block & block) {
    if (!(_ports.empty() && _instances.empty() && !_action)) {
        ERROR("[CONFIG] 'Block' object already populated");
        return false;
    }

    _name = block.name();

    // ports
    for (int i = 0; i < block.ports_size(); ++i) {
        const auto & port = block.ports(i);
        auto result = _ports.emplace(port.name(), Port());
        if (!result.second) {
            ERROR("[CONFIG] Duplicated port '{}' in block '{}'", port.name(), _name);
            return false;
        } else if (!result.first->second.populate(port)) {
            return false;
        }
    }

    // instances
    for (int i = 0; i < block.instances_size(); ++i) {
        const auto & instance = block.instances(i);
        auto result = _instances.emplace(instance.name(), Instance());
        if (!result.second) {
            ERROR("[CONFIG] Duplicated instance '{}' in block '{}'", instance.name(), _name);
            return false;
        } else if (!result.first->second.populate(instance)) {
            return false;
        }
    }

    // action
    if (block.has_action()) {
        _action.reset(new common::Block::BlockAction(block.action()));
    }

    return true;
}

const Port * Block::get_port(const string & name) const {
    const auto it = _ports.find(name);
    if (it != _ports.end()) {
        return &(it->second);
    } else {
        ERROR("[CONFIG] Block '{}' does not have port '{}'", _name, name);
        return nullptr;
    }
}

const Instance * Block::get_instance(const string & name) const {
    const auto it = _instances.find(name);
    if (it != _instances.end()) {
        return &(it->second);
    } else {
        ERROR("[CONFIG] Block '{}' does not have instance '{}'", _name, name);
        return nullptr;
    }
}

const common::Block::BlockAction * Block::get_action() const {
    return _action.get();
}

ConfigDatabase::ConfigDatabase():
    _parse_finished(false), _width(0), _height(0), _signature(0), _action(),
    _blocks(), _placement_actions(), _graph()
{}

ConfigDatabase::ParseDatabaseReturnStatus ConfigDatabase::parse_database(const char * filename) {
    if (_parse_finished) {
        ERROR("[CONFIG] Config database already parsed");
        return PARSE_DATABASE_STATUS_DATABASE_PARSED;
    }

    int fd = open(filename, O_RDONLY);
    if (!fd) {
        ERROR("[CONFIG] Config database file error");
        return PARSE_DATABASE_STATUS_BAD_FILE;
    }

    unique_ptr<FileInputStream> zero_copy_stream(new FileInputStream(fd));
    zero_copy_stream->SetCloseOnDelete(true);

    unique_ptr<CodedInputStream> stream(new CodedInputStream(zero_copy_stream.get()));
    stream->SetTotalBytesLimit(INT_MAX, INT_MAX);

    uint64_t magic = 0;
    uint32_t packet_size = 0;
    string buffer;

    if (!stream->ReadLittleEndian64(&magic)) {
        ERROR("[CONFIG] Unable to read 64-bit magic number");
        return PARSE_DATABASE_STATUS_BAD_FILE;
    } else if (magic != 0x6d67666361677270) {
        ERROR("[CONFIG] '{}' is not a valid configuration database file (wrong magic number: {})", filename, magic);
        return PARSE_DATABASE_STATUS_BAD_FILE;
    }

    if (!stream->ReadLittleEndian32(&packet_size)) {
        ERROR("[CONFIG] Unable to read the header packet size");
        return PARSE_DATABASE_STATUS_BAD_PACKET_SIZE;
    }

    if (!stream->ReadString(&buffer, packet_size)) {
        ERROR("[CONFIG] Incomplete header packet in the config database");
        return PARSE_DATABASE_STATUS_PACKET_INCOMPLETE;
    }

    common::Header header;
    if (!header.ParseFromString(buffer)) {
        ERROR("[CONFIG] Header packet cannot be parsed by protobuf");
        return PARSE_DATABASE_STATUS_PACKET_PROTOBUF_PARSE_FAILED;
    }

    TRACE("[CONFIG] Size: {} x {}, node_size: {}",
            header.width(), header.height(), header.node_size());

    _width = header.width();
    _height = header.height();
    _signature = header.signature();
    _graph.reset(new Graph(header.node_size()));
    auto & graph = *(_graph.get());

    if (header.has_action()) {
        _action.reset(new common::Header::HeaderAction(header.action()));
    }

    vector<vector<vector<vector<common::Placement::PlacementAction>>>>(_width,
            vector<vector<vector<common::Placement::PlacementAction>>>(_height,
                vector<vector<common::Placement::PlacementAction>>())).swap(_placement_actions);

    while (true) {
        if (!stream->ReadLittleEndian32(&packet_size)) {
            ERROR("[CONFIG] Unexpected end of config database");
            return PARSE_DATABASE_STATUS_BAD_FILE;
        }

        if (packet_size == 0) {
            break;
        } else {
            TRACE("[CONFIG] Next packet size: {}", packet_size);
        }

        if (!stream->ReadString(&buffer, packet_size)) {
            ERROR("[CONFIG] Incomplete packet in the config database");
            return PARSE_DATABASE_STATUS_PACKET_INCOMPLETE;
        }
        common::Packet packet;
        if (!packet.ParseFromString(buffer)) {
            ERROR("[CONFIG] Chunk cannot be parsed by protobuf");
            return PARSE_DATABASE_STATUS_PACKET_PROTOBUF_PARSE_FAILED;
        }
        TRACE("[CONFIG] Packet received: \n{}", packet.DebugString());
        // TRACE("[CONFIG] # blocks in the packet: {}", packet.blocks_size());
        for (int i = 0; i < packet.blocks_size(); ++i) {
            const auto & block = packet.blocks(i);
            auto result = _blocks.emplace(block.name(), Block());
            if (!result.second) {
                ERROR("[CONFIG] Duplicated block '{}'", block.name());
                return PARSE_DATABASE_STATUS_BLOCK_NAME_CONFLICTION;
            } else if (!result.first->second.populate(block)) {
                return PARSE_DATABASE_STATUS_INVALID_BLOCK;
            }
        }
        // TRACE("[CONFIG] # placements in the packet: {}", packet.placements_size());
        for (int i = 0; i < packet.placements_size(); ++i) {
            const auto & placement = packet.placements(i);
            if (placement.x() >= _width || placement.y() >= _height) {
                ERROR("[CONFIG] Placement rule ({}, {}) beyond the grid ({} x {})",
                        placement.x(), placement.y(), _width, _height);
                return PARSE_DATABASE_STATUS_BAD_FILE;
            }
            auto & placements = _placement_actions[placement.x()][placement.y()];
            if (placement.subblock() >= placements.size()) {
                placements.resize(placement.subblock() + 1);
            }
            if (placement.has_action()) {
                placements[placement.subblock()].emplace_back(placement.action());
            }
        }
        // TRACE("[CONFIG] # edges in the packet: {}", packet.edges_size());
        for (int i = 0; i < packet.edges_size(); ++i) {
            const auto & edge = packet.edges(i);

            graph_traits<Graph>::edge_descriptor e;
            bool has_edge;
            tie(e, has_edge) = add_edge(edge.src(), edge.sink(), graph);
            if (edge.has_action()) {
                graph[e].actions.emplace_back(edge.action());
            }
        }
    }

    _parse_finished = true;

    INFO("[CONFIG] # blocks in config database: {}", _blocks.size());
    INFO("[CONFIG] # nodes in config database: {}", num_vertices(graph));
    INFO("[CONFIG] # edges in config database: {}", num_edges(graph));

    return PARSE_DATABASE_STATUS_SUCCESS;
}

ConfigDatabase::ParseDatabaseReturnStatus ConfigDatabase::parse_database(const string & filename) {
    return parse_database(filename.c_str());
}

const common::Header::HeaderAction * ConfigDatabase::get_header_action() const {
    return _action.get();
}

const uint64_t & ConfigDatabase::get_signature() const {
    return _signature;
}

const Block * ConfigDatabase::get_block(const string & name) const {
    const auto it = _blocks.find(name);
    return (it == _blocks.end()) ? nullptr : &(it->second);
}

const map<string, Block> & ConfigDatabase::get_blocks() const {
    return _blocks;
}

const vector<common::Placement::PlacementAction> * ConfigDatabase::get_placement_actions(
        const uint32_t & x,
        const uint32_t & y,
        const uint32_t & subblock) const {
    if (x >= _width || y >= _height) {
        ERROR("[CONFIG] Querying placement actions at position ({}, {}) beyond the grid ({} x {})",
                x, y, _width, _height);
        return nullptr;
    }

    const auto & placements = _placement_actions[x][y];
    if (placements.size() == 0) {
        // either this placement does not matter to bitstream, or this tile is empty.
        return nullptr;
    }

    if (subblock >= placements.size()) {
        ERROR("[CONFIG] Querying placement actions at position ({}, {}) for subblock {} beyond number of subblocks ({})",
                x, y, subblock, placements.size());
        return nullptr;
    } else {
        return &(placements[subblock]);
    }
}

const vector<common::RoutingEdge::RoutingAction> * ConfigDatabase::get_edge_actions(const uint64_t & src_node,
        const uint64_t & sink_node) const {
    if (nullptr == _graph.get()) {
        ERROR("[CONFIG] Routing graph is null");
        return nullptr;
    }
    auto & graph = *(_graph.get());

    auto e = edge(vertex(src_node, graph), vertex(sink_node, graph), graph);
    if (!e.second) {
        ERROR("[CONFIG] No edge from node {} to node {}", src_node, sink_node);
        return nullptr;
    }
    return &(graph[e.first].actions);
}
