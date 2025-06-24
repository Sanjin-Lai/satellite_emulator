#include "network_status.h"
#include "images.h"
#include "parser.h"
#include <iostream>

int main(int argc, char* argv[]){
    parse_result result_of_parser = parse_command_line(argc, argv);
    while(!check_network_status()){
        std::cout << "network is not available, try to recover..." << std::endl;
        recover_network();
    }
    std::cout << "network is available" << std::endl;
    ImageExistence imageExistence = check_images_existence();
    execute_operation_on_images(imageExistence, result_of_parser);
    atexit(clean_images_cache);
    return 0;
}