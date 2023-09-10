import typing
import functools
import re

import tex_utils
import str_utils
import spreadsheet_parser as sp


# RegExp на ссылку на другую ячейку
re_cell = re.compile(r'(?<=\[)[\s\S]+?(?=\])', re.I)

# RegExp на ссылку на именованное выражение
re_named_expr = re.compile(r'(?!=\[)\b(?!\d)\w+?\b(?!\])', re.I)

# RegExp на ссылки на другую ячейку или на именованное выражение
re_dependent_name = re.compile(r'\[[\s\S]+?\]|(?!=\[)\b(?!\d)\w+?\b(?!\])', re.I)

# RegExp на знак умножения в формулах
re_star = re.compile(r'\s*\*\s*', re.I)


class Headers:
	data = "data"
	texput = "texput"
	unit_texput = "unit_texput"
	tex_equation = "tex_equation"
	description = "description"
	is_known = "is_known"
	is_constant = "is_constant"
	do_not_print = "do_not_print"
	is_disabled = "is_disabled"
	source = "source"
	source_name = "source_name"
	source_aux = "source_aux"
	digits_count = "digits_count"


class CalcObject():
	"""
		Физическая величина.

		Включает в себя TeX-написания символьного обозначения величины, единицы измерения \
		и записи расчетной формулы; численное значение; описание величины; ссылку на источник и др.
		Может быть как константной, так и расчетной по формуле (в LOCalc).

		Представляется, как правило, строкой на листе таблицы (Spreadsheet) LibreOffice Calc.
	"""
	def __init__(self, address: sp.Address) -> None:
		self._address: sp.Address = address
		self._source_name: str = ""
		self._source_aux: str = ""
		self._description: str = ""
		self._texput: str = ""
		self._unit_texput: str = ""
		self._tex_equation: str = ""

		self._is_disabled: bool = False
		self._is_known: bool = False
		self._is_constant: bool = False
		self._do_not_print: bool = False
		self._digits_count: int = -1

		self._text: str = ""
		self._value: 'float|None' = None
		self._value_type: str = ""
		self._formula: str = ""

	def is_empty(self) -> bool:
		return \
			self._text == "" \
			and self._description == "" \

	def is_equation(self) -> bool:
		return not self.is_constant()

	def is_constant(self) -> bool:
		return self._is_constant

	def is_known(self) -> bool:
		return self._is_known

	def do_not_print(self) -> bool:
		return self._do_not_print

	def address(self) -> sp.Address:
		return self._address

	def source_name(self) -> str:
		return self._source_name

	def source_aux(self) -> str:
		return self._source_aux

	def description(self) -> str:
		return self._description

	def texput(self) -> str:
		return self._texput

	def unit_texput(self) -> str:
		return self._unit_texput

	def tex_equation(self) -> str:
		return self._tex_equation

	def text(self) -> str:
		return self._text

	def value(self) -> 'float|None':
		return self._value

	def value_type(self) -> str:
		return self._value_type

	def formula(self) -> str:
		return self._formula

	def digits_count(self) -> int:
		return self._digits_count


