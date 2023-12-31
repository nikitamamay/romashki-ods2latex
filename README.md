# romashki-ods2latex

`romashki-ods2latex` - это программа, которая конвертирует таблицу с расчетами, выполненными и оформленными особым образом в файле формата ODS (Open Document Spreadsheet), в LaTeX-код, представляющий собой человекочитамое оформление этих расчетов в неполном (пока) соответствии с нормами ГОСТ 7.32.


## Использование

Вызов в командной строке:
    `python main.py <ods-file> <sheet-name> [-t <tex-file>]`

Аргументы:
* `<ods-file>`
    Путь к ODS-файлу.

* `<sheet-name>`
    Название листа (sheet) в ODS-файле.

Опции:
* `-t`, `--tex` `<tex-file>`
  Путь к результирующему tex-файлу.
  По-умолчанию - `./data_calc.tex`.


### Логика работы 

...

### Требования к ODS-файлу 

...


## Пример использования

Для ознакомления с функционалом программы и его проверки при разработке создана папка `tests/` со следующим содержимым:
* `tests/calc.ods` - исходный файл ODS;
* `tests/data_calc_raw.tex` - результирующий файл TeX (после запуска `tests/launch.bat`);
* `tests/tex/main.pdf` - PDF для просмотра (после компиляции `tests/tex/main.tex`).

Порядок работы с программой предполагает первоначальный запуск конвертации ODS -> LaTeX с помощью `tests/launch.bat`, а затем компиляция LaTeX -> PDF с помощью `tests/tex/latex_compile.bat`.


## Об авторе

Разработчик: Никита Мамай (nikita@mamay.su).
