#! /usr/bin/python3

import polib
import re
import random
from urllib import parse
from tqdm import tqdm
import sys
import json
import os
import zipfile
import shutil
import requests
import execjs
import html

# 全局变量初始化
plugin_name = ""
plugin_text_domain = ""
plugin_domain_path = ""
plugin_pot_file = ""
plugin_dir = "./tmp/plugin/"
po_file_object = None
wp_plugin_name_list = []

# 异常代码
_PLUGIN_PACKAGE_FORMAT_ERROR = -10
_POT_FILE_NOT_FOUND = -11


# 工具函数定义
def translate_str(text, exclude=None):
    if not html.unescape(text).strip():
        return ""

    result = requests.get("https://wptest.ibadboy.net/wp-content/plugins/gp-super-more/query_memory.php?query="
                          + parse.quote(text))
    if len(result.text) != 0 and result.status_code == 200:
        return result.text

    # 一些不想被翻译的特殊标记替换成随机数字
    exclude_dict = {}
    match_list = list(set(filter(not_empty, re.findall(
        r"<(?!/).+?>|\[.+\]|http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        text))))
    for value in match_list:
        if value[0:1] == "<" and value[len(value) - 1:len(value)] == ">":
            tag_att_list = list(set(filter(not_empty, re.findall(r"\s.+", value[1:len(value) - 1]))))
            for v in tag_att_list:
                exclude_dict[id_generator(exclude_dict)] = v[1:len(v)]
        else:
            exclude_dict[id_generator(exclude_dict)] = value
    # 对于%2$s等占位符，在其两侧增加[]，变成类似如下形式：[%2$s]防止被翻译引擎解析
    match_list = list(set(filter(not_empty, re.findall(r"%[0-9]\$s|%[sd]|&[a-z]+;", text))))
    for value in match_list:
        exclude_dict["[" + value + "]"] = value

    rough_match_list = []
    lower_text = text.lower().replace(" ", "-")
    for plugin in wp_plugin_name_list:
        if plugin in lower_text:
            rough_match_list.append(plugin)

    # 插件/作者名称认定规则：
    # 1、无论用空格还是连词符分隔，每个单词的首字母必须大写
    # 2、鉴于一些插件作者们喜欢用诸如：timer、the、mirror、cache这种沙雕名称，导致过滤单单词插件名会造成很多的误过滤，所以只过滤多单词的名称
    for rough_match in rough_match_list:
        if "-" not in rough_match:
            continue
        reg = r"\b" + (rough_match.title().replace("-", r"[-|\s]")) + r"\b"
        match_list = list(set(filter(not_empty, re.findall(reg, text))))
        for value in match_list:
            exclude_dict[id_generator(exclude_dict)] = value

    for (k, v) in exclude_dict.items():
        text = str(text).replace(v, k)

    if exclude is not None:
        random_str = str(id_generator(exclude_dict))
        exclude_dict[random_str] = exclude
        text = str(text).replace(exclude, random_str)

    google_api = GoogleAPI()
    tr = punctuation_c_trans_to_e(google_api.translate(text))
    if len(tr) != 0:
        for re_str in [r"</.+?>", r"%[0-9]\s\$\ss", r"\s/\s", r"\s/", r"/\s", r"\$\s"]:
            remove_spaces_list = list(set(filter(not_empty, re.findall(re_str, tr))))
            for value in remove_spaces_list:
                tr = str(tr).replace(value, value.replace(" ", ""))
        tr_text = tr
    else:
        tr_text = text

    for (k, v) in exclude_dict.items():
        tr_text = tr_text.replace(k, v)

    return tr_text


class GoogleAPI:
    def __init__(self):
        self.ctx = execjs.compile(""" 
    function TL(a) { 
    var k = ""; 
    var b = 406644; 
    var b1 = 3293161072;       
    var jd = "."; 
    var $b = "+-a^+6"; 
    var Zb = "+-3^+b+-f";    
    for (var e = [], f = 0, g = 0; g < a.length; g++) { 
        var m = a.charCodeAt(g); 
        128 > m ? e[f++] = m : (2048 > m ? e[f++] = m >> 6 | 192 : (55296 == (m & 64512) && g + 1 < a.length && 56320 == (a.charCodeAt(g + 1) & 64512) ? (m = 65536 + ((m & 1023) << 10) + (a.charCodeAt(++g) & 1023), 
        e[f++] = m >> 18 | 240, 
        e[f++] = m >> 12 & 63 | 128) : e[f++] = m >> 12 | 224, 
        e[f++] = m >> 6 & 63 | 128), 
        e[f++] = m & 63 | 128) 
    } 
    a = b; 
    for (f = 0; f < e.length; f++) a += e[f], 
    a = RL(a, $b); 
    a = RL(a, Zb); 
    a ^= b1 || 0; 
    0 > a && (a = (a & 2147483647) + 2147483648); 
    a %= 1E6; 
    return a.toString() + jd + (a ^ b) 
    };      
    function RL(a, b) { 
      var t = "a"; 
      var Yb = "+"; 
      for (var c = 0; c < b.length - 2; c += 3) { 
        var d = b.charAt(c + 2), 
        d = d >= t ? d.charCodeAt(0) - 87 : Number(d), 
        d = b.charAt(c + 1) == Yb ? a >>> d: a << d; 
        a = b.charAt(c) == Yb ? a + d & 4294967295 : a ^ d 
      } 
      return a 
    } 
    """)

    def getTk(self, text):
        return self.ctx.call("TL", text)

    def buildUrl(self, text, tk):
        baseUrl = 'https://translate.google.cn/translate_a/single'
        baseUrl += '?client=webapp&'
        baseUrl += 'sl=auto&'
        baseUrl += 'tl=zh-CN&'
        baseUrl += 'hl=zh-CN&'
        baseUrl += 'dt=at&'
        baseUrl += 'dt=bd&'
        baseUrl += 'dt=ex&'
        baseUrl += 'dt=ld&'
        baseUrl += 'dt=md&'
        baseUrl += 'dt=qca&'
        baseUrl += 'dt=rw&'
        baseUrl += 'dt=rm&'
        baseUrl += 'dt=ss&'
        baseUrl += 'dt=t&'
        baseUrl += 'ie=UTF-8&'
        baseUrl += 'oe=UTF-8&'
        baseUrl += 'otf=1&'
        baseUrl += 'pc=1&'
        baseUrl += 'ssel=0&'
        baseUrl += 'tsel=0&'
        baseUrl += 'kc=2&'
        baseUrl += 'tk=' + str(tk) + '&'
        baseUrl += 'q=' + text
        return baseUrl

    def translate(self, text):
        url = self.buildUrl(parse.quote(text), self.getTk(text))
        res = ''

        try:
            r = requests.get(url)
            result = json.loads(r.text)

            for v in result[0]:
                if v[0] is not None:
                    res += v[0]

            return res
        except Exception as e:
            return text


def id_generator(exist):
    while True:
        random_id = "_" + str(random.randint(200000, 264308)) + "_"
        if random_id not in exist:
            return random_id


def not_empty(s):
    return s and s.strip()


def punctuation_c_trans_to_e(string):
    e_pun = u',.!?[]()<>%"\''
    c_pun = u'，。！？【】（）《》％“‘'
    table = {ord(f): ord(t) for f, t in zip(c_pun, e_pun)}
    return string.translate(table)


# 解压插件压缩包到临时目录
if os.path.isdir(plugin_dir):
    shutil.rmtree(plugin_dir)
os.mkdir(plugin_dir)

zip_file = zipfile.ZipFile(sys.argv[1])
zip_list = zip_file.namelist()
for f in zip_list:
    zip_file.extract(f, plugin_dir)

filename_list = os.listdir(plugin_dir)
if len(filename_list) != 1:
    print("插件包格式错误")
    exit(_PLUGIN_PACKAGE_FORMAT_ERROR)
plugin_dir += filename_list[0]

# 读取插件元信息
filename_list = os.listdir(plugin_dir)
for v in filename_list:
    php_file = re.findall(r"[\w]+.php$", v)
    if len(php_file) != 0:
        file = open(plugin_dir + "/" + v, "r", encoding="utf-8")

        i = 0
        for line in file:
            if i >= 30:
                break
            plugin_meta_title_match = re.findall(r".*Plugin Name:\s+|.*Text Domain:\s+|.*Domain Path:\s+", line)
            for plugin_meta_title in plugin_meta_title_match:
                line = line.replace("\n", "").replace("\r", "")
                plugin_meta_title_len = len(plugin_meta_title)
                plugin_meta_len = len(line)
                if "Plugin Name" in plugin_meta_title:
                    plugin_name = line[plugin_meta_title_len:plugin_meta_len]
                elif "Text Domain" in plugin_meta_title:
                    plugin_text_domain = line[plugin_meta_title_len:plugin_meta_len]
                elif "Domain Path" in plugin_meta_title:
                    plugin_domain_path = line[plugin_meta_title_len:plugin_meta_len]
            i += 1
        file.close()

# 生成pot文件
os.system("php ./wp-cli.phar i18n make-pot " + plugin_dir)
filename_list = os.listdir(plugin_dir + plugin_domain_path)
for v in filename_list:
    pot_file = re.findall(r"[\w]+.pot$", v)
    if len(pot_file) != 0:
        plugin_pot_file = plugin_dir + plugin_domain_path + "/" + v

if len(plugin_pot_file) == 0:
    print("翻译模板文件生成失败")
    exit(_POT_FILE_NOT_FOUND)

# 读取WordPress插件目录中已有插件的名字列表
with open("plugins.txt") as file_obj:
    plugins_txt = file_obj.read()
wp_plugin_name_list = plugins_txt.split("\n")

# 开始翻译流程
po_file_object = polib.pofile(plugin_pot_file)
print(plugin_name + " 插件开始本地化：")

for item in tqdm(po_file_object):
    if item.comment == "Author of the plugin":
        continue

    if item.msgid:
        item.msgstr = translate_str(item.msgid, plugin_name)
    if item.msgid_plural:
        item.msgstr_plural[0] = translate_str(item.msgid, plugin_name)
        item.msgstr_plural[1] = item.msgstr_plural[0]

po_file_object.save("./out/%s-zh_CN.po" % plugin_text_domain)
po_file_object.save_as_mofile("./out/%s-zh_CN.mo" % plugin_text_domain)
