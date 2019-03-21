project("prga-bitgen-shared")
cmake_minimum_required(VERSION 3.5.0)

##############################################################################
##                              Compile Protobuf                            ##
##############################################################################
set(PROTOBUF_IMPORT_DIRS ${CMAKE_SOURCE_DIR}/proto)

PROTOBUF_GENERATE_CPP(PROTO_SRC PROTO_HEADER
    ${CMAKE_SOURCE_DIR}/proto/common.proto)

##############################################################################
##                               Shared library                             ##
##############################################################################
include_directories(${PRGA_BITGEN_THIRD_PARTY_INCLUDE_DIRS})
include_directories(${CMAKE_CURRENT_BINARY_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

file(GLOB_RECURSE SHARED_SRCS ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp)

set(LIB_NAME prga-bitgen-shared)

add_library(${LIB_NAME} STATIC ${PROTO_SRC} ${SHARED_SRCS})
target_link_libraries(${LIB_NAME} ${PRGA_BITGEN_THIRD_PARTY_LIBS})

set(PRGA_BITGEN_SHARED_LIBS ${LIB_NAME} PARENT_SCOPE)
set(PRGA_BITGEN_SHARED_INCLUDE_DIRS
    ${PRGA_BITGEN_THIRD_PARTY_INCLUDE_DIRS}
    ${CMAKE_CURRENT_BINARY_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    PARENT_SCOPE)
