//
// Created by 张贺凡 on 2023/11/22.
//

#ifndef PARSER_H
#define PARSER_H
#include "cmdline.h"
struct parse_result{
    std::string image_name;
    std::string operation;
};
parse_result parse_command_line(int argc, char* argv[]);
#endif // PARSER_H
