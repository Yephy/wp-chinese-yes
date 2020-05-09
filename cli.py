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
@click.option("--output_po", "-o", type=click.Path(file_okay=True, writable=True, dir_okay=False),
              help="Output *.po file to write to")
@click.option("--output_mo", "-om", type=click.Path(file_okay=True, writable=True, dir_okay=False),
              help="Output *.mo file to write to")
def translate(input, output_po="", output_mo=""):
    pot_file = ""
    if input:
        pot_file = pot.get(input)

    if not output_po and not output_mo:
        print("No --output_po or --output_mo specified")
        return

    print("Initializing...")
    t = Translator(pot_file)
    t.go_translate(plugin_info_handle.get_name())
    print("Translation finished")

    if output_po:
        print("Saving po-file to " + output_po)
        t.save_po_file(output_po)
    if output_mo:
        print("Saveing mo-file to " + output_mo)
        t.save_mo_file(output_mo)


@cli.command(help="Convert source *.po file to *.mo")
@click.option("--input_po", "-i", type=click.Path(exists=True), help="Input *.po file to open")
@click.option("--output_mo", "-o", type=click.Path(writable=True), help="Output *.mo file to write to")
def convert(input_po, output_mo):
    print("Reading PO file " + input_po)
    p = polib.pofile(input_po)
    print("Writing MO file " + output_mo)
    p.save_as_mofile(output_mo)
    print("Done")


if __name__ == "__main__":
    cli(obj={})
