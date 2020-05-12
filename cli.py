import pot
import sys
import plugin_info_handle
from potrans import Translator

pot_file = pot.get(sys.argv[1])

plugin_info_handle.get_official_language_package()

t = Translator(pot_file)
t.go_translate(plugin_info_handle.get_name())

t.save_po_file("./out/%s-zh_CN.po" % (plugin_info_handle.get_text_domain()))
t.save_mo_file("./out/%s-zh_CN.mo" % (plugin_info_handle.get_text_domain()))
