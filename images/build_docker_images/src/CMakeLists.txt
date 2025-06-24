set(SUB_DIRS "utility")
foreach(sub_dir IN LISTS SUB_DIRS)
    add_subdirectory(${sub_dir})
endforeach()

# ------------------create executable----------------------
include_directories(${HEADER_DIR})
set(EXECUTABLE_OUTPUT_PATH ${EXEC_DIR})
link_directories(${LIB_DIR})
link_libraries(${UTILITY_LIB_NAME})
add_executable(${EXEC_NAME} main.cpp)
# ------------------create executable----------------------