import pot
import sys
import plugin_info_handle
from potrans import Translator

t = Translator(pot.get(sys.argv[1]))
t.go_translate(plugin_info_handle.get_name())

t.save_po_file("./out/zh_CN.po")
t.save_mo_file("./out/zh_CN.mo")
