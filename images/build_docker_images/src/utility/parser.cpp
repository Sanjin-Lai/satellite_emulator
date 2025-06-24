//
// Created by 张贺凡 on 2023/11/22.
//
#include "parser.h"
#include "images.h"
#include <iostream>
#include <sstream>

parse_result parse_command_line(int argc, char* argv[]){
    cmdline::parser parser;
    struct parse_result result;

    std::stringstream ss;
    ss << "image name to operate" << " [ " << UBUNTU_IMAGE_NAME << " | " << PYTHON_IMAGE_NAME << " | " << SATELLITE_NODE_IMAGE_NAME << " ]";
    parser.add<std::string>("image_name",
                            'i',
                            ss.str(),
                            true,
                            "",
                            cmdline::oneof(std::string(UBUNTU_IMAGE_NAME), std::string(PYTHON_IMAGE_NAME), std::string(SATELLITE_NODE_IMAGE_NAME)));

    ss.str("");

    ss << "operation to perform" << " [ " << OPERATION_BUILD << " | " << OPERATION_REMOVE << " | " << OPERATION_REBUILD << " ]";
    parser.add<std::string>("operation",
                            'o',
                            ss.str(),
                            true,
                            "build",
                            cmdline::oneof(std::string(OPERATION_BUILD), std::string(OPERATION_REMOVE), std::string(OPERATION_REBUILD)));

    parser.parse_check(argc, argv);
    result.image_name = parser.get<std::string>("image_name");
    result.operation = parser.get<std::string>("operation");

    return result;
}