#ifndef SYNTH_H
#define SYNTH_H

#include <vector>
#include <map>
#include <string>
#include <iostream>
#include <memory>

#include "blifparse.hpp"

class LutInstance {
    public:
        // constructor:
        LutInstance();

        enum LutParseStatus {
            LUT_PARSE_STATUS_SUCCESS = 0,
            LUT_PARSE_STATUS_NETS_AND_TRUTH_TABLE_MISMATCH,
            LUT_PARSE_STATUS_INCONSISTENT_TRUTH_TABLE_ENTRY,
            LUT_PARSE_STATUS_INVALID_TRUTH_TABLE_SYMBOL
        };

        // populate: populate this lut using the parsed .names tag in the blif file
        //  @argument num_nets: number of inputs + output of this LUT
        //  @argument so_cover: the truth table (see external library blifparse
        //      for more detail)
        LutParseStatus populate(const unsigned int & num_nets,
                const std::vector<std::vector<blifparse::LogicValue>> & so_cover);

        // rotate:
        //  @argument rotation_map: the rotation map as in VPR's .net file
        std::vector<bool> rotate(const std::vector<int> & rotation_map) const;

        // get_bitstream: get the bit vector of the contents of this LUT
        const std::vector<bool> & get_bitstream() const;

    private:
        std::vector<bool> _bitstream;
};

class SynthResultManager: public blifparse::Callback {
    public:
        // constructor: does nothing
        SynthResultManager();

        // get_lut: get the LUT instance with the given name
        //  @argument name:
        const LutInstance * get_lut(const std::string & name) const;

        // get_luts:
        const std::map<std::string, LutInstance> & get_luts() const;

        enum ParseBLIFReturnStatus {
            PARSE_BLIF_STATUS_SUCCESS = 0,
            PARSE_BLIF_STATUS_INCOMPLETE,
            PARSE_BLIF_STATUS_INVALID_STATE,
            PARSE_BLIF_STATUS_MULTIPLE_MODELS,
            PARSE_BLIF_STATUS_LUT_NAME_CONFLICTS,
            PARSE_BLIF_STATUS_PARSER_ERROR
        };

        // parse_blif: parse the BLIF file
        ParseBLIFReturnStatus parse_blif(const char * filename);
        ParseBLIFReturnStatus parse_blif(const std::string & filename);

        // implement methods required by blifparse::Callback
        void start_parse();
        void filename(std::string fname);
        void lineno(int line_num);
        void begin_model(std::string model_name);
        void inputs(std::vector<std::string> inputs);
        void outputs(std::vector<std::string> outputs);
        void names(std::vector<std::string> nets,
                std::vector<std::vector<blifparse::LogicValue> > so_cover);
        void latch(std::string input,
                std::string output,
                blifparse::LatchType type,
                std::string control,
                blifparse::LogicValue init);
        void subckt(std::string model,
                std::vector<std::string> ports,
                std::vector<std::string> nets);
        void blackbox();
        void end_model();
        void finish_parse();
        void parse_error(const int curr_lineno,
                const std::string & near_text,
                const std::string & msg);

    private:
        // BLIF parser state info
        enum _BLIFParserState {
            PARSER_STATE_INIT = 0,
            PARSER_STATE_PARSE_STARTED,
            PARSER_STATE_MODEL_BEGAN,
            PARSER_STATE_MODEL_ENDED,
            PARSER_STATE_PARSE_FINISHED,

            // boundary between valid states and errorneous states
            PARSER_STATE_VALID_BOUNDARY,

            // errorneous states
            PARSER_STATE_INVALID_STATE,
            PARSER_STATE_PARSE_ALREADY_STARTED,
            PARSER_STATE_MULTIPLE_MODELS,
            PARSER_STATE_LUT_NAME_CONFLICTS,
            PARSER_STATE_PARSER_ERROR
        };

    private:
        std::map<std::string, LutInstance> _luts;

        _BLIFParserState _state;
        int _lineno;
        std::string _filename;
};

#endif /* SYNTH_H */
