include_directories(${HEADER_DIR})
set(LIBRARY_OUTPUT_PATH ${LIB_DIR})
add_library(${UTILITY_LIB_NAME} STATIC network_status.cpp
        images.cpp parser.cpp)