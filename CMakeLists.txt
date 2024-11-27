cmake_minimum_required(VERSION 3.15...3.26)

project(
  ${SKBUILD_PROJECT_NAME}
  LANGUAGES C
  VERSION ${SKBUILD_PROJECT_VERSION})

find_package(
  Python 
  COMPONENTS 
  Interpreter 
  Development.Module 
  ${SKBUILD_SABI_COMPONENT} 
  REQUIRED)

if("${Python_INTERPRETER_ID}" STREQUAL "PyPy")
    message(STATUS "PyPy detected. Skip compilation of C-extension.")
    return()
endif()

if(NOT CMAKE_C_COMPILER)
    message(STATUS "C compiler not found. Skip compilation of C-extension.")
    return()
endif()

if(NOT "${SKBUILD_SABI_COMPONENT}" STREQUAL "")
    # placeholder for stable abi builds
    set(PY_ABI_OPTIONS "WITH_SOABI" "USE_SABI" "3.11")
else()
    set(PY_ABI_OPTIONS "")
endif()

python_add_library(c
                   MODULE
                   src/bitstruct/c.c
                   src/bitstruct/bitstream.c
                   ${PY_ABI_OPTIONS})

install(TARGETS c DESTINATION bitstruct)
