cmake_minimum_required(VERSION 3.22)
project(build_docker_images)

# ------------------INITIALIZE VARIABLES------------------
set(CMAKE_CXX_STANDARD 11)
set(EXEC_DIR ${CMAKE_CURRENT_SOURCE_DIR}/bin)
set(LIB_DIR ${CMAKE_CURRENT_SOURCE_DIR}/lib)
set(HEADER_DIR ${CMAKE_CURRENT_SOURCE_DIR}/headers)
set(EXEC_NAME "images_manager")
set(UTILITY_LIB_NAME "utility")
# ------------------INITIALIZE VARIABLES-------------------

# ------------------add subdirectories---------------------
add_subdirectory(src)
# ------------------add subdirectories---------------------

