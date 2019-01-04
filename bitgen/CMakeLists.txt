project("prga-bitgen")
cmake_minimum_required(VERSION 3.5.0)

##############################################################################
##                            Third-party set up                            ##
##############################################################################
# set up third-party dependencies
add_subdirectory(third_party/libblifparse)

# set variables for third-party include directories
set(PRGA_BITGEN_THIRD_PARTY_INCLUDE_DIRS
    ${PROTOBUF_INCLUDE_DIRS}
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/spdlog/include
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/libblifparse
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/libblifparse/src)

# set variables for third-party libraries
set(PRGA_BITGEN_THIRD_PARTY_LIBS
    expat
    libblifparse
    ${PROTOBUF_LIBRARIES})

##############################################################################
##                               Shared library                             ##
##############################################################################
add_subdirectory(shared)

##############################################################################
##          Bitgen for different configuration circuitry types              ##
##############################################################################
add_subdirectory(bitchain)
