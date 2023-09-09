import typing
import functools  # for @cache on functions

import xml_parser
import re


def parse_spreadsheet(nodes: list[xml_parser.Node]) -> 'Spreadsheet':
	"""
		Читает массив с XML-элементами.

		Возвращает Таблицу (`Spreadsheet`).

		Рекурсивно.
	"""
	spreadsheet = Spreadsheet()

	for node in xml_parser.iterate_tags(nodes):
		if node.name == "table:table":
			spreadsheet.set_table(_parse_table(node))
		elif node.name == "table:named-expressions":
			for ne in _parse_named_exprs(node):
				spreadsheet.set_named_expression(ne)
		else:
			ss: Spreadsheet = parse_spreadsheet(node.children)
			for t in ss.tables():
				spreadsheet.set_table(t)
			for ne in ss.named_expressions():
				spreadsheet.set_named_expression(ne)

	return spreadsheet


class Address():
	"""
		Адрес ячейки (`Cell`) в таблице (`Spreadsheet`) по стандарту ODS (Open \
		Type Document Spreadsheet), как в LibreOffice Calc.

		Ссылается на лист (`sheet`), номер строки (`row`) и номер столбца \
		(`column`).

		Нумерация строк и столбцов в реализации класса - с нуля 0. \
		При возврате текстового представления адреса через `get_text()` \
		(и `__str__()`) нумерация строк (`row`) - с единицы 1.
	"""
	def __init__(self, sheet: str, row: int, column: int) -> None:
		super().__init__()
		self._sheet: str = sheet
		self._row: int = row
		self._column: int = column

	@staticmethod
	def from_text(address_text: str) -> 'Address':
		if not "." in address_text:
			raise Exception(f"Bad address: {repr(address_text)}")

		address_text = address_text.replace("$", "")
		sheet, cell = address_text.split(".", 1)
		i = 0
		while i < len(cell):
			if cell[i].isnumeric():
				break
			i += 1
		column_name = cell[:i]
		row_name = cell[i:]

		column = Address.get_column_number(column_name)
		row = int(row_name) - 1

		return Address(sheet, row, column)

	@staticmethod
	def get_column_name(number: int) -> str:
		if number < 26:
			return "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[number]
		else:
			div = number // 26 - 1
			mod = number % 26
			return Address.get_column_name(div) + Address.get_column_name(mod)

	@staticmethod
	def get_column_number(s: str) -> int:
		i = 0
		for letter in s.upper():
			i *= 26
			i += "ABCDEFGHIJKLMNOPQRSTUVWXYZ".index(letter) + 1
		return i - 1

	def copy(self, sheet: 'str|None' = None, row: 'int|None' = None, column: 'int|None' = None):
		"""
			Возвращает новый объект `Address` - копию `self` с изменениями или без таковых.

			Переданные аргументы меняют соответствующие свойства возвращаемого объекта.
		"""
		return Address(
			self.sheet() if sheet is None else sheet,
			self.row() if row is None else row,
			self.column() if column is None else column,
		)


	# def __hash__(self) -> int:  # FIXME # Нужно ли вообще? - это для @functools.cache
	# 	return self.__str__().__hash__()

	def __eq__(self, __value: object) -> bool:
		if isinstance(__value, Address):
			return self._sheet == __value._sheet \
				and self._row == __value._row \
				and self._column == __value._column
		raise Exception(f"Cannot compare {self.__class__} with {__value.__class__}")

	def get_row_address(self) -> 'Address':
		"""
			Возвращает адрес ячейки на этом же листе на той же строке, но с номером \
			столбца `0`.
		"""
		return Address(self._sheet, self._row, 0)

	def get_text(self) -> str:
		return f'{self.sheet()}.{Address.get_column_name(self.column())}{self.row() + 1}'

	def sheet(self) -> str:
		return self._sheet

	def row(self) -> int:
		return self._row

	def column(self) -> int:
		return self._column

	def __str__(self) -> str:
		return self.get_text()

	def __repr__(self) -> str:
		return f'<Address {self.get_text()}>'


class NamedExpression():
	"""
		Именованное выражение, то есть альтернативное имя (`name`) для ячейки \
		по адресу (`address`) в таблице ODS/LibreOffice Calc.
	"""
	def __init__(self, name: str, address: Address) -> None:
		self._name: str = name
		self._address: Address = address

	def name(self) -> str:
		return self._name

	def address(self) -> Address:
		return self._address


class Cell():
	"""
		Ячейка таблицы.
	"""
	def __init__(self) -> None:
		self._value: float = 0
		self._value_type: str = ""
		self._formula: str = ""
		self._text: str = ""

	def init(self, value: float, formula: str = "", text: str = "", value_type: str = ""):
		self._value = value
		self._value_type = value_type
		self._formula = formula
		self._text = text

	def is_empty(self) -> bool:
		return self._text == ""

	def __repr__(self) -> str:
		return f'<Cell: {self._text} | {self._value} | {self._formula}>'

	def text(self) -> str:
		return self._text

	def value(self) -> float:
		return self._value

	def formula(self) -> str:
		return self._formula


