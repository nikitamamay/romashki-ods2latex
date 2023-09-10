import re


re_bad_percent = re.compile(r"(?<!\\)%")
re_percent_after_digit = re.compile(r"(?<=\d)\\%")
re_dot_between_digits = re.compile(r"(\d+)\.(\d+)")


def fix_percent(text: str) -> str:
    text = re_bad_percent.sub("\\%", text)
    return text

def escape_tex(text: str) -> str:
    text = text.replace("_", "\\_")
    text = text.replace("$", "\\$")
    text = fix_percent(text)
    return text


def fix_comma(text) -> str:
    return re_dot_between_digits.sub(r"\1,\2", str(text))


def pretty_number(text: 'str|float|int') -> str:
    text = str(text)
    text = fix_percent(text)
    text = fix_comma(text)
    text = text.replace('\u00a0', '')  # удаление пробела при форматировании типа '218 500'
    text = re_percent_after_digit.sub(r"~\%", text)  # добавление пробела перед '%'
    return text


def fancy_tex(text):
    text = fix_comma(text)
    text = text.replace("\\x", " \\cdot ")
    return text


def tex_equation(text):
    return "\\begin{equation*}\n" + text + "\n\\end{equation*}\n"


def tex_inline(text):
    return f"${text}$"


def textbox(text: str) -> str:
    return "\\text{" + text + "}"


# def verb(text: str, char: str="\"") -> str:
#     # return f"\\verb{char}{text}{char}"
#     return f"\\ensuremath{{\\mathtt{{{text}}}}}"
