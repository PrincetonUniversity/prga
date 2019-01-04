#ifndef CONFIGDB_H
#define CONFIGDB_H

#include <vector>
#include <map>
#include <memory>
#include <cstdint>

#include "common.pb.h"

#include <boost/graph/adjacency_list.hpp>

class PortBit {
    public:
        // constructor
        PortBit();

        // populate this object with the given protobuf message
        bool populate(const uint32_t & index,
                const prga::common::PortBit & bit);

        // get the configuration action of the given connection
        const prga::common::BitConnection::ConnectionAction * get_connection_action(const std::string & name) const;

        // check if this bit is hard-wired to its driver
        bool is_hardwired() const;

    private:
        unsigned int _index;
        std::map<std::string, std::unique_ptr<prga::common::BitConnection::ConnectionAction>> _connections;
};

class Port {
    public:
        // constructor
        Port();

        // populate this object with the given protobuf message
        bool populate(const prga::common::Port & port);

        // get the bit of the given index
        const PortBit * get_bit(const uint32_t & index) const;

    private:
        std::string _name;
        std::vector<PortBit> _bits;
};

class Instance {
    public:
        // constructor
        Instance();

        // populate this object with the given protobuf message
        bool populate(const prga::common::Instance & instance);

        // get the port of the given name
        const Port * get_port(const std::string & name) const;

        // get the configuration action of the given mode (Multi-mode only)
        const prga::common::Mode::ModeAction * get_mode_action(const std::string & name) const;

        // get the configuration action of this instance (LUT only)
        const prga::common::Instance::InstanceAction * get_action() const;

        // get the type of this instance
        const prga::common::Instance::Type & get_type() const;

    private:
        std::string _name;
        std::map<std::string, Port> _ports;
        std::map<std::string, std::unique_ptr<prga::common::Mode::ModeAction>> _modes;
        std::unique_ptr<prga::common::Instance::InstanceAction> _action;
        prga::common::Instance::Type _type;
};

class Block {
    public:
        // constructor
        Block();

        // populate this object with the given protobuf message
        bool populate(const prga::common::Block & block);

        // get the port of the given name
        const Port * get_port(const std::string & name) const;

        // get the sub-instance of the given name
        const Instance * get_instance(const std::string & name) const;

        // get the configuration action of this block
        const prga::common::Block::BlockAction * get_action() const;

    private:
        std::string _name;
        std::map<std::string, Port> _ports;
        std::map<std::string, Instance> _instances;
        std::unique_ptr<prga::common::Block::BlockAction> _action;
};

class ConfigDatabase {
    public:
        typedef struct _EdgeProperty {
            std::vector<prga::common::RoutingEdge::RoutingAction> actions;
        } EdgeProperty;

        typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::directedS,
                boost::property<boost::vertex_index_t, uint64_t>,
                boost::property<boost::edge_index_t, uint64_t, EdgeProperty>> Graph;

    public:
        // constructor:
        ConfigDatabase();

        enum ParseDatabaseReturnStatus {
            PARSE_DATABASE_STATUS_SUCCESS = 0,
            PARSE_DATABASE_STATUS_DATABASE_PARSED = 1,
            PARSE_DATABASE_STATUS_BAD_FILE = 2,
            PARSE_DATABASE_STATUS_BAD_PACKET_SIZE = 3,
            PARSE_DATABASE_STATUS_PACKET_INCOMPLETE = 4,
            PARSE_DATABASE_STATUS_PACKET_PROTOBUF_PARSE_FAILED = 5,
            PARSE_DATABASE_STATUS_BLOCK_NAME_CONFLICTION = 6,
            PARSE_DATABASE_STATUS_INVALID_BLOCK = 7
        };

        // parse_database: parse the database file
        ParseDatabaseReturnStatus parse_database(const char * filename);
        ParseDatabaseReturnStatus parse_database(const std::string & filename);

        // get_header_action: get the header action of the configuration database
        const prga::common::Header::HeaderAction * get_header_action() const;

        // get_signature: get the signature of the configuration database
        const uint64_t & get_signature() const;

        // get_block: get the block with the given name
        const Block * get_block(const std::string & name) const;

        // get_blocks: get the mapping from block name to block
        const std::map<std::string, Block> & get_blocks() const;

        // get_placement_actions: get the placement actions at the speicified
        // position
        const std::vector<prga::common::Placement::PlacementAction> * get_placement_actions(
                const uint32_t & x,
                const uint32_t & y,
                const uint32_t & subblock) const;

        // get_edge_actions: get the actions for the given edge
        const std::vector<prga::common::RoutingEdge::RoutingAction> * get_edge_actions(const uint64_t & src_node,
                const uint64_t & sink_node) const;

    private:
        bool _parse_finished;
        uint32_t _width;
        uint32_t _height;
        uint64_t _signature;

        std::unique_ptr<prga::common::Header::HeaderAction> _action;
        std::map<std::string, Block> _blocks;
        std::vector<std::vector<std::vector<std::vector<prga::common::Placement::PlacementAction>>>> _placement_actions;
        std::unique_ptr<Graph> _graph;
};

#endif /* CONFIGDB_H */
