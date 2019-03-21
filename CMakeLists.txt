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
elseif(Protobuf_VERSION VERSION_LESS 3.7)
    message(FATAL_ERROR "Protobuf version must be at least 3.7!")
endif()

# find Python
include(FindPython)
find_package(Python REQUIRED)
if(NOT ${Python_FOUND})
    message(FATAL_ERROR "Python not found")
elseif(Python_VERSION VERSION_LESS 3.0)
    if(Protobuf_VERSION VERSION_GREATER 3.7 OR
            Protobuf_VERSION VERSION_EQUAL 3.7)
        message(FATAL_ERROR "Python 2 is not compatible with Protobuf 3.7+")
    endif()
elseif(Python_VERSION VERSION_GREATER 3.0)
    if(Protobuf_VERSION VERSION_LESS 3.7)
        message(FATAL_ERROR "Python 3 requires Protobuf 3.7+")
    endif()
endif()

# tests:
enable_testing()

# executable output path
set(EXECUTABLE_OUTPUT_PATH ${CMAKE_SOURCE_DIR}/bin)

##############################################################################
##                          Sub-directories set up                          ##
##############################################################################
# set sub-projects
add_subdirectory(prga-builder/proto)
add_subdirectory(prga-bitgen)

##############################################################################
##                             Integration Tests                            ##
##############################################################################
add_test(NAME naive-fpga
    COMMAND ${CMAKE_MAKE_PROGRAM}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/examples/fpga/naive/naive)

add_test(NAME naive-longsegment
    COMMAND ${CMAKE_MAKE_PROGRAM}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/examples/fpga/naive/naive_L2)

add_test(NAME small-fpga
    COMMAND ${CMAKE_MAKE_PROGRAM}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/examples/fpga/small/k4_N2_8x8)

add_test(NAME small-fpga-longsegment
    COMMAND ${CMAKE_MAKE_PROGRAM}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/examples/fpga/small/k4_N2_8x8_L2)

add_test(NAME small-fpga-hier
    COMMAND ${CMAKE_MAKE_PROGRAM}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/examples/fpga/small/k4_N2_8x8_hier)

add_test(NAME naive-target
    COMMAND ${CMAKE_MAKE_PROGRAM}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/examples/target/xor/naive_naive)

add_test(NAME naive-target-longsegment
    COMMAND ${CMAKE_MAKE_PROGRAM}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/examples/target/xor/naive_naive_L2)

add_test(NAME naive-target-fakeprog
    COMMAND ${CMAKE_MAKE_PROGRAM}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/examples/target/xor/naive_naive_fakeprog)

add_test(NAME small-target
    COMMAND ${CMAKE_MAKE_PROGRAM}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/examples/target/bcd2bin/small_k4_N2_8x8)

add_test(NAME small-target-longsegment
    COMMAND ${CMAKE_MAKE_PROGRAM}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/examples/target/bcd2bin/small_k4_N2_8x8_L2)

add_test(NAME small-target-fakeprog
    COMMAND ${CMAKE_MAKE_PROGRAM}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/examples/target/bcd2bin/small_k4_N2_8x8_fakeprog)

add_test(NAME small-target-hier
    COMMAND ${CMAKE_MAKE_PROGRAM}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/examples/target/bcd2bin/small_k4_N2_8x8_hier)
