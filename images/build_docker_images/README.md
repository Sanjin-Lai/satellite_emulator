# build_docker_images

这是一个用来自动化进行镜像重建的命令行程序。可以进行自动的构建 ubuntu-modified ubuntu-python satellite-node 镜像，并进行删除重建等。

- 要进行重新编译，请创建 `build/` 目录，并输入命令 `cmake ..`, 然后输入 `make`。
- 要使用程序，请进入 `bin/` 目录，并输入命令 `./images_manager` 就能够看到提示的内容

