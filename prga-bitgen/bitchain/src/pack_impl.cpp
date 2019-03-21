#include "util.hpp"
#include "pack_impl.hpp"
#include "bitchain.pb.h"

using namespace std;
using namespace prga;

PackingManager::PackingManager(const ConfigDatabase * config_db,
                const SynthResultManager * synth_mgr):
    AbstractPackingManager(config_db, synth_mgr),
    _block_instances(), _cur_block_bitstream(nullptr)
{}

void PackingManager::report_block_instances() const {
    INFO("====== report block instances ======");
    for (auto it : _block_instances) {
        INFO("[PACK] [Block instance] {}: {}", it.first, bitstream_to_string(it.second));
    }
}

int PackingManager::get_num_block_instances() const {
    return _block_instances.size();
}

const vector<bool> * PackingManager::get_block_instance(const string & name) const {
    auto it = _block_instances.find(name);
    return (it == _block_instances.end()) ? nullptr : &(it->second);
}

void PackingManager::_enter_block_impl(const AbstractPackingManager::AttributeMap & attrs) {
    auto name_it = attrs.find(_Constants::str_name);
    if (name_it == attrs.end()) {
        ERROR("[PACK] {}:{} Expecting 'name' attribute in 'block' element", _filename, _lineno);
        _state = PARSER_STATE_FORMAT_ERROR;
        return;
    }
    auto & name = name_it->second;

    auto action = _cur_block->get_action();
    if (nullptr == action || !action->HasExtension(bitchain::Ext::config_size)) {
        auto result = _block_instances.emplace(name, vector<bool>(0));
        if (!result.second) {
            ERROR("[PACK] Duplicated block instance '{}'", name);
            _state = PARSER_STATE_INTERNAL_ERROR;
        }
        _cur_block_bitstream = &(result.first->second);
        TRACE("[PACK] Creating block instance: {}, bits: {}", name, 0);
    } else {
        auto size = action->GetExtension(bitchain::Ext::config_size);
        auto result = _block_instances.emplace(name, vector<bool>(size));
        if (!result.second) {
            ERROR("[PACK] Duplicated block instance '{}'", name);
            _state = PARSER_STATE_INTERNAL_ERROR;
        }
        _cur_block_bitstream = &(result.first->second);
        TRACE("[PACK] Creating block instance: {}, bits: {}", name, size);
    }
}

void PackingManager::_select_mode(const string & mode) {
    TRACE("[PACK] Selecting mode: {}", mode);

    auto actions = _cur_instance->get_mode_action(mode);

    if (!actions) {
        WARN("[PACK] {}:{} No configuration actions to be taken for mode '{}'",
                _filename, _lineno, mode);
        return;
    }

    auto num_actions = actions->ExtensionSize(bitchain::Ext::mode_actions);
    for (int j = 0; j < num_actions; ++j) {
        auto & action = actions->GetExtension(bitchain::Ext::mode_actions, j);

        for (unsigned int k = 0; k < action.width(); ++k) {
            _cur_block_bitstream->at(action.offset() + k) = action.value() & (1 << k);
        }
    }
}

void PackingManager::_select_port_connections(const vector<string> & connections) {
    TRACE("[PACK] Selecting port connections: {}", connections.size());

    for (unsigned int i = 0; i < connections.size(); ++i) {
        auto bit = _cur_port->get_bit(i);
        if (!bit) {
            ERROR("[PACK] {}:{} No config database for bit no. {} in the current port", _filename, _lineno, i);
            _state = PARSER_STATE_MISSING_IN_CONFIG_DB;
            return;
        }

        auto actions = bit->get_connection_action(connections[i]);
        if (!actions) {
            if (_Constants::str_open.compare(connections[i]) == 0) {
                TRACE("[PACK] Ignoring 'open' connection for bit no. {}", i);
            } else if (!bit->is_hardwired()) {
                WARN("[PACK] {}:{} No configuration actions to be taken for connection '{}' for bit no. {}",
                        _filename, _lineno, connections[i], i);
            }
            continue;
        }

        auto num_actions = actions->ExtensionSize(bitchain::Ext::connection_actions);
        for (int j = 0; j < num_actions; ++j) {
            auto & action = actions->GetExtension(bitchain::Ext::connection_actions, j);

            for (unsigned int k = 0; k < action.width(); ++k) {
                _cur_block_bitstream->at(action.offset() + k) = action.value() & (1 << k);
            }
        }
    }
}

void PackingManager::_configure_lut(const vector<bool> & bitstream) {
    TRACE("[PACK] configuring lut: {}", bitstream.size());

    auto actions = _cur_instance->get_action();

    if (!actions) {
        WARN("[PACK] {}:{} No configuration actions to be taken for lut rotation",
                _filename, _lineno);
        return;
    }

    auto num_actions = actions->ExtensionSize(bitchain::Ext::lut_actions);
    for (int j = 0; j < num_actions; ++j) {
        auto & action = actions->GetExtension(bitchain::Ext::lut_actions, j);

        for (unsigned int k = 0; k < action.width(); ++k) {
            int from_idx = action.begin() + k,
                to_idx = action.offset() + k;
            _cur_block_bitstream->at(to_idx) = bitstream[from_idx];
        }
    }
}

unique_ptr<AbstractPackingManager> AbstractPackingManager::create_packing_manager(const ConfigDatabase * config_db,
                const SynthResultManager * synth_mgr) {
    return unique_ptr<AbstractPackingManager>(dynamic_cast<AbstractPackingManager *>(new PackingManager(config_db, synth_mgr)));
}
