import os


class FileOperator:
    @classmethod
    def copy_dir(cls, source_dir: str, dest_dir: str):
        """
        进行文件夹的拷贝
        :param source_dir: 源文件夹
        :param dest_dir:  目标文件夹
        """
        if not os.path.exists(source_dir) and os.path.exists(dest_dir):
            raise ValueError(f"{source_dir} or {dest_dir} not exists")
        os.system(f"cp -rf {source_dir} {dest_dir}")