class Table():
	"""
		Таблица (точнее, Лист) в Spreadsheet.
	"""
	def __init__(self) -> None:
		self._name: str = ""
		self._cells: dict[int, dict[int, Cell]] = {}
		# self._named_exprs: list[NamedExpression] = []

		# self._COs_cache: dict[int, CalcObject] = {}  # cache
		# self._columns: dict[str, int] = {
		# 	"data": -1,
		# 	"texput": -1,
		# 	"unit_texput": -1,
		# 	"tex_equation": -1,
		# 	"description": -1,
		# 	"is_known": -1,
		# 	"is_constant": -1,
		# 	"do_not_print": -1,
		# 	# "is_disabled": -1,
		# 	"source": -1,
		# 	"source_name": -1,
		# 	"source_aux": -1,
		# }

	# def init_header_row(self) -> None:
	# 	for i in range(self.get_column_count()):
	# 		c = self.get_cell(0, i)
	# 		if c.text() in self._columns:
	# 			self._columns[c.text()] = i

	# def clear_cache(self) -> None:
	# 	self._COs_cache.clear()

	def name(self) -> str:
		return self._name

	def set_cell(self, row: int, column: int, cell: Cell) -> None:
		if not row in self._cells:
			self._cells[row] = {}
		self._cells[row][column] = cell

	# @functools.cache
	def get_cell(self, row: int, column: int) -> 'Cell':
		if row < 0 or not row in self._cells or column < 0 or not column in self._cells[row]:
			return Cell()
		return self._cells[row][column]

	def get_row_count(self) -> int:
		if len(self._cells.keys()) == 0:
			return 0
		return max(self._cells.keys()) + 1

	def get_column_count(self) -> int:
		result = 0
		for row_i in self._cells:
			result = max(result, *self._cells[row_i].keys())
		return result + 1

	def is_empty(self) -> bool:
		return self.get_row_count() == 0

	# def get_calc_object(self, row: int) -> CalcObject:
	# 	if not row in self._COs_cache:
	# 		addr = Address(self._name, row, 0)
	# 		co = CalcObject(addr)

	# 		c_data = self.get_cell(row, self._columns["data"])
	# 		text = c_data.text()
	# 		texput = self.get_cell(row, self._columns["texput"]).text()

	# 		if text == "" and texput == "":
	# 			return co

	# 		# FIXME убирать неразрывный пробел, только если value_type = float и т.п., но не для текста!
	# 		text = text.replace("\u00a0", "")  # неразрывный пробел в написании числа

	# 		value = c_data.value()
	# 		formula = c_data.formula()
	# 		description = self.get_cell(row, self._columns["description"]).text()
	# 		unit_texput = self.get_cell(row, self._columns["unit_texput"]).text()
	# 		tex_equation = self.get_cell(row, self._columns["tex_equation"]).text()
	# 		is_known = self.get_cell(row, self._columns["is_known"]).text()
	# 		is_constant = self.get_cell(row, self._columns["is_constant"]).text()
	# 		do_not_print = self.get_cell(row, self._columns["do_not_print"]).text()
	# 		source = self.get_cell(row, self._columns["source"]).text()
	# 		source_name = self.get_cell(row, self._columns["source_name"]).text()
	# 		source_aux = self.get_cell(row, self._columns["source_aux"]).text()

	# 		co._text = text
	# 		co._value = value
	# 		co._formula = formula

	# 		co._description = description

	# 		co._texput = texput if texput != "" \
	# 			else f'\\text{{{fix_percent(addr.get_text())}}}'

	# 		co._unit_texput = unit_texput

	# 		co._tex_equation = tex_equation

	# 		co._is_known = is_known != ""
	# 		co._treat_as_constant = is_constant != ""
	# 		co._do_not_print = do_not_print != ""

	# 		if self._columns["source_name"] != -1:
	# 			co._source_name = source_name
	# 			co._source_aux = source_aux
	# 		else:
	# 			_i = source.find(",")
	# 			if _i != -1:
	# 				co._source_name = source[:_i].strip()
	# 				co._source_aux = source[_i + 1:].strip()
	# 			else:
	# 				co._source_name = source.strip()

	# 		self._COs_cache[row] = co

	# 	return self._COs_cache[row]

	# def get_named_exprs(self) -> list[NamedExpression]:
	# 	return self._named_exprs

	# def iterate_calc_objects(self) -> typing.Iterator[CalcObject]:
	# 	for i in range(1, self.get_row_count()):
	# 		co = self.get_calc_object(i)
	# 		if not co.is_empty():
	# 			yield co

	def to_tsv(self) -> str:
		result = ""
		rows = self.get_row_count()
		cols = self.get_column_count()
		for i in range(rows):
			result += "\t".join([repr(self.get_cell(i, j).text()) for j in range(cols)])
			result += "\n"
		return result


