#! /usr/bin/python3

import unicodedata
import polib
import io
import re
import random
import http.client
from urllib import parse
from tqdm import tqdm
import sys
import json
import hashlib
import urllib
import os
import zipfile
import urllib.request
import shutil


class PluginInfoHandle:
    def make_pot_file(self, filename):
        dir_prefix = "./tmp/plugin/"
        if os.path.isdir(dir_prefix):
            shutil.rmtree(dir_prefix)
        os.mkdir(dir_prefix)

        zip_file = zipfile.ZipFile(filename)
        zip_list = zip_file.namelist()
        for f in zip_list:
            zip_file.extract(f, "./tmp/plugin")

        filename_list = os.listdir(dir_prefix)

        # 如果说解压后只存在一个目录，那说明插件在打包的时候是从上级目录开始打包的，于是就需要进入到这个目录查看实际的包内容
        if len(filename_list) == 1:
            dir_prefix += filename_list[0]

        pot_file = self.find_pot_file_by_dir(dir_prefix)

        # 如果目录中搜索不到pot文件就尝试用WordPress提供的wp-cli工具生成pot文件
        if pot_file is None:
            os.system("php ./wp-cli.phar i18n make-pot " + dir_prefix)
            pot_file = self.find_pot_file_by_dir(dir_prefix)

        zip_file.close()

        return pot_file

    def find_pot_file_by_dir(self, dir_prefix):
        filename_list = os.listdir(dir_prefix)

        # 开始查找.pot文件，这个文件可能在三个地方出现：插件根目录、languages、lang
        pot_file = self.find_pot_file_by_list(filename_list)
        if pot_file is not None:
            return dir_prefix + "/" + pot_file
        if "languages" in filename_list and pot_file is None:
            filename_list = os.listdir(dir_prefix + "/languages")
            pot_file = self.find_pot_file_by_list(filename_list)
            if pot_file is not None:
                return dir_prefix + "/languages/" + pot_file
        if "lang" in filename_list and pot_file is None:
            filename_list = os.listdir(dir_prefix + "/lang")
            pot_file = self.find_pot_file_by_list(filename_list)
            if pot_file is not None:
                return dir_prefix + "/lang/" + pot_file

        return None

    def find_pot_file_by_list(self, filename_list):
        for v in filename_list:
            pot_file = re.findall(r"[\w]+.pot$", v)
            if len(pot_file) != 0:
                return v

        return None

    def get_name(self):
        dir_prefix = "./tmp/plugin/"

        filename_list = os.listdir(dir_prefix)
        if len(filename_list) == 1:
            dir_prefix += filename_list[0]
            filename_list = os.listdir(dir_prefix)

        for v in filename_list:
            php_file = re.findall(r"[\w]+.php$", v)
            if len(php_file) != 0:
                file = open(dir_prefix + "/" + v, "r", encoding="utf-8")

                i = 0
                for line in file:
                    if i >= 30:
                        break
                    plugin_name_match = re.match(r".*Plugin Name:\s+", line)
                    if plugin_name_match is not None:
                        return (line[plugin_name_match.regs[0][1]:len(line)]).replace("\n", "").replace("\r", "")
                    i += 1
                file.close()

        return None

    def get_text_domain(self):
        plugin_dir = os.listdir("./tmp/plugin")

        if len(plugin_dir) == 1:
            return plugin_dir[0]

        raise Exception("无法获取插件文本域")

    def get_official_language_package(self):
        zh_cn_package_url = ""
        http_client = None
        memory_query_url = "/translations/plugins/1.0/?slug=" + self.get_text_domain()
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


