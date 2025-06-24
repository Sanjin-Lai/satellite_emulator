#!/usr/bin/env bash

# 删除所有的容器
docker rm -f $(docker ps -aq)
# 删除所有的 veth pair
ip link show type veth | awk '{print $2}' | sed 's/@.*//' | xargs -n1 sudo ip link delete
# 列出所有以 br 开头的网桥并删除它们
#ip link show type bridge | grep 'br' | awk '{print $2}' | tr -d ':' | xargs -I {} sudo ip link delete {}