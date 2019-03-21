project("prga-python-proto-bitchain")
cmake_minimum_required(VERSION 3.5.0)

include_directories(${PROTOBUF_INCLUDE_DIRS})

# force in-source build
set(CMAKE_CURRENT_BINARY_DIR ${CMAKE_CURRENT_LIST_DIR})
set(PROTOBUF_IMPORT_DIRS ${CMAKE_SOURCE_DIR}/proto)

PROTOBUF_GENERATE_PYTHON(PROTO_PY ${CMAKE_SOURCE_DIR}/proto/common.proto
    ${CMAKE_SOURCE_DIR}/proto/bitchain.proto)
add_custom_target(prga-python-proto-bitchain ALL DEPENDS ${PROTO_PY})
set_property(DIRECTORY APPEND PROPERTY ADDITIONAL_MAKE_CLEAN_FILES ${PROTO_PY})
