import str_utils


def _parse_pair(l: 'list[str]') -> str:
	if not isinstance(l, list):
		raise Exception(f"list[str] was expected, got: {repr(l)}")

	s: str = ""

	i = 0
	while i < len(l):
		el = l[i]
		if isinstance(el, str):
			el = el.strip()
			if el.startswith("\\"):
				if el.startswith("\\frac"):
					s += f"({_parse_pair(l[i + 1])})/({_parse_pair(l[i + 2])})"
					i += 3
					continue
				elif el.startswith("\\sqrt"):
					if el == "\\sqrt":
						s += f"math.sqrt({_parse_pair(l[i + 1])})"
					else:
						s += f"({_parse_pair(l[i + 1])})**(1/({el[6:-1]}))"
					i += 2
					continue
				elif el == "\\cdot" or el == "\\x":
					s += "*"
					i += 1
					continue
				elif el == "\\pi":
					s += "math.pi"
					i += 1
					continue
				else:
					raise Exception(f"Warning: unknown el: \"{el}\"")
			else:
				el = el.replace("^", "**")
				s += el
		elif isinstance(el, list):
			s += f"({_parse_pair(el)})"
		else:
			raise Exception("what a hell")
		i += 1
	return s


def parse_tex(tex: str) -> str:
	l = str_utils.find_pair(tex, 0)[0]
	# print(l)
	s = _parse_pair(l)
	return s



if __name__ == '__main__':
	t = r"a \b{{c}}{\d{e} + f + \g[3]{h}{i} + j + {k} - l}"

	t = r"K_a \cdot (u + 1) \cdot \sqrt[3]{\frac{K_H \x T_1}{psi_ba \cdot u \cdot sigma_HP^2}}"

	s = parse_tex(t)
	print(s)

	# l, i = str_utils.find_pair2(t, 0)
	# print(l, i)
