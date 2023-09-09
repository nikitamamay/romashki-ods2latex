import re


def fix_percent(text: str) -> str:
    text = text.replace("%", "\\%")
    return text

def escape_tex(text: str) -> str:
    text = text.replace("_", "\\_")
    text = text.replace("$", "\\$")
    return fix_percent(text)



def fix_comma(text) -> str:
    return re.sub(r"(\d+)\.(\d+)", r"\1,\2", str(text))


def pretty_number(text: 'str|float|int') -> str:
    text = str(text)
    text = fix_comma(text)
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
