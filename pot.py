import os
import zipfile
import shutil
import re


def get(filename):
    dir_prefix = "./tmp/"
    if os.path.isdir(dir_prefix):
        shutil.rmtree(dir_prefix)
    os.mkdir(dir_prefix)

    zip_file = zipfile.ZipFile(filename)
    zip_list = zip_file.namelist()
    for f in zip_list:
        zip_file.extract(f, "./tmp")

    filename_list = os.listdir(dir_prefix)

    # 如果说解压后只存在一个目录，那说明插件在打包的时候是从上级目录开始打包的，于是就需要进入到这个目录查看实际的包内容
    if len(filename_list) == 1:
        dir_prefix += filename_list[0]

    pot_file = find_pot_file_by_dir(dir_prefix)

    # 如果目录中搜索不到pot文件就尝试用WordPress提供的wp-cli工具生成pot文件
    if pot_file is None:
        os.system("php ./wp-cli.phar i18n make-pot " + dir_prefix)
        pot_file = find_pot_file_by_dir(dir_prefix)

    zip_file.close()

    return pot_file


def find_pot_file_by_dir(dir_prefix):
    filename_list = os.listdir(dir_prefix)

    # 开始查找.pot文件，这个文件可能在三个地方出现：插件根目录、languages、lang
    pot_file = find_pot_file_by_list(filename_list)
    if pot_file is not None:
        return dir_prefix + "/" + pot_file
    if "languages" in filename_list and pot_file is None:
        filename_list = os.listdir(dir_prefix + "/languages")
        pot_file = find_pot_file_by_list(filename_list)
        if pot_file is not None:
            return dir_prefix + "/languages/" + pot_file
    if "lang" in filename_list and pot_file is None:
        filename_list = os.listdir(dir_prefix + "/lang")
        pot_file = find_pot_file_by_list(filename_list)
        if pot_file is not None:
            return dir_prefix + "/lang/" + pot_file

    return None


def find_pot_file_by_list(filename_list):
    for v in filename_list:
        pot_file = re.match(r"[\w]+.pot$", v)
        if pot_file is not None:
            return v

    return None
