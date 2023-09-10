import typing
import re

import spreadsheet_parser as sp
import calc_object as calc_object
import tex_utils
import str_utils
import math_utils


class Document():
    def __init__(self, spreadsheet: sp.Spreadsheet) -> None:
        self._spreadsheet: sp.Spreadsheet = spreadsheet
        self._COF: calc_object.CalcObjectsFactory = calc_object.CalcObjectsFactory(spreadsheet)

        self._known: list[sp.Address] = []
        self._equation_known: list[sp.Address] = []
        self._calculated: list[sp.Address] = []
        self._to_calculate: list[sp.Address] = []  # only which are CalcObject.is_equation()
        self._to_process: list[sp.Address] = []

        self._string: str = ""
        self._current_tabulation: int = 0

        self.cfg_use_equation_numbers: bool = True
        self.cfg_always_write_where: bool = False
        self.cfg_allow_symbolic_and_numeric_equation: bool = True
        self.cfg_use_units: bool = True
        self.cfg_default_digits_count: int = 3
        # self.cfg_max_depth_of_fast_calc: int = 0

    def string(self) -> str:
        return self._string

    def string_fixed_percent(self) -> str:
        return tex_utils.fix_percent(self._string)  # FIXME

    def is_known(self, addr: sp.Address) -> bool:
        return self._COF.get_calc_object(addr).is_known() or addr.copy(column=0) in self._known

    def is_equation_known(self, addr: sp.Address) -> bool:
        return addr.copy(column=0) in self._equation_known

    def is_calculated(self, addr: sp.Address) -> bool:
        return addr.copy(column=0) in self._calculated or self._COF.get_calc_object(addr).is_constant()

    def set_known(self, addr: sp.Address) -> None:
        self._known.append(addr.copy(column=0))

    def set_equation_known(self, addr: sp.Address) -> None:
        self._equation_known.append(addr.copy(column=0))

    def set_calculated(self, addr: sp.Address) -> None:
        self._calculated.append(addr.copy(column=0))

    @staticmethod
    def get_label(addr: sp.Address) -> str:
        return "l_" + str(addr)

    def append_text(self, s: str) -> str:
        new_s = ""
        for line in s.splitlines(True):
            new_s += '\t' * self._current_tabulation + line
        self._string += new_s
        return new_s


    def text_text(self, co: calc_object.CalcObject) -> str:
        ifdescription = co.description()
        iftext = co.text()
        ifsep = " --- " if (len(ifdescription) > 0 and len(iftext) > 0) else ""
        return f'{str_utils.first_uppercase(ifdescription)}{ifsep}{iftext}\n'

    def text_constant(self, co: calc_object.CalcObject) -> str:
        ifsource = " " + self.text_cite(co.source_name(), co.source_aux()) if co.source_name() != "" else ""
        ifunit = "" if co.unit_texput() == "" else f' \\text{{~{co.unit_texput()}}}'
        return f'{str_utils.first_uppercase(co.description())} ${co.texput()} = {self.text_value(co, True)}{ifunit}${ifsource}.\n'

    def text_where_line(self, co: calc_object.CalcObject) -> str:
        ifunit = "" if co.unit_texput() == "" else f' \\text{{~{co.unit_texput()}}}'
        ifvalue = f' = {self.text_value(co, True)}{ifunit}' if co.is_constant() else ""
        ifsource = " " + self.text_cite(co.source_name(), co.source_aux()) if co.source_name() != "" and co.is_constant() else ""
        return f'${co.texput()}{ifvalue}$ --- {co.description()}{ifsource}'

    def text_equation_symbolic(self, co: calc_object.CalcObject, with_number: bool = False, with_comma: bool = False) -> str:
        ifsource = " " + self.text_cite(co.source_name(), co.source_aux()) if co.source_name() != "" else ""
        ifcomma = "," if with_comma else "."
        ifnumber = "equation" if with_number else "equation*"
        iflabel = f'\n\t\\label{{{Document.get_label(co.address())}}}' if with_number else ""
        return f'{str_utils.first_uppercase(co.description())} --- по формуле{ifsource}:\n\\begin{{{ifnumber}}}\n' \
            + f'\t{co.texput()}\n\t= {self.subst_symbols(co)}\n\t{ifcomma}{iflabel}\n\\end{{{ifnumber}}}\n'

    def text_equation_symbolic_numeric(
            self,
            co: calc_object.CalcObject,
            is_together: bool = True,
            with_number: bool = False,
            with_comma: bool = False
            ) -> str:
        ifsource = " " + self.text_cite(co.source_name(), co.source_aux()) if co.source_name() != "" else ""
        ifunit = "" if co.unit_texput() == "" else f' \\text{{~{co.unit_texput()}}}'
        ifcomma = "," if with_comma else "."
        ifstar = "" if with_number else "*"
        iflabel = f'\n\t\\label{{{Document.get_label(co.address())}}}' if with_number else ""
        ifnotag = f'\n\t\\notag' if with_number else ""
        if with_number or not is_together:
            return f'{str_utils.first_uppercase(co.description())} --- по формуле{ifsource}:\n\\begin{{gather{ifstar}}}\n' \
                + f'\t{co.texput()}\n\t= {self.subst_symbols(co)}\n\t,{iflabel}\n\t\\\\\n\t{co.texput()}\n\t= {self.subst_numbers(co)}\n' \
                + f'\t= {self.text_value(co, True)}{ifunit}{ifcomma}{ifnotag}\n\\end{{gather{ifstar}}}\n'
        else:
            return f'{str_utils.first_uppercase(co.description())} --- по формуле{ifsource}:\n\\begin{{equation{ifstar}}}\n'\
                + f'\t{co.texput()}\n\t= {self.subst_symbols(co)}\n\t= {self.subst_numbers(co)}\n'\
                + f'\t= {self.text_value(co, True)}{ifunit}{ifcomma}{iflabel}\n\\end{{equation{ifstar}}}\n'

    def text_equation_numeric(self, co: calc_object.CalcObject, with_comma: bool = False) -> str:
        ifcomma = "," if with_comma else "."
        ifunit = "" if co.unit_texput() == "" else f' \\text{{~{co.unit_texput()}}}'
        return f'{str_utils.first_uppercase(co.description())} --- расчет значения по формуле (\\ref{{{Document.get_label(co.address())}}}):\n\\begin{{equation*}}\n'\
                + f'\t{co.texput()}\n\t= {self.subst_numbers(co)}\n'\
                + f'\t= {self.text_value(co, True)}{ifunit}{ifcomma}\n\\end{{equation*}}\n'

    def text_where(self, addresses: list[sp.Address]) -> str:
        s = "где "
        str_join = ";\n\\\\ \\phantomwhere "
        for addr in addresses:
            s += self.text_where_line(self._COF.get_calc_object(addr)) + str_join
        s = s[ : -len(str_join)]
        s += ".\n"
        return s

    def text_value(self, co: calc_object.CalcObject, multiply_percentage_100: bool = True) -> str:
        if co.value() is None or (co.is_constant()):
            if not multiply_percentage_100:
                value = co.value()
            else:
                value = co.text()
        else:
            dc = co.digits_count() if co.digits_count() != -1 else self.cfg_default_digits_count
            use_percents = (co.value_type() == "percentage" and multiply_percentage_100)
            v = co.value() * (100 if use_percents else 1)
            value = math_utils.round_digits_str(v, dc) + ("\\%" if use_percents else "")
        return tex_utils.pretty_number(value)

    def text_cite(self, cite_name: str, cite_aux: str = "") -> str:
        if cite_aux == "":
            return f'\\cite{{{cite_name}}}'
        return f'\\cite[{cite_aux}]{{{cite_name}}}'


    def subst_symbols(self, co: calc_object.CalcObject) -> str:
        s = co.tex_equation()
        s = tex_utils.fix_comma(s)

        s = re.sub(r'\\x\b', " ", s)
        s = s.replace("PI()", "\\pi")

        addresses: list[sp.Address] = self._COF.get_dependent_addresses_in_order(co.formula(), co.address().sheet())[1]
        for i in range(len(addresses) - 1, -1, -1):
            co = self._COF.get_calc_object(addresses[i])
            substr = "#" + str(i + 1)
            t = co.texput()
            s = s.replace(substr, t)
        return s

    def subst_numbers(self, co: calc_object.CalcObject) -> str:
        s = co.tex_equation()
        s = tex_utils.fix_comma(s)

        s = re.sub(r'\\x\b', "\\\\cdot", s)

        # ВМЕСТО \pi или PI() использовать NamedExpression Pi, которое is_known=1, is_constant=1, data="of:=PI()" и texput=\pi
        s = re.sub(r'\\pi\b', "3,14", s)  # FIXME а если это просто индекс?
        s = s.replace("PI()", "3,14")

        addresses: list[sp.Address] = self._COF.get_dependent_addresses_in_order(co.formula(), co.address().sheet())[1]
        for i in range(len(addresses) - 1, -1, -1):
            co = self._COF.get_calc_object(addresses[i])
            substr = "#" + str(i + 1)
            ifunit = "" if co.unit_texput() == "" else f' \\text{{~{co.unit_texput()}}}'
            t = self.text_value(co, False) + (ifunit if self.cfg_use_units else "")
            s = s.replace(substr, t)
        return s

    def process(self, co_to_process: typing.Iterable[sp.Address]) -> None:
        self._to_process = iter(co_to_process)

        addr = self._next_in_process_queue()
        while not addr is None:
            co = self._COF.get_calc_object(addr)

            s = self._process_CO(co)

            if s != "":
                s += "\n"
                self.append_text(s)
                # print(s, end="")

            addr = self._next_in_process_queue()

    def _next_in_process_queue(self) -> 'sp.Address|None':
        i = len(self._to_calculate) - 1
        while i >= 0:
            addr = self._to_calculate[i]

            # if len(self.get_uncalculated_for(addr)) == 0:
            # 	return self._to_calculate.pop(i)

            return self._to_calculate.pop(i)

            # i -= 1

        try:
            return next(self._to_process)
        except StopIteration as e:
            return None


    def _process_CO(self, co: calc_object.CalcObject) -> str:
        s = ""
        addr = co.address()

        if co.value_type() in ["float", "percentage"]:
            if co.is_constant():
                if self.is_known(addr):
                    # print(co.address(), "is known; skipping it.")
                    pass
                else:
                    s += self.text_constant(co)
                    self.set_known(addr)

            else:  # is_equation()
                # not known
                #	or known, but not equation_known
                # known, equation_known, but not calculated, can be calculated
                # known, equation_known, but not calculated, cannot be calculated = skip
                # known, equation_known, calculated = skip

                try:
                    if self.is_calculated(addr):
                        if not self.is_known(addr):
                            # can this case appear in real?
                            s += self.text_constant(co)
                            self.set_known(addr)
                        else:
                            pass
                    else:
                        dependent: list[sp.Address] = self._COF.get_dependent_addresses_in_order(co.formula(), addr.sheet())[1]

                        unknown: list[sp.Address] = list(filter(lambda el: not self.is_known(el), dependent))  # if not self.cfg_always_write_where else dependent
                        uncalculated: list[sp.Address] = list(filter(lambda el: not self.is_calculated(el), unknown))

                        to_write_where: bool = len(unknown) > 0
                        can_be_calculated: bool = len(uncalculated) == 0

                        if can_be_calculated:
                            if self.is_equation_known(addr):
                                s += self.text_equation_numeric(co, False)
                                self.set_calculated(addr)
                            else:
                                s += self.text_equation_symbolic_numeric(co, self.cfg_allow_symbolic_and_numeric_equation, self.cfg_use_equation_numbers, to_write_where)
                                self.set_known(addr)
                                self.set_equation_known(addr)
                                self.set_calculated(addr)

                                if to_write_where:
                                    s += self.text_where(unknown)
                                    [self.set_known(a) for a in unknown]
                        else:
                            if self.is_equation_known(addr):
                                self._to_calculate.insert(-1, co.address())  # append() leads to infinite loop!
                                pass
                                print("Warning: Trying", co.address(),"- equation_known, but cannot be calculated because of these:", uncalculated)
                            else:
                                s += self.text_equation_symbolic(co, self.cfg_use_equation_numbers, to_write_where)
                                self.set_known(addr)
                                self.set_equation_known(addr)

                                self._to_calculate.append(co.address())

                                if to_write_where:
                                    s += self.text_where(unknown)

                                    [self.set_known(a) for a in unknown]

                                    # reversed() здесь потому, что self._to_calculate итерируется в обратном порядке (с конца).
                                    [self._to_calculate.append(_co.address()) for _co in \
                                        reversed(list(
                                            filter(lambda _co: _co.is_equation(),
                                                map(lambda a: self._COF.get_calc_object(a), unknown)
                                            )
                                        ))
                                    ]
                except Exception as e:
                    import traceback
                    print("_process_CO():", co.address(), "---", e, traceback.format_exc())
        elif co.value_type() in ["string", ""]:
            self.set_known(addr)
            s += self.text_text(co)
        else:
            raise Exception(f"Unknown value_type: {repr(co.value_type())} ({addr})")
        return s

