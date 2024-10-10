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

if(NOT "${SKBUILD_SABI_COMPONENT}" STREQUAL "")
  python_add_library(c MODULE src/bitstruct/c.c src/bitstruct/bitstream.c WITH_SOABI USE_SABI 3.13)
else()
  python_add_library(c MODULE src/bitstruct/c.c src/bitstruct/bitstream.c)
endif()

install(TARGETS c DESTINATION bitstruct)
