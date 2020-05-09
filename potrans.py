import unicodedata
import polib
import io
import re
import baidu_trans
import random
from tqdm import tqdm


class Translator:
    def __init__(self, src_po_file=None):
        if src_po_file is not None:
            self.open_po_file(src_po_file)

    def open_po_file(self, po_filename):
        if isinstance(po_filename, io.TextIOWrapper):
            po_filename = po_filename.name
        self.po = polib.pofile(po_filename)

    def _translate_str(self, text, return_src_if_empty_result=True, exclude=None):
        if not text.strip():
            return ""

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

        tr = baidu_trans.baidu_trans(text, "auto", "zh")
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
