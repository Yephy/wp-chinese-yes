import click
import polib
import pot
import plugin_info_handle
from potrans import Translator


@click.group(help="PoTranslator console tool. Used to translate *.po files."
                  + " To display help on command, use <command> --help")
def cli():
    pass


@cli.command(help="Translate source *.po file from one language to another, and save result as *.po or *.mo file")
@click.option("--input", "-i", default="", type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
              help="Input *.zip file to open")
def translate(input):
    pot_file = ""
    if input:
        pot_file = pot.get(input)

    print("Initializing...")
    t = Translator(pot_file)
    t.go_translate(plugin_info_handle.get_name())
    print("Translation finished")

    t.save_po_file("./out/zh_CN.po")
    t.save_mo_file("./out/zh_CN.mo")


if __name__ == "__main__":
    cli(obj={})
