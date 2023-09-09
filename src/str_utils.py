
WHITESPACE = [" ", "\r", "\n", "\t"]


def check_for_substr_from_start(
		text: str,
        substr: str,
        start_i: int = 0
	    ) -> bool:
	i = start_i
	if text[i] == substr[0]:
		if len(substr) > 1 and i + len(substr) < len(text):
			j = 1
			while j < len(substr):
				if text[i + j] != substr[j]:
					return False
				j += 1
		return True
	return False


def slice_until(
		text: str,
		substrs: list[str],
		start_i: int = 0,
		can_be_escaped: bool = True,
		) -> tuple[str, int]:
	i = start_i

	while i < len(text):
		for s in substrs:
			if check_for_substr_from_start(text, s, i):
				return (text[start_i : i], i + len(s))
		else:
			i += 1

	return (text[start_i : ], len(text))


def slice_until_non_escaped_char(
		text: str,
	    char: list[str],
	    start_i: int = 0
	    ) -> tuple[str, int]:
	i = start_i
	while i < len(text):
		if text[i] in char:
			if i == 0 or (i > 0 and text[i - 1] != "\\"):
				return (text[start_i : i], i + 1)
		i += 1
	return (text[start_i : ], i)


def skip_chars(text: str, chars: list[str], i_start: int = 0) -> int:
	i = i_start
	while i < len(text):
		if not text[i] in chars:
			break
		i += 1
	return i


def find_pair(text: str, pos_start: int):
	i = pos_start
	l: list[str] = [""]
	is_cmd = False
	cmd = ""

	while i < len(text):
		if text[i] == "\\":
			if text[i+1] == "\\":
				l[-1] += "\\"
			else:
				if l[-1] == "": l.pop()
				l.append("\\")
				is_cmd = True
				# cmd += text[i+1]
		elif text[i] == "{":
			l2, i = find_pair(text, i + 1)
			if l[-1] == "": l.pop()
			l.append(l2)
			l.append("")
			# cmd = ""
		elif text[i] == "}":
			if l[-1] == "": l.pop()
			return (l, i)
		else:
			if is_cmd and text[i].isspace():
				is_cmd = False
				if l[-1] == "": l.pop()
				l.append("")
			l[-1] += text[i]
		i += 1

	if l[-1] == "": l.pop()
	return (l, i)


def first_uppercase(text: str) -> str:
	if len(text) > 1:
		return text[0].upper() + text[1:]
	return text



