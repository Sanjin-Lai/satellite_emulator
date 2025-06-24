//
// Created by 张贺凡 on 2023/11/22.
//
#include "images.h"
#include "parser.h"
#include <iostream>
#include <cstring>

void execute_operation_on_images(ImageExistence image_existence, const parse_result& result_of_parser){
    std::string image_name = result_of_parser.image_name;
    std::string operation = result_of_parser.operation;
    std::string execute_command;
    if(operation == OPERATION_BUILD){
        build_image_operation(image_name, image_existence);
    } else if(operation == OPERATION_REMOVE){
        remove_image_operation(image_name);
    } else {
        rebuild_image_operation(image_name);
    }
}

void clean_images_cache(){
    std::string execute_command;
    execute_command = "docker builder prune";
    std::cout << "cleaning images cache..." << std::endl;
    system(execute_command.c_str());
}

void rebuild_image_operation(const std::string& image_name){
    remove_image_operation(image_name);
    ImageExistence image_existence = check_images_existence();
    build_image_operation(image_name, image_existence);
}

void remove_image_operation(const std::string& image_name){
    std::string execute_command;
    execute_command = "docker rmi " + image_name;
    std::cout << "removing image..." << std::endl;
    system(execute_command.c_str());
}

void build_image_operation(const std::string& image_name, ImageExistence image_existence){ // NOLINT
    if(image_name == UBUNTU_IMAGE_NAME){
        if(!image_existence.ubuntu_existence){
            std::stringstream ss;
            ss << "docker build -t " << UBUNTU_IMAGE_NAME << ":latest" << " " << BUILD_UBUNTU_PATH;
            std::cout << "building ubuntu image..." << std::endl;
            system(ss.str().c_str());
            ss.str("");
        } else {
            std::cout << "ubuntu image already exists" << std::endl;
        }
    } else if(image_name == PYTHON_IMAGE_NAME){
        if(!image_existence.python_existence){
            if(!image_existence.ubuntu_existence){
                build_image_operation(UBUNTU_IMAGE_NAME, image_existence);
            }
            std::stringstream ss;
            ss << "docker build -t " << PYTHON_IMAGE_NAME << ":latest" << " " << BUILD_PYTHON_38_PATH;
            std::cout << "building python38 image..." << std::endl;
            system(ss.str().c_str());
            ss.str("");
        } else {
            std::cout << "python image already exists" << std::endl;
        }
    } else {
        if(!image_existence.satellite_node_existence){
            if(!image_existence.python_existence){
                build_image_operation(PYTHON_IMAGE_NAME, image_existence);
            }
            std::stringstream ss;
            ss << "docker build -t " << SATELLITE_NODE_IMAGE_NAME << ":latest" << " " << BUILD_SATELLITE_NODE_PATH;
            std::cout << "building satellite node image..." << std::endl;
            system(ss.str().c_str());
        } else {
            std::cout << "satellite node image already exists" << std::endl;
        }
    }
}

ImageExistence check_images_existence(){
    ImageExistence image_existence{
        .ubuntu_existence = false,
        .python_existence = false,
        .satellite_node_existence = false
    };
    char single_line[SINGLE_LINE_LENGTH];
    FILE* fp = popen("docker images", "r");
    if(fp == nullptr){
        perror("popen");
        exit(EXIT_FAILURE);
    }
    while(fgets(single_line, SINGLE_LINE_LENGTH, fp) != nullptr){
        if(strstr(single_line, UBUNTU_IMAGE_NAME) != nullptr){
            std::cout << "ubuntu image exists" << std::endl;
            image_existence.ubuntu_existence = true;
        }
        if(strstr(single_line, PYTHON_IMAGE_NAME) != nullptr){
            std::cout << "python image exists" << std::endl;
            image_existence.python_existence = true;
        }
        if(strstr(single_line, SATELLITE_NODE_IMAGE_NAME) != nullptr){
            std::cout << "satellite node image exists" << std::endl;
            image_existence.satellite_node_existence = true;
        }
    }
    return image_existence;
}