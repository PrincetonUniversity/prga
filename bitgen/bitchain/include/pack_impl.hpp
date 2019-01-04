#ifndef PACK_IMPL_H
#define PACK_IMPL_H

#include "pack.hpp"

class PackingManager : public AbstractPackingManager {
    public:
        // constructor
        explicit PackingManager(const ConfigDatabase * config_db,
                const SynthResultManager * synth_mgr);

        void report_block_instances() const;
        int get_num_block_instances() const;

        // API specific to this type of config circuitry
        const std::vector<bool> * get_block_instance(const std::string & name) const;

    private:
        std::map<std::string, std::vector<bool>> _block_instances;
        std::vector<bool> * _cur_block_bitstream;

    protected:
        void _enter_block_impl(const AttributeMap & attrs);
        void _select_mode(const std::string & mode);
        void _select_port_connections(const std::vector<std::string> & connections);
        void _configure_lut(const std::vector<bool> & bitstream);
};

#endif /* PACK_IMPL_H */
