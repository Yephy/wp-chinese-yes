import pot
import sys
import plugin_info_handle
from potrans import Translator

t = Translator(pot.get(sys.argv[1]))
t.go_translate(plugin_info_handle.get_name())

t.save_po_file("./out/%s-zh_CN.po" % (plugin_info_handle.get_text_domain()))
t.save_mo_file("./out/%s-zh_CN.mo" % (plugin_info_handle.get_text_domain()))
