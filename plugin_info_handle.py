import os
import re
import json
import zipfile
import urllib.request
import http.client


def get_name():
    dir_prefix = "./tmp/plugin/"

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
    plugin_dir = os.listdir("./tmp/plugin")

    if len(plugin_dir) == 1:
        return plugin_dir[0]

    raise Exception("无法获取插件文本域")

def get_official_language_package():
    zh_cn_package_url = ""
    http_client = None
    memory_query_url = "/translations/plugins/1.0/?slug=" + get_text_domain()
    try:
        http_client = http.client.HTTPSConnection("api.w.org.ibadboy.net")
        http_client.request("GET", memory_query_url)
        response = http_client.getresponse()
        result_all = response.read().decode("utf-8")
        result = json.loads(result_all)

        if len(result) != 0 and response.status == 200:
            trans = result["translations"]
            for language in trans:
                if language["language"] == "zh_CN":
                    zh_cn_package_url = language["package"]
    finally:
        if http_client:
            http_client.close()

    if len(zh_cn_package_url) > 0:
        urllib.request.urlretrieve(zh_cn_package_url, "./tmp/language.zip")

    zip_file = zipfile.ZipFile("./tmp/language.zip")
    zip_list = zip_file.namelist()
    for f in zip_list:
        zip_file.extract(f, "./tmp")

    zip_file.close()
