#ifndef BITSTREAM_IMPL_H
#define BITSTREAM_IMPL_H

#include "bitstream.hpp"

class Bitstream : public AbstractBitstream {
    public:
        // constructor
        explicit Bitstream(const ConfigDatabase * config_db,
                const AbstractPackingManager * pack_mgr);

        void report_bitstream(const size_t & bits_per_line) const;
        WriteBitstreamStatus write_bitstream_memh(const char * filename,
                const unsigned int & width) const;
        WriteBitstreamStatus write_bitstream_memh(const std::string & filename,
                const unsigned int & width) const;

    private:
        std::vector<bool> _bitstream;

    protected:
        bool _place_block_instance(const std::string & block_name,
                const uint32_t & x,
                const uint32_t & y,
                const uint32_t & subblock);

        bool _route_connection(const uint64_t & src_node,
                const uint64_t & sink_node);
};

#endif /* BITSTREAM_IMPL_H */