class Translator:
    __baidu_id = ""
    __baidu_key = ""

    def __init__(self, src_po_file=None, baidu_id=None, baidu_key=None):
        self.__baidu_id = baidu_id
        self.__baidu_key = baidu_key
        if src_po_file is not None:
            self.open_po_file(src_po_file)

    def open_po_file(self, po_filename):
        if isinstance(po_filename, io.TextIOWrapper):
            po_filename = po_filename.name
        self.po = polib.pofile(po_filename)

    def _translate_str(self, text, return_src_if_empty_result=True, exclude=None):
        if not text.strip():
            return ""

        http_client = None
        memory_query_url = "/wp-content/plugins/gp-super-more/query_memory.php?query=" + parse.quote(text)
        try:
            http_client = http.client.HTTPSConnection("wptest.ibadboy.net")
            http_client.request("GET", memory_query_url)
            response = http_client.getresponse()
            result = response.read().decode("utf-8")

            if len(result) != 0 and response.status == 200:
                return result
        finally:
            if http_client:
                http_client.close()

        exclude_dict = {}
        match_list = re.findall(
            r"%[sd]|&[a-z]+;|%[0-9]+{\$s}|\[.+\]|<.+?>|http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            text)
        if match_list is not None:
            for value in match_list:
                exclude_dict[" " + str(random.randint(0, 264308)) + " "] = value

        for (k, v) in exclude_dict.items():
            text = str(text).replace(v, k)

        if exclude is not None:
            random_str = str(random.randint(0, 99999))
            exclude_dict[random_str] = exclude
            text = str(text).replace(exclude, random_str)

        tr = self.baidu_trans(text, "auto", "zh")
        if "error_code" not in tr:
            tr_text = tr['trans_result'][0]['dst']
        else:
            tr_text = ""

        if not tr_text and return_src_if_empty_result:
            tr_text = text

        for (k, v) in exclude_dict.items():
            tr_text = tr_text.replace(k[1:len(k) - 1], v)

        return unicodedata.normalize('NFKC', tr_text)

    def go_translate(self, exclude="", **kwargs):
        break_on = kwargs.get("break_on", False)
        pos = 0
        print(exclude + " 插件开始本地化：")
        pbar = tqdm(self.po)

        for item in pbar:
            if break_on and break_on == pos:
                break
            pos += 1
            translated = False
            if item.msgid:
                item.msgstr = self._translate_str(item.msgid, True, exclude)
                translated = True
            if item.msgid_plural:
                item.msgstr_plural[0] = self._translate_str(item.msgid, True, exclude)
                item.msgstr_plural[1] = item.msgstr_plural[0]
                translated = True
            if not translated and item.msgstr:
                item.msgstr = self._translate_str(item.msgstr, True, exclude)
                if item.msgstr_plural:
                    item.msgstr_plural[0] = self._translate_str(item.msgstr, True, exclude)
                    item.msgstr_plural[1] = item.msgstr_plural[0]

    def save_po_file(self, dest_po_file=None):
        self.po.save(dest_po_file)

    def save_mo_file(self, dest_mo_file=None):
        self.po.save_as_mofile(dest_mo_file)

    def baidu_trans(self, q="", fromLang="auto", toLang="zh"):
        appid = self.__baidu_id
        secretKey = self.__baidu_key

        httpClient = None
        myurl = "/api/trans/vip/translate"

        salt = random.randint(32768, 65536)
        sign = appid + q + str(salt) + secretKey
        sign = hashlib.md5(sign.encode()).hexdigest()
        myurl = myurl + "?appid=" + appid + "&q=" + urllib.parse.quote(
            q) + "&from=" + fromLang + "&to=" + toLang + "&salt=" + str(
            salt) + "&sign=" + sign

        try:
            httpClient = http.client.HTTPConnection("api.fanyi.baidu.com")
            httpClient.request("GET", myurl)

            # response是HTTPResponse对象
            response = httpClient.getresponse()
            result_all = response.read().decode("utf-8")
            result = json.loads(result_all)

            return (result)

        except Exception as e:
            print(e)
        finally:
            if httpClient:
                httpClient.close()


config_file = open("./config", "r", encoding="utf-8")
config = data = json.load(config_file)

p = PluginInfoHandle()

pot_file = p.make_pot_file(sys.argv[1])

# plugin_info_handle.get_official_language_package()

t = Translator(pot_file, config["baidu-api"]["id"], config["baidu-api"]["key"])
t.go_translate(p.get_name())

t.save_po_file("./out/%s-zh_CN.po" % (p.get_text_domain()))
t.save_mo_file("./out/%s-zh_CN.mo" % (p.get_text_domain()))