class Spreadsheet():
	"""
		Набор таблиц (листов) (`Table`) и именованных выражений (`NamedExpression`).
	"""
	def __init__(self) -> None:
		self._sheets: dict[str, Table] = {}
		self._named_exprs: dict[str, NamedExpression] = {}

	def get_cell(self, addr: Address) -> Cell:
		return self.get_table(addr.sheet()).get_cell(addr.row(), addr.column())

	# def get_calc_object(self, addr: Address) -> CalcObject:
	# 	return self.get_table(addr.sheet()).get_calc_object(addr.row())

	def get_table(self, table_name: str) -> Table:
		if table_name in self._sheets:
			return self._sheets[table_name]
		return Table()

	def tables(self) -> list[Table]:
		return self._sheets.values()

	def set_table(self, t: Table) -> None:
		self._sheets[t.name()] = t

	def set_named_expression(self, ne: NamedExpression) -> None:
		self._named_exprs[ne.name()] = ne

	def get_named_expression(self, name: str) -> NamedExpression:
		if not self.has_named_expression(name):
			raise Exception(f"There is no NamedExpression '{name}' in {repr(self)}")
		return self._named_exprs[name]

	def has_named_expression(self, name: str) -> bool:
		return name in self._named_exprs

	def named_expressions(self) -> list[NamedExpression]:
		return self._named_exprs.values()

	# def get_dependent_cells(self, formula_text: str, self_sheet: str) -> list[Address]:
	# 	cells, NEs = get_dependent_cells_and_NEs(formula_text)
	# 	cells = [(self_sheet + name if name.startswith(".") else name).replace("$", "") for name in cells]

	# 	addresses: list[Address] = []
	# 	for addr in map(lambda c: Address.from_text(c), cells):
	# 		if not addr in addresses:
	# 			addresses.append(addr)

	# 	for ne in NEs:
	# 		try:
	# 			addr = self.get_named_expression(ne).address()
	# 			if not addr in addresses:
	# 				addresses.append(addr)
	# 		except Exception as e:
	# 			# print(e)
	# 			pass

	# 	return addresses

	# def get_dependent_cells_in_order(self, formula_text: str, self_sheet: str) -> list[Address]:
	# 	names = get_dependent_names_in_order(formula_text)

	# 	addresses: list[Address] = []
	# 	for name in names:
	# 		if name.startswith("["):  # Cell name
	# 			name = ("[" + self_sheet + name[1:] if name.startswith("[.") else name)[1:-1].replace("$", "")
	# 			addr = Address.from_text(name)
	# 			if not addr in addresses:
	# 				addresses.append(addr)
	# 		else:  # NamedExpression name
	# 			try:
	# 				addr = self.get_named_expression(name).address()
	# 				if not addr in addresses:
	# 					addresses.append(addr)
	# 			except Exception as e:
	# 				# print(e)
	# 				pass

	# 	return addresses

	# def get_dependent_cells_for(self, addr: Address) -> list[Address]:
	# 	co = self.get_calc_object(addr)
	# 	return self.get_dependent_cells(co.formula(), addr.sheet())

	# def get_dependent_cells_in_order_for(self, addr: Address) -> list[Address]:
	# 	co = self.get_calc_object(addr)
	# 	return self.get_dependent_cells_in_order(co.formula(), addr.sheet())




def _parse_cell(
		table: Table,
		node: xml_parser.NodeTag,
		row_counter: int,
		column_counter: int
		) -> int:
	col_span = int(node.get_option("table:number-columns-repeated", "1"))

	text = ""

	cell = Cell()
	for n in xml_parser.iterate_tags(node.children):
		if n.name == "text:p":
			text += " " + "".join(xml_parser.iterate_text(n.children)).strip()

	text = text.strip()

	s_value = node.get_option("office:value", "")
	value_type = node.get_option("office:value-type", "")
	formula = node.get_option("table:formula", "of:=")[4:]

	try:
		value = float(s_value)
	except Exception as e:
		value = 0

	cell.init(value, formula, text, value_type)

	if not cell.is_empty():
		for i in range(col_span):
			table.set_cell(row_counter, column_counter + i, cell)

	return column_counter + col_span


def _parse_rows(table: Table, node: xml_parser.NodeTag, row_counter: int) -> int:
	row_span = int(node.get_option("table:number-rows-repeated", "1"))

	if row_span == 1:
		column_counter = 0
		for cell in xml_parser.iterate_tags(node.children):
			column_counter = _parse_cell(table, cell, row_counter, column_counter)

	return row_counter + row_span


def _parse_table(table_tag: xml_parser.NodeTag) -> Table:
	table = Table()
	row_counter: int = 0

	table._name = table_tag.get_option("table:name", "")

	for node in xml_parser.iterate_tags(table_tag.children):
		if node.name == "table:table-row":
			row_counter = _parse_rows(table, node, row_counter)

	return table


def _parse_named_exprs(tag_ne: xml_parser.NodeTag):
	NEs: list[NamedExpression] = []
	for node in xml_parser.iterate_tags(tag_ne.children):
		if node.name == "table:named-range":
			name = node.get_option("table:name", "")
			addr = Address.from_text(node.get_option("table:cell-range-address", ""))
			ne = NamedExpression(name, addr)
			NEs.append(ne)
		else:
			raise Exception("Unknown tag: " + repr(node))
	return NEs

