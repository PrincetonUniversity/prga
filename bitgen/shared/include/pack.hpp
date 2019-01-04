#ifndef PACK_H
#define PACK_H

#include <memory>
#include <regex>

#include "synth.hpp"
#include "configdb.hpp"

class AbstractPackingManager {
    public:
        // constructor
        explicit AbstractPackingManager(const ConfigDatabase * config_db,
                const SynthResultManager * synth_mgr);

        enum ParsePackingResultStatus {
            PARSE_PACKING_RESULT_SUCCESS = 0,
            PARSE_PACKING_RESULT_NULL_CONFIG_DB,
            PARSE_PACKING_RESULT_NULL_SYNTH_MGR,
            PARSE_PACKING_RESULT_XML_ERROR,
            PARSE_PACKING_RESULT_FILE_ERROR,
            PARSE_PACKING_RESULT_FORMAT_ERROR,
            PARSE_PACKING_RESULT_INTERNAL_ERROR,
            PARSE_PACKING_RESULT_INCOMPLETE,
            PARSE_PACKING_RESULT_MISSING_IN_CONFIG_DB,
            PARSE_PACKING_RESULT_MISSING_IN_SYNTH_MGR,
        };

        // parse_packing_result: parse the packing result
        ParsePackingResultStatus parse_packing_result(const char * filename);
        ParsePackingResultStatus parse_packing_result(const std::string & filename);

        // create_packing_manager: create an implemented packing manager
        static std::unique_ptr<AbstractPackingManager> create_packing_manager(const ConfigDatabase * config_db,
                const SynthResultManager * synth_mgr);

        typedef std::map<std::string, std::string> AttributeMap;

        // _xml_start_element_handler: handles the beginning of a new element
        void _xml_start_element_handler(const std::string & name,
                const AttributeMap & attrs);

        // _xml_end_element_handler: handles the end of a new element
        void _xml_end_element_handler(const std::string & name);

        // _xml_character_data_handler: handles the character data
        void _xml_character_data_handler(const std::string & data);

    protected:
        // _process_port_connections: tokenize the character data buffer
        std::vector<std::string> _process_port_connections();

        // _process_lut_rotation: tokenize the character data buffer and rotate
        // the current lut instance
        std::vector<bool> _process_lut_rotation();

        // _process_lut_wire: tokenize the character data buffer and implement a
        // wire using a lut instance
        std::vector<bool> _process_lut_wire(const std::vector<std::string> & connections);

        // utility functions
        void _enter_block(const AttributeMap & attrs);
        void _enter_instance(const AttributeMap & attrs);
        void _enter_lut(const std::string & name,
                const AttributeMap & attrs);
        void _enter_multimode(const std::string & name,
                const AttributeMap & attrs);
        void _enter_custom(const std::string & name,
                const AttributeMap & attrs);
        void _enter_port(const AttributeMap & attrs);

    protected:
        // XML parser state info
        enum _XMLParserState {
            PARSER_STATE_INIT = 0,
            PARSER_STATE_IDLE,              // waiting for the next block
            PARSER_STATE_IGNORE,            // top-level inputs/outputs/clocks
            PARSER_STATE_DONE,              // parse done

            PARSER_STATE_BLOCK,             // top-level of a block

            PARSER_STATE_LUT,               // a lut instance
            PARSER_STATE_LUT_INNER,         // the inner instance of the lut instance

            PARSER_STATE_LUT_WIRE,          // LUT used as a buffer (should be rare if pack_pattern is used)

            PARSER_STATE_MULTIMODE,         // a multi-mode instance
            PARSER_STATE_MULTIMODE_INNER,   // the inner instances in a multi-mode model

            PARSER_STATE_CUSTOM,            // a custom (non-configurable) model instance

            // boundary between valid states and errorneous states
            PARSER_STATE_VALID_BOUNDARY,

            // Errorneous states
            PARSER_STATE_FORMAT_ERROR,
            PARSER_STATE_INTERNAL_ERROR,
            PARSER_STATE_MISSING_IN_CONFIG_DB,
            PARSER_STATE_MISSING_IN_SYNTH_MGR,
        };

        // XML parser sub-state
        enum _XMLParserSubState {
            PARSER_SUBSTATE_NONE = 0,       // no sub-state

            // ports sub-states
            PARSER_SUBSTATE_INPUTS,         // inputs of the parent element
            PARSER_SUBSTATE_INPUT_PORT,     // input port of the parent element
            PARSER_SUBSTATE_OUTPUTS,        // outputs of the parent element
            PARSER_SUBSTATE_OUTPUT_PORT,    // output port of the parent element
            PARSER_SUBSTATE_CLOCKS,         // clocks of the parent element
            PARSER_SUBSTATE_CLOCK_PORT,     // clock port of the parent element

            // lut-only sub-state
            PARSER_SUBSTATE_ROTATION,       // lut instance: <port_rotation_map>

            // leaf-instance sub-state
            PARSER_SUBSTATE_IGNORE,         // irrelevent elements
        };

        // XML parser constants
        class _Constants {
            public:
                static const std::string str_block;
                static const std::string str_name;
                static const std::string str_instance;
                static const std::string str_mode;
                static const std::string str_inputs;
                static const std::string str_outputs;
                static const std::string str_clocks;
                static const std::string str_port;
                static const std::string str_attributes;
                static const std::string str_parameters;
                static const std::string str_rotation;
                static const std::string str_extio_i;
                static const std::string str_extio_o;
                static const std::string str_open;
                static const std::string str_wire;

                static const std::regex regex_instance;
                static const std::regex regex_connection;
        };

        const ConfigDatabase * _config_db;
        const SynthResultManager * _synth_mgr;

        _XMLParserState _state;
        _XMLParserSubState _substate;
        const Block * _cur_block;
        const Instance * _cur_instance;
        const LutInstance * _cur_lut;
        const Port * _cur_port;

        int _ignore_level;
        std::string _buffer;
        std::string _filename;
        int _lineno;

    // implemented by sub-classes
    public:
        // report_block_instances: print block instances using info logger
        virtual void report_block_instances() const = 0;

        // get_num_block_instances: total number of block instances
        virtual int get_num_block_instances() const = 0;

    protected:
        virtual void _enter_block_impl(const AttributeMap & attrs);
        virtual void _enter_lut_impl(const std::string & name,
                const AttributeMap & attrs);
        virtual void _enter_multimode_impl(const std::string & name,
                const AttributeMap & attrs);
        virtual void _enter_custom_impl(const std::string & name,
                const AttributeMap & attrs);
        virtual void _enter_port_impl(const AttributeMap & attrs);
        virtual void _select_mode(const std::string & mode) = 0;
        virtual void _select_port_connections(const std::vector<std::string> & connections) = 0;
        virtual void _configure_lut(const std::vector<bool> & bitstream) = 0;
};

#endif /* PACK_H */
