cmake_minimum_required(VERSION 3.10)
project(dwg2dxf LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Default to Release build
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# libdxfrw static library
set(LIBDXFRW_SRC_DIR ${CMAKE_SOURCE_DIR}/dwg2dxf/libdxfrw/src)

set(LIBDXFRW_SOURCES
    ${LIBDXFRW_SRC_DIR}/drw_classes.cpp
    ${LIBDXFRW_SRC_DIR}/drw_entities.cpp
    ${LIBDXFRW_SRC_DIR}/drw_header.cpp
    ${LIBDXFRW_SRC_DIR}/drw_objects.cpp
    ${LIBDXFRW_SRC_DIR}/libdwgr.cpp
    ${LIBDXFRW_SRC_DIR}/libdxfrw.cpp
    ${LIBDXFRW_SRC_DIR}/Transcode.cpp
    ${LIBDXFRW_SRC_DIR}/intern/drw_dbg.cpp
    ${LIBDXFRW_SRC_DIR}/intern/drw_textcodec.cpp
    ${LIBDXFRW_SRC_DIR}/intern/dwgbuffer.cpp
    ${LIBDXFRW_SRC_DIR}/intern/dwgreader.cpp
    ${LIBDXFRW_SRC_DIR}/intern/dwgreader15.cpp
    ${LIBDXFRW_SRC_DIR}/intern/dwgreader18.cpp
    ${LIBDXFRW_SRC_DIR}/intern/dwgreader21.cpp
    ${LIBDXFRW_SRC_DIR}/intern/dwgreader24.cpp
    ${LIBDXFRW_SRC_DIR}/intern/dwgreader27.cpp
    ${LIBDXFRW_SRC_DIR}/intern/dwgutil.cpp
    ${LIBDXFRW_SRC_DIR}/intern/dxfreader.cpp
    ${LIBDXFRW_SRC_DIR}/intern/dxfwriter.cpp
    ${LIBDXFRW_SRC_DIR}/intern/rscodec.cpp
)

add_library(libdxfrw STATIC ${LIBDXFRW_SOURCES})

target_include_directories(libdxfrw PUBLIC
    ${LIBDXFRW_SRC_DIR}
    ${LIBDXFRW_SRC_DIR}/intern
)

# dwg2dxf executable
set(DWG2DXF_SRC_DIR ${CMAKE_SOURCE_DIR}/dwg2dxf/dwg2dxf)

add_executable(dwg2dxf
    ${DWG2DXF_SRC_DIR}/main.cpp
    ${DWG2DXF_SRC_DIR}/dx_iface.cpp
)

target_include_directories(dwg2dxf PRIVATE
    ${DWG2DXF_SRC_DIR}
    ${LIBDXFRW_SRC_DIR}
)

target_link_libraries(dwg2dxf PRIVATE libdxfrw)

# fix_dxf executable: post-process LibreDWG DXF output
# Fixes encoding (GBK->UTF-8), negative layer colors, and DWGCODEPAGE
add_executable(fix_dxf ${DWG2DXF_SRC_DIR}/fix_dxf.cpp)

if(WIN32)
    # On Windows, ensure setlocale works correctly with Chinese characters
    target_compile_definitions(dwg2dxf PRIVATE _CRT_SECURE_NO_WARNINGS)
endif()
