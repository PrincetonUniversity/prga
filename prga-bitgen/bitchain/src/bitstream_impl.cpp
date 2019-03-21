#include <fstream>
#include <iomanip>

#include "util.hpp"
#include "pack_impl.hpp"
#include "bitstream_impl.hpp"
#include "bitchain.pb.h"

using namespace std;
using namespace prga;
using namespace boost;

unique_ptr<AbstractBitstream> AbstractBitstream::create_bitstream(const ConfigDatabase * config_db,
        const AbstractPackingManager * pack_mgr) {
    if (nullptr == config_db || nullptr == pack_mgr) {
        ERROR("[BITSTREAM] Config DB or packing manager is NULL");
        return unique_ptr<AbstractBitstream>();
    }

    if (config_db->get_signature() != 0xaf27dbd3ad76bbdd) {
        ERROR("[BITSTREAM] Wrong config database signature for bitchain configuration circuitry");
        return unique_ptr<AbstractBitstream>();
    }

    auto header_ptr = config_db->get_header_action();
    if (!header_ptr || !header_ptr->HasExtension(bitchain::Ext::total_size)) {
        ERROR("[BITSTREAM] Unknown total bitstream size");
        return unique_ptr<AbstractBitstream>();
    }

    return unique_ptr<AbstractBitstream>(dynamic_cast<AbstractBitstream *>(new Bitstream(config_db, pack_mgr)));
}

Bitstream::Bitstream(const ConfigDatabase * config_db,
        const AbstractPackingManager * pack_mgr):
    AbstractBitstream(config_db, pack_mgr), _bitstream()
{
    auto header_ptr = _config_db->get_header_action();
    if (header_ptr) {
        if (header_ptr->HasExtension(bitchain::Ext::total_size)) {
            const auto & size = header_ptr->GetExtension(bitchain::Ext::total_size);
            _bitstream.resize(size, false);
        }
    }
}

void Bitstream::report_bitstream(const size_t & bits_per_line) const {
    INFO("[BITGEN] Current bitstream:");
    for (size_t i = 0; i < _bitstream.size(); i += bits_per_line) {
        size_t end = i + bits_per_line;
        if (end >= _bitstream.size()) {
            end = _bitstream.size();
        }
        INFO("[BITGEN] {}-{}: {}", i, end,
                bitstream_to_string(vector<bool>(_bitstream.begin() + i, _bitstream.begin() + end)));
    }
}

bool Bitstream::_place_block_instance(const string & block_name,
        const uint32_t & x,
        const uint32_t & y,
        const uint32_t & subblock) {
    const PackingManager * pack_mgr = static_cast<const PackingManager *>(_pack_mgr);

    auto block_instance_ptr = pack_mgr->get_block_instance(block_name);
    if (nullptr == block_instance_ptr) {
        ERROR("[PLACE] Block instance '{}' is not defined", block_name);
        return false;
    }
    auto & block_instance = *block_instance_ptr;

    auto placements_ptr = _config_db->get_placement_actions(x, y, subblock);
    if (nullptr != placements_ptr) {
        for (auto & placement : *placements_ptr) {
            auto size = placement.ExtensionSize(bitchain::Ext::placement_actions);
            for (int i = 0; i < size; ++i) {
                auto & action = placement.GetExtension(bitchain::Ext::placement_actions, i);
                for (unsigned int j = 0; j < action.width(); ++j) {
                    unsigned int    from_idx = action.begin() + j,
                                    to_idx = action.offset() + j;
                    _bitstream[to_idx] = block_instance[from_idx];
                }
            }
        }
    }

    return true;
}

bool Bitstream::_route_connection(const uint64_t & src_node,
        const uint64_t & sink_node) {
    TRACE("[ROUTE] Connecting node {} to node {}", src_node, sink_node);
    auto actions_ptr = _config_db->get_edge_actions(src_node, sink_node);
    if (nullptr == actions_ptr) {
        return false;
    }
    for (auto & actions : *actions_ptr) {
        auto size = actions.ExtensionSize(bitchain::Ext::edge_actions);
        for (int i = 0; i < size; ++i) {
            auto & action = actions.GetExtension(bitchain::Ext::edge_actions, i);
            DEBUG("[ROUTE] Setting {} to bits {} +: {}", action.value(), action.offset(), action.width());
            for (unsigned int j = 0; j < action.width(); ++j) {
                _bitstream[action.offset() + j] = action.value() & (1 << j);
            }
        }
    }
    return true;
}

Bitstream::WriteBitstreamStatus Bitstream::write_bitstream_memh(const char * filename,
        const unsigned int & width) const {
    if (width != 4 && width != 8 && width != 16 && width != 32 && width != 64) {
        ERROR("[BITGEN] Unsupported word size: {} (accepted word sizes are: 4, 8, 16, 32, 64)", width);
        return WRITE_BITSTREAM_BAD_ALIGNMENT;
    }

    ofstream stream(filename);
    if (!stream) {
        ERROR("[BITSTREAM] Creating output file error: {}", filename);
        return WRITE_BITSTREAM_BAD_FILE;
    }

    auto bit = _bitstream.rbegin();
    for (unsigned int addr = 0; bit != _bitstream.rend(); ++addr) {
        uint64_t h = 0;
        for (unsigned int i = 0; i < width; ++i) {
            h |= (bit != _bitstream.rend() && *(bit++)) ? (1 << i) : 0;
        }
        stream << setfill('0') << setw(width / 4) << hex << h;
        if (addr % 4 == 3) {
            stream << endl;
        } else {
            stream << " ";
        }
    }

    stream.close();

    return WRITE_BITSTREAM_SUCCESS;
}

Bitstream::WriteBitstreamStatus Bitstream::write_bitstream_memh(const string & filename,
        const unsigned int & width) const {
    return write_bitstream_memh(filename.c_str(), width);
}
