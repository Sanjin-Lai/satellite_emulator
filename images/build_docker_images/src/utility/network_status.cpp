//
// Created by 张贺凡 on 2023/11/22.
//
#include "network_status.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <iostream>
#include <netdb.h>
#include <cstring>

bool check_network_status(){
    // creat tcp socket
    int socket_fd = socket(AF_INET, SOCK_STREAM, 0);
    if(socket_fd < 0){
        perror("socket");
    }
    // create server address
    struct sockaddr_in server_addr{
        .sin_family = AF_INET,
        .sin_port = htons(PORT)
    };
    // convert domain name to ip address
    struct hostent* host = gethostbyname(BAIDU);
    if(host == nullptr){
        perror("gethostbyname");
        return false;
    }
    // copy ip address to server address
    memcpy(&server_addr.sin_addr, host->h_addr, host->h_length);
    // connect to server
    int connect_status = connect(socket_fd, (struct sockaddr*)&server_addr, sizeof(server_addr));
    if(connect_status < 0){
        perror("connect");
        return false;
    }
    // close socket
    close(socket_fd);
    return true;
}

void recover_network(){
    system(NETWORK_RECOVERY_SCRIPT);
}