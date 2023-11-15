import sys
import arguments_parser

import zipfile

import xml_parser
import spreadsheet_parser
import calc_object
import tex_constructor
import file_watcher
import time


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

    -w
    --watch
        Следить за изменениями ODS-файла и перезапускать программу в случае
        обновления файла.

    --disable_units_in_equations
        Отключить подстановку единиц измерения при подстановке чисел в формулы.
        Единицы измерения всё равно будут подставляться в формулу, если для неё
        принудительно задано subst_units == 1.


Разработчик: Никита Мамай (nikita@mamay.su).
Екатеринбург, 2023 год."""




# Default
tex_filename: str = "data_calc.tex"


### parsing arguments

class OPTIONS:
    TEX_FILENAME = "tex_filename"
    WATCH_CHANGES = "watch_changes"
    DISABLE_UNITS_IN_EQUATIONS = "disable_units_in_equations"


args_positional, options = arguments_parser.ArgumentsParser() \
    .set_min_max_count(2, -1) \
    .add_option_with_one_local_arg(["-t", "--tex"], OPTIONS.TEX_FILENAME) \
    .add_option_boolean(["-w", "--watch"], OPTIONS.WATCH_CHANGES, True) \
    .add_option_boolean(["--disable_units_in_equations"], OPTIONS.DISABLE_UNITS_IN_EQUATIONS) \
    .parse(sys.argv[1:])



use_tex_filename: bool = OPTIONS.TEX_FILENAME in options
if use_tex_filename:
    tex_filename = options[OPTIONS.TEX_FILENAME]

do_watch_for_changes: bool = OPTIONS.WATCH_CHANGES in options
do_disable_units_in_equations: bool = OPTIONS.DISABLE_UNITS_IN_EQUATIONS in options


ods_filename: str = args_positional[0]
sheet_names: str = args_positional[1:]


def do_action():
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
    doc.cfg_use_units_in_equations = not do_disable_units_in_equations


    ### listing CalcObjects in the target sheet, which specified in argv
    co_to_use: list[spreadsheet_parser.Address] = []
    for sheet_name in sheet_names:
        co_to_use.extend([
            co.address() for co in \
                filter(lambda co: not co.do_not_print(), doc._COF.iterate_calc_objects(sheet_name))
        ])


    ### constructing TeX

    doc.process(co_to_use)
    text = doc.string_fixed_percent()


    ### writing result in TeX-file

    with open(tex_filename, "w", encoding="utf-8") as file:
        written = file.write(text)

    print(f"\nWritten {written} bytes in '{tex_filename}'")


### starting loop

# timestamp of entry's last update
# 0 means that the actions will execute immediately when program is started.
last_updated: int = 0

while True:
    try:
        last_updated_new = file_watcher.check_entry_for_updates(ods_filename, last_updated)

        if last_updated_new > last_updated:
            do_action()

            if not do_watch_for_changes:
                exit(0)

            last_updated = time.time_ns()
            print("=" * 30, end="\n\n")

        time.sleep(1)

    except KeyboardInterrupt:
        exit(0)

    except Exception as e:
        raise e
