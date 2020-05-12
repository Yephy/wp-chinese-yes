import os
import re
import unicodedata


def get_name():
    dir_prefix = "./tmp/"

    filename_list = os.listdir(dir_prefix)
    if len(filename_list) == 1:
        dir_prefix += filename_list[0]
        filename_list = os.listdir(dir_prefix)

    for v in filename_list:
        php_file = re.match(r"[\w]+.php$", v)
        if php_file is not None:
            file = open(dir_prefix + "/" + v, "r", encoding="utf-8")

            i = 0
            for line in file:
                if i >= 30:
                    break
                plugin_name_match = re.match(r".+Plugin Name:\s+", line)
                if plugin_name_match is not None:
                    return (line[plugin_name_match.regs[0][1]:len(line)]).replace("\n", "").replace("\r", "")
                i += 1
            file.close()

    return None


def get_text_domain():
    plugin_dir = os.listdir("./tmp")

    if len(plugin_dir) == 1:
        return plugin_dir[0]

    raise Exception("无法获取插件文本域")
