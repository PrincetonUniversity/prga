project("prga")
cmake_minimum_required(VERSION 3.5.0)

##############################################################################
##                              global settings                             ##
##############################################################################
# check compiler version
if("${CMAKE_CXX_COMPILER_ID}" STREQUAL "GNU")
    if (CMAKE_CXX_COMPILER_VERSION VERSION_LESS 4.9)
        message(FATAL_ERROR "GCC version must be at least 4.9!")
    endif()
else()
    message(WARNING
        "You are using an unsupported compiler! Only tested on GCC 4.9+")
endif()

# check the cxx compiler supports c++11
include(CheckCXXCompilerFlag)
CHECK_CXX_COMPILER_FLAG("-std=c++11" CXX_COMPILER_SUPPORTS_CXX11)
if(NOT ${CXX_COMPILER_SUPPORTS_CXX11})
    message(FATAL_ERROR "The compiler ${CMAKE_CXX_COMPILER} has no C++11 support")
else()
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11 -O3 -Wall")
endif()

# find Protobuf
include(FindProtobuf)
find_package(Protobuf REQUIRED)
if(NOT ${PROTOBUF_FOUND})
    message(FATAL_ERROR "Protobuf not found")
endif()

# tests:
enable_testing()

# executable output path
set(EXECUTABLE_OUTPUT_PATH ${CMAKE_BINARY_DIR}/bin)

##############################################################################
##                          Sub-directories set up                          ##
##############################################################################
# set sub-projects
add_subdirectory(prga/_configcircuitry/bitchain/proto)
add_subdirectory(bitgen)

##############################################################################
##                             Integration Tests                            ##
##############################################################################
add_test(NAME naive
    COMMAND make
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/examples/naive/build)

add_test(NAME small
    COMMAND make
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/examples/small/build)

add_test(NAME longsegment
    COMMAND make
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/examples/longsegment/build)

##############################################################################
##                             Custom clean-up                              ##
##############################################################################
add_custom_target(cleanall
    COMMAND ${CMAKE_MAKE_PROGRAM} clean
    COMMAND ${CMAKE_MAKE_PROGRAM} -C ${CMAKE_SOURCE_DIR}/examples clean)
