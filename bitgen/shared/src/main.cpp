#include "util.hpp"
#include "synth.hpp"
#include "configdb.hpp"
#include "pack.hpp"
#include "bitstream.hpp"

#include <iostream>
#include <string>
#include <cstdlib>
#include <getopt.h>

using namespace std;

int main(int argc, char* argv[]) {
    // parse program arguments
    string filename_configdb,
           filename_blif,
           filename_net,
           filename_place,
           filename_route,
           filename_memh;

    unsigned int memh_width = 16;

    logger = spdlog::stdout_color_st("stdout");
    logger->set_pattern("[%D %T] [%^%l%$] %v");
    string verbose("info");

    while (true) {
        static struct option long_options[] = {
            {"verbose",                required_argument, 0, 'v'},
            {"config_db",              required_argument, 0, 'c'},
            {"blif",                   required_argument, 0, 'b'},
            {"net",                    required_argument, 0, 'n'},
            {"place",                  required_argument, 0, 'p'},
            {"route",                  required_argument, 0, 'r'},
            {"output_memh",            optional_argument, 0, 'm'},
            {"memh_width",             optional_argument, 0, 'w'},
            {0,                        0,                 0, 0  }
        };
        int option_index = 0,
            c = getopt_long(argc, argv, "v:c:b:n:p:r:", long_options, &option_index);

        if (c == -1) {
            break;
        }

        switch (c) {
            case 0:
                break;
            case 'm':
                filename_memh = string(optarg);
                break;
            case 'w':
                memh_width = stoul(optarg);
                break;
            case 'v':
                verbose = string(optarg);
                break;
            case 'c':
                filename_configdb = string(optarg);
                break;
            case 'b':
                filename_blif = string(optarg);
                break;
            case 'n':
                filename_net = string(optarg);
                break;
            case 'p':
                filename_place = string(optarg);
                break;
            case 'r':
                filename_route = string(optarg);
                break;
            case '?':
                break;
            default:
                return 1;
        }
    }

    if (verbose.compare("trace") == 0) {
        spdlog::set_level(spdlog::level::trace);
    } else if (verbose.compare("debug") == 0) {
        spdlog::set_level(spdlog::level::debug);
    } else if (verbose.compare("info") == 0) {
        spdlog::set_level(spdlog::level::info);
    } else if (verbose.compare("warn") == 0) {
        spdlog::set_level(spdlog::level::warn);
    } else if (verbose.compare("err") == 0) {
        spdlog::set_level(spdlog::level::err);
    } else if (verbose.compare("critical") == 0) {
        spdlog::set_level(spdlog::level::critical);
    } else if (verbose.compare("off") == 0) {
        spdlog::set_level(spdlog::level::off);
    } else {
        cerr << "Invalid verbose level. Valid options are: "
            << "trace, debug, info, warn, err, critical, off" << endl;
        return 1;
    }

    // check and report input files
    bool inputs_valid = true;
    INFO("====== report input files ======");

    // config database
    if (filename_configdb.empty()) {
        ERROR("Missing input file: config database. "
                "Used '-c FILENAME' or '--config_db FILENAME' to specify the input file.");
        inputs_valid = false;
    } else {
        INFO("[FILE] Config database: {}", filename_configdb);
    }

    // blif
    if (filename_blif.empty()) {
        ERROR("Missing input file: blif (synthesis result). "
                "Use '-b FILENAME' or '--blif FILENAME' to specify the input file.");
        inputs_valid = false;
    } else {
        INFO("[FILE] BLIF (synthesis result): {}", filename_blif);
    }

    // net
    if (filename_net.empty()) {
        ERROR("Missing input file: net (packing result). "
                "Use '-n FILENAME' or '--net FILENAME' to specify the input file.");
        inputs_valid = false;
    } else {
        INFO("[FILE] Net (packing result): {}", filename_net);
    }

    // place
    if (filename_place.empty()) {
        ERROR("Missing input file: place (placement result). "
                "Use '-p FILENAME' or '--place FILENAME' to specify the input file.");
        inputs_valid = false;
    } else {
        INFO("[FILE] Place (placement result): {}", filename_place);
    }

    // route
    if (filename_route.empty()) {
        ERROR("Missing input file: route (routing result). "
                "Use '-r FILENAME' or '--route FILENAME' to specify the input file.");
        inputs_valid = false;
    } else {
        INFO("[FILE] Route (routing result): {}", filename_route);
    }
    
    if (!inputs_valid) {
        return 1;
    }

    // parse the config database
    INFO("====== parse config database ======");
    ConfigDatabase config_db;
    if (config_db.parse_database(filename_configdb)) {
        return 1;
    }
    // report config database
    INFO("====== report config database ======");
    for (const auto & it : config_db.get_blocks()) {
        INFO("[CONFIG] Block({})", it.first);
    }
    INFO("====== config database parsed and established ======");

    // analyze the synthesized design
    INFO("====== analyze synthesized design ======");
    SynthResultManager syn_mgr;
    if (syn_mgr.parse_blif(filename_blif)) {
        return 1;
    }
    // report lut instances
    INFO("====== report lut instances ======");
    for (const auto & it : syn_mgr.get_luts()) {
        INFO("[BLIF] LUT instance({}): {}", it.first, bitstream_to_string(it.second.get_bitstream()));
    }
    INFO("====== synthesized design analyzed ======");

    // parse packing result
    INFO("====== parse packing result ======");
    auto pack_mgr_ptr = AbstractPackingManager::create_packing_manager(&config_db, &syn_mgr);
    if (pack_mgr_ptr->parse_packing_result(filename_net)) {
        return 1;
    }
    pack_mgr_ptr->report_block_instances();
    INFO("====== packing result parsed ======");

    // start working on generating bitstream
    INFO("====== initializing bitstream ======");
    auto bitstream_ptr = AbstractBitstream::create_bitstream(&config_db, pack_mgr_ptr.get());
    INFO("====== parse placing result ======");
    if (bitstream_ptr->parse_placing_result(filename_place)) {
        return 1;
    }
    INFO("====== placing result parsed ======");
    bitstream_ptr->report_bitstream(64);
    INFO("====== parse routing result ======");
    if (bitstream_ptr->parse_routing_result(filename_route)) {
        return 1;
    }
    INFO("====== routing result parsed ======");
    bitstream_ptr->report_bitstream(64);

    if (!filename_memh.empty()) {
        if (bitstream_ptr->write_bitstream_memh(filename_memh, memh_width)) {
            return 1;
        }
    }

    return 0;
}