class CalcObjectsFactory():
	def __init__(self, ss: sp.Spreadsheet) -> None:
		super().__init__()
		self._ss: sp.Spreadsheet = ss
		self._warnings: dict[str, int] = {}

	# @functools.cache
	def get_calc_object(self, addr: sp.Address) -> 'CalcObject':
		def get_cell(c: str):
			return self._ss.get_cell(addr.copy(column=self.get_column_number(addr, c)))

		co = CalcObject(addr)

		c_data = get_cell(Headers.data)
		text = c_data.text()
		texput = get_cell(Headers.texput).text()
		description = get_cell(Headers.description).text()

		if text == "" and texput == "" and description == "":  # пустой CalcObject
			return co

		value = c_data.value()
		value_type = c_data.value_type()
		formula = c_data.formula()
		unit_texput = get_cell(Headers.unit_texput).text()
		tex_equation = get_cell(Headers.tex_equation).text()
		is_known = get_cell(Headers.is_known).text()
		is_constant = get_cell(Headers.is_constant).text()
		is_disabled = get_cell(Headers.is_disabled).text()
		do_not_print = get_cell(Headers.do_not_print).text()
		source = get_cell(Headers.source).text()
		source_name = get_cell(Headers.source_name).text()
		source_aux = get_cell(Headers.source_aux).text()
		digits_count = get_cell(Headers.digits_count).text()

		co._text = text
		co._value = value
		co._value_type = value_type
		co._formula = formula

		co._description = description

		if texput != "":
			co._texput = texput
		else:
			co._texput = f'\\text{{{tex_utils.escape_tex(addr.get_text())}}}'
			if value_type in ["float", "percentage"]:
				self.print_warning(f"Warning: no texput for {addr}")

		co._unit_texput = unit_texput

		co._tex_equation = tex_equation if tex_equation != "" \
			else self.ensure_tex_equation(formula, addr.sheet())

		co._is_known = is_known != ""
		co._do_not_print = do_not_print != ""
		co._is_disabled = is_disabled != ""
		co._is_constant = is_constant != "" or formula == "" or not self.has_any_dependency(formula)

		co._digits_count = str_utils.safe_int(digits_count, -1)

		if self.get_column_number(addr, Headers.source_name) != -1:
			co._source_name = source_name
			co._source_aux = source_aux
		else:
			_i = source.find(",")
			if _i != -1:
				co._source_name = source[:_i].strip()
				co._source_aux = source[_i + 1:].strip()
			else:
				co._source_name = source.strip()
		return co

	# @functools.cache
	def get_column_number(self, addr: sp.Address, column_header_name: str, headers_row: int = 0) -> int:
		"""
			Возвращает номер столбца (нумерация с `0`), на пересечении которого \
			со строкой `headers_row` (нумерация с `0`) в ячейке \
			содержится текст `column_header_name`.
		"""
		table: sp.Table = self._ss.get_table(addr.sheet())
		for i in range(table.get_column_count()):
			if table.get_cell(headers_row, i).text() == column_header_name:
				return i
		return -1

	def get_dependent_addresses_in_order(self, formula_text: str, self_sheet: str) -> 'tuple[list[str], list[sp.Address]]':
		names: list[str] = []
		addresses: list[sp.Address] = []

		for name in re_dependent_name.findall(formula_text):
			# Cell name
			if name.startswith("["):
				if ":" in name:
					print(f"Warning: the cell with formula '{formula_text}' depends on range '{name}'. Cannot deal with ranges for now.")  # FIXME
					continue

				full_name = ("[" + self_sheet + name[1:] if name.startswith("[.") else name)[1:-1].replace("$", "")
				addr = sp.Address.from_text(full_name)
				if not addr in addresses:
					addresses.append(addr)
					names.append(name)

			# NamedExpression name
			elif self._ss.has_named_expression(name):
				addr = self._ss.get_named_expression(name).address()
				if not addr in addresses:
					addresses.append(addr)
					names.append(name)

			# Other name
			else:
				pass

		return names, addresses

	def has_any_dependency(self, formula_text: str) -> bool:
		for m in re_dependent_name.finditer(formula_text):
			name: str = m.group(0)
			if name.startswith("[") or self._ss.has_named_expression(name):
				return True
			else:
				pass
		return False

	def ensure_tex_equation(self, formula_text: str, self_sheet: str) -> str:
		names: list[str] = self.get_dependent_addresses_in_order(formula_text, self_sheet)[0]

		for i, name in enumerate(names):
			formula_text = formula_text.replace(name, "#" + str(i + 1))

		formula_text = re.sub(re_star, " \\\\cdot ", formula_text)

		return formula_text

	def iterate_calc_objects(self, sheet_name: str) -> typing.Iterator[CalcObject]:
		sheet = self._ss.get_table(sheet_name)
		if sheet.is_empty():
			raise Exception(f"Bad sheet name: \"{sheet_name}\"")

		for i in range(1, sheet.get_row_count()):
			co = self.get_calc_object(sp.Address(sheet_name, i, 0))
			if not co.is_empty():
				yield co

	def print_warning(self, msg: str) -> None:
		if not msg in self._warnings:
			self._warnings[msg] = 0
			print(msg)
		self._warnings[msg] += 1
