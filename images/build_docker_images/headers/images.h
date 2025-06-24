//
// Created by 张贺凡 on 2023/11/22.
//
#ifndef BUILD_IMAGES_H
#define BUILD_IMAGES_H
#include <string>
#define BUILD_PYTHON_36_PATH "../../build-python/build_python_36/"
#define BUILD_PYTHON_38_PATH "../../build-python/build_python_38/"
#define BUILD_UBUNTU_PATH "../../build-ubuntu/"
#define BUILD_SATELLITE_NODE_PATH "../../build-satellite"

#define UBUNTU_IMAGE_NAME "ubuntu-modified"
#define PYTHON_IMAGE_NAME "ubuntu-python"
#define SATELLITE_NODE_IMAGE_NAME "satellite-node"

#define OPERATION_BUILD "build"
#define OPERATION_REMOVE "remove"
#define OPERATION_REBUILD "rebuild"

#define SINGLE_LINE_LENGTH 100
struct ImageExistence{
    bool ubuntu_existence;
    bool python_existence;
    bool satellite_node_existence;
};
struct parse_result;
void execute_operation_on_images(ImageExistence image_existence, const parse_result& result_of_parser);
void build_image_operation(const std::string& image_name, ImageExistence image_existence);
void remove_image_operation(const std::string& image_name);
void rebuild_image_operation(const std::string& image_name);
void clean_images_cache();
ImageExistence check_images_existence();
#endif //BUILD_IMAGES_H
