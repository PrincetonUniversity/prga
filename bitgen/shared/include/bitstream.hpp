#ifndef BITSTREAM_H
#define BITSTREAM_H

#include "pack.hpp"

class AbstractBitstream {
    public:
        // constructor
        explicit AbstractBitstream(const ConfigDatabase * config_db,
                const AbstractPackingManager * pack_mgr);

        // create_bitstream: create an implemented bitstream class object
        static std::unique_ptr<AbstractBitstream> create_bitstream(const ConfigDatabase * config_db,
                const AbstractPackingManager * pack_mgr);

        enum ParsePlacingResultStatus {
            PARSE_PLACING_RESULT_SUCCESS = 0,
            PARSE_PLACING_RESULT_NULL_CONFIG_DB,
            PARSE_PLACING_RESULT_NULL_PACK_MGR,
            PARSE_PLACING_RESULT_BAD_FILE,
            PARSE_PLACING_RESULT_PLACING_FAILED,
            PARSE_PLACING_RESULT_MISMATCH_WITH_PACKING_RESULT,
        };

        // parse_placing_result: parse the placing result
        ParsePlacingResultStatus parse_placing_result(const char * filename);
        ParsePlacingResultStatus parse_placing_result(const std::string & filename);

        enum ParseRoutingResultStatus {
            PARSE_ROUTING_RESULT_SUCCESS = 0,
            PARSE_ROUTING_RESULT_NULL_CONFIG_DB,
            PARSE_ROUTING_RESULT_BAD_FILE,
            PARSE_ROUTING_RESULT_ROUTING_FAILED,
            PARSE_ROUTING_RESULT_FORMAT_ERROR,
        };

        // parse_routing_result: parse the routing result
        ParseRoutingResultStatus parse_routing_result(const char * filename);
        ParseRoutingResultStatus parse_routing_result(const std::string & filename);

        // report_bitstream: print the bitstream using info logger
        virtual void report_bitstream(const size_t & bits_per_line) const = 0;

        enum WriteBitstreamStatus {
            WRITE_BITSTREAM_SUCCESS = 0,
            WRITE_BITSTREAM_BAD_FILE,
        };

        // write_bitstream_memh: write the bitstream in verilog memory file
        // format
        virtual WriteBitstreamStatus write_bitstream_memh(const char * filename,
                const unsigned int & width) const = 0;
        virtual WriteBitstreamStatus write_bitstream_memh(const std::string & filename,
                const unsigned int & width) const = 0;

    protected:
        const ConfigDatabase * _config_db;
        const AbstractPackingManager * _pack_mgr;

    protected:
        class _Constants {
            public:
                static const std::regex regex_placing_line;
                static const std::regex regex_routing_net_line;
                static const std::regex regex_routing_node_line;
                static const std::regex regex_routing_global_line;
                static const std::regex regex_routing_global_node_line;

                static const std::string str_source;
                static const std::string str_opin;
                static const std::string str_chanx;
                static const std::string str_chany;
                static const std::string str_ipin;
                static const std::string str_sink;
        };

        enum _RoutingParserState {
            ROUTING_PARSER_STATE_INIT = 0,
            ROUTING_PARSER_STATE_GLOBAL,
            ROUTING_PARSER_STATE_NET,
            ROUTING_PARSER_STATE_SOURCE,
            ROUTING_PARSER_STATE_OPIN,
            ROUTING_PARSER_STATE_SEGMENT,
            ROUTING_PARSER_STATE_IPIN,
            ROUTING_PARSER_STATE_SINK,
        };

    protected:
        // pure virtual functions to be implemented by sub-classes
        // _place_block_instance: place a packed block at a specific position
        virtual bool _place_block_instance(const std::string & block_name,
                const uint32_t & x,
                const uint32_t & y,
                const uint32_t & subblock) = 0;

        // _route_connection: route one connection between two nodes
        virtual bool _route_connection(const uint64_t & src_node,
                const uint64_t & sink_node) = 0;

};

#endif /* BITSTREAM_H */
