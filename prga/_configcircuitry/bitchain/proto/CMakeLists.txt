project("prga-python-proto-bitchain")
cmake_minimum_required(VERSION 3.5.0)

include_directories(${PROTOBUF_INCLUDE_DIRS})

# force in-source build
set(CMAKE_CURRENT_BINARY_DIR ${CMAKE_CURRENT_LIST_DIR})
set(PROTOBUF_IMPORT_DIRS ${CMAKE_SOURCE_DIR}/proto/common
    ${CMAKE_SOURCE_DIR}/proto/bitchain)

PROTOBUF_GENERATE_PYTHON(PROTO_PY ${CMAKE_SOURCE_DIR}/proto/common/common.proto
    ${CMAKE_SOURCE_DIR}/proto/bitchain/bitchain.proto)
add_custom_target(prga-python-proto-bitchain ALL DEPENDS ${PROTO_PY})
