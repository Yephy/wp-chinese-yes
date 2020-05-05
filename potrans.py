import polib
import io
import re
import baidu_trans
import random


class Translator:
    def __init__(self, src_lang=None, dest_lang=None, src_po_file=None):
        self.src_lang = src_lang
        self.dest_lang = dest_lang
        if src_po_file is not None:
            self.open_po_file(src_po_file)

    def open_po_file(self, po_filename):
        if isinstance(po_filename, io.TextIOWrapper):
            po_filename = po_filename.name
        self.po = polib.pofile(po_filename)

    def _translate_str(self, text, src_lang, dest_lang, return_src_if_empty_result=True, need_print=False, exclude=""):
        if not text.strip():
            return ""

        replacers = {}
        exclude_dict = {}
        match_list = re.findall("%[sd]|&[a-z]+;|%[0-9]+|\[.+\]|<.+?>", text)
        if match_list is not None:
            for value in match_list:
                exclude_dict[str(random.randint(0, 264308))] = value

        for (k, v) in exclude_dict.items():
            text = str(text).replace(v, k)

        if exclude != "":
            random_str = str(random.randint(0, 99999))
            exclude_dict[random_str] = exclude
            text = str(text).replace(exclude, random_str)

        tr = baidu_trans.baidu_trans(text, self.src_lang, self.dest_lang)
        if "error_code" not in tr:
            tr_text = tr['trans_result'][0]['dst']
        else:
            tr_text = ""

        if not tr_text and return_src_if_empty_result:
            tr_text = text

        if len(replacers) > 0:
            for r, s in replacers.items():
                tr_text = tr_text.replace(r, s)

        if need_print:
            print(text + " => " + tr_text)

        # 将排除的字符串替换回来
        for (k, v) in exclude_dict.items():
            tr_text = tr_text.replace(k, v)

        return tr_text

    def go_translate(self, src_lang=None, dest_lang=None, debug=False, usemsgid=False, exclude="", **kwargs):
        break_on = kwargs.get("break_on", False)
        if src_lang is None:
            src_lang = self.src_lang
        if dest_lang is None:
            dest_lang = self.dest_lang
        count = len(self.po)
        pos = 0
        prev_percent = -1
        for item in self.po:
            if break_on and break_on == pos:
                break
            pos += 1
            translated = False
            if usemsgid:
                if item.msgid:
                    item.msgstr = self._translate_str(item.msgid, src_lang, dest_lang, True, debug, exclude)
                    translated = True
                if item.msgid_plural:
                    item.msgstr_plural[0] = self._translate_str(item.msgid, src_lang, dest_lang, True, debug, exclude)
                    item.msgstr_plural[1] = item.msgstr_plural[0]
                    translated = True
            if not translated and item.msgstr:
                item.msgstr = self._translate_str(item.msgstr, src_lang, dest_lang, True, debug, exclude)
                if item.msgstr_plural:
                    item.msgstr_plural[0] = self._translate_str(item.msgstr, src_lang, dest_lang, True, debug, exclude)
                    item.msgstr_plural[1] = item.msgstr_plural[0]

            percent = int(pos * 100 / count)
            if percent != prev_percent:
                prev_percent = percent
                print("### Progress: " + str(percent) + "% ###")

    def save_po_file(self, dest_po_file=None):
        if dest_po_file is None:
            dest_po_file = self.dest_po_file
        self.po.save(dest_po_file)

    def save_mo_file(self, dest_mo_file=None):
        if dest_mo_file is None:
            dest_mo_file = self.dest_mo_file
        self.po.save_as_mofile(dest_mo_file)
