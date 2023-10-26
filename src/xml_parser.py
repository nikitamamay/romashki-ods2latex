import typing

from html import unescape as html_unescape

import str_utils


def parse_xml(
		text: str
		) -> 'list[Node]':
	"""
		Читает строку с XML.

		Возвращает `list` со всеми `Node`. Де-факто возвращает список XML-элементов, \
		которые являются потомками (`children`) к корню документа. Рекурсивно.
	"""
	result: list[Node] = []

	i = 0
	while i < len(text):
		txt_pre, i = str_utils.slice_until(text, ["<"], i)

		if txt_pre != "":
			result.append(NodeText(html_unescape(txt_pre)))

		tag_all, i = str_utils.slice_until(text, [">"], i)

		tag, tag_i = str_utils.slice_until(tag_all, [" ", ">"])
		tag_options, tag_i = str_utils.slice_until(tag_all, ["/>", ">"], tag_i)

		if tag != "":
			if tag_all.endswith("/"):
				result.append(NodeTag(tag, NodeTag.parse_options(tag_options)))
			elif tag_all.startswith("?"):
				# result.append(NodeTag(tag, NodeTag.parse_options(tag_options)))
				pass
			else:
				tag_end = f"</{tag}>"
				inner, i = str_utils.slice_until(text, [tag_end], i)
				node = NodeTag(tag, NodeTag.parse_options(tag_options))
				node.children = parse_xml(inner)
				result.append(node)

	return result


def pretty_print_xml(nodes: 'list[Node]', tab: int = 0) -> None:
	"""
		Печатает с помощью `print()` дерево XML-документов. Рекурсивно.
	"""
	for n in nodes:
		if isinstance(n, NodeText):
			print("\t" * tab, n, sep="")
		elif isinstance(n, NodeTag):
			print("\t" * tab, n.tag_open(), sep="")
			pretty_print_xml(n.children, tab + 1)


def iterate_tags(l: 'list[Node]') -> 'typing.Iterator[NodeTag]':
	"""
		Итерирует тэги из массива XML-элементов, пропуская текстовые элементы.
	"""
	for node in l:
		if isinstance(node, NodeTag):
			yield node

def iterate_text(l: 'list[Node]') -> 'typing.Iterator[str]':
	"""
		Итерирует строки текста, извлекая их из текстовых XML-элементов и \
		из текстовых элементов-потомков тэговых элементов. Рекурсивно.
	"""
	for node in l:
		if isinstance(node, NodeText):
			yield node.text
		if isinstance(node, NodeTag):
			for n in iterate_text(node.children):
				yield n



class Node():
	"""
		Интерфейс элемента XML (тэга или текста между открывающим \
		и закрывающим тэгами).
	"""
	def __init__(self) -> None:
		self.children: list[Node] = []


class NodeText(Node):
	"""
		Элемент XML, представляющий текст (`text`) между открывающим \
		и закрывающим тэгами.
	"""
	def __init__(self, text: str = "") -> None:
		super().__init__()
		self.text: str = text

	def __repr__(self) -> str:
		return repr(self.text)


class NodeTag(Node):
	"""
		Элемент XML, представляющий тэг с именем (`name`), опциями (`options` - \
		словарь с названиями опций и их значениями) и потомками (`children` - \
		массив XML-элементов между открывающим и закрывающим тэгами).
	"""
	def __init__(self, name: str, options: dict[str, str]) -> None:
		super().__init__()
		self.name: str = name
		self.options: dict[str, str] = options

	def has_option(self, name: str) -> bool:
		return name in self.options

	def get_option(self, name: str, default_value = "") -> str:
		if self.has_option(name):
			return self.options[name]
		return default_value

	@staticmethod
	def parse_options(text: str) -> dict[str, str]:
		options = {}
		i = str_utils.skip_chars(text, str_utils.WHITESPACE, 0)
		while i < len(text):
			opt_name, i = str_utils.slice_until_non_escaped_char(text, ["="], i)
			schar = text[i]
			opt_value, i = str_utils.slice_until_non_escaped_char(text, [schar], i + 1)
			i = str_utils.skip_chars(text, str_utils.WHITESPACE, i)

			opt_name = html_unescape(opt_value)
			opt_value = html_unescape(opt_value)

			options[opt_name] = opt_value
		return options


	def __repr__(self) -> str:
		if len(self.children) == 0:
			return f'<{self.name} {self.options} />'
		return f'<{self.name} {self.options}>{repr(self.children)}</{self.name}>'

	def tag_open(self) -> str:
		return f'<{self.name} {self.options}{" /" if len(self.children) == 0 else ""}>'

	def tag_close(self) -> str:
		if len(self.children) == 0:
			return ""
		return f'</{self.name}>'

