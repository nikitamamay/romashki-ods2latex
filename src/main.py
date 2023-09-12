import sys
import arguments_parser

import zipfile

import xml_parser
import spreadsheet_parser
import calc_object
import tex_constructor


arguments_parser.ARGUMENTS_HELP_MESSAGE = """\
Описание:
    ods2latex - это программа, которая конвертирует таблицу с расчетами,
    выполненными и оформленными особым образом в файле формата ODS (Open
    Document Spreadsheet), в LaTeX-код, представляющий собой человекочитамое
    оформление этих расчетов в неполном (пока) соответствии с нормами ГОСТ 7.32.

Использование:
    python main.py <ods-file> <sheet-name> [-t <tex-file>]

Аргументы:
    <ods-file>
        Путь к ODS-файлу.

    <sheet-name>
        Название листа (sheet) в ODS-файле.

Опции:
    -t
    --tex
        Путь к результирующему tex-файлу.

        По-умолчанию - './data_calc.tex'.


Разработчик: Никита Мамай (nikita@mamay.su).
Екатеринбург, 2023 год."""




# Default
tex_filename: str = "data_calc.tex"


### parsing arguments

class OPTIONS:
    TEX_FILENAME = "tex_filename"

args_positional, options = arguments_parser.ArgumentsParser() \
    .set_min_max_count(2, 2) \
    .add_option_with_one_local_arg(["-t", "--tex"], OPTIONS.TEX_FILENAME) \
    .parse(sys.argv[1:])



use_tex_filename: bool = OPTIONS.TEX_FILENAME in options
if use_tex_filename:
    tex_filename = options[OPTIONS.TEX_FILENAME]


ods_filename: str = args_positional[0]
sheet_name: str = args_positional[1]


### loading the ods file

with zipfile.ZipFile(ods_filename, "r") as file:
    b = file.read("content.xml")
    text = str(b, encoding="utf-8")

### parsing XML

xml = xml_parser.parse_xml(text)


### parsing Spreadsheet

ss: spreadsheet_parser.Spreadsheet = spreadsheet_parser.parse_spreadsheet(xml)

# printing read tables sizes
for t in ss.tables():
    print(t.name(), ":", t.get_row_count(), "x", t.get_column_count())
print()

doc = tex_constructor.Document(ss)


### listing CalcObjects in the target sheet, which specified in argv
co_to_use: list[spreadsheet_parser.Address] = [
    co.address() for co in \
        filter(lambda co: not co.do_not_print(), doc._COF.iterate_calc_objects(sheet_name))
]


### constructing TeX

doc.process(co_to_use)
text = doc.string_fixed_percent()


### writing result in TeX-file

with open(tex_filename, "w", encoding="utf-8") as file:
    written = file.write(text)

print(f"\nWritten {written} bytes in '{tex_filename}'")
