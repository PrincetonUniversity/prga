project("prga-bitgen-bitchain")
cmake_minimum_required(VERSION 3.5.0)

##############################################################################
##                              Compile Protobuf                            ##
##############################################################################
set(PROTOBUF_IMPORT_DIRS ${CMAKE_SOURCE_DIR}/proto)

PROTOBUF_GENERATE_CPP(PROTO_SRC PROTO_HEADER
    ${CMAKE_SOURCE_DIR}/proto/bitchain.proto)

##############################################################################
##                              bitgen-bitchain                             ##
##############################################################################
include_directories(${PRGA_BITGEN_SHARED_INCLUDE_DIRS})
include_directories(${CMAKE_CURRENT_BINARY_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

file(GLOB_RECURSE BITCHAIN_SRCS ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp)

set(EXE_NAME prga-bitgen-bitchain)

add_executable(${EXE_NAME} ${PROTO_SRC} ${BITCHAIN_SRCS})
target_link_libraries(${EXE_NAME} ${PRGA_BITGEN_SHARED_LIBS})

set(PRGA_BITGEN_BITCHAIN_BIN ${EXE_NAME} PARENT_SCOPE)
