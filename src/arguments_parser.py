import typing
import sys

ARGUMENTS_HELP_MESSAGE = "No one can help you."


def show_error_and_exit(msg: str) -> None:
    print(msg)
    print("use '--help'.")
    sys.exit(1)

def show_help_and_exit():
    print(ARGUMENTS_HELP_MESSAGE)
    sys.exit(0)


class handlers():
    @staticmethod
    def set(options_dict, key, value):
        options_dict[key] = value


class ArgumentsParser():
    def __init__(self) -> None:
        self.handlers: list[tuple[list[str], int, typing.Callable[[list[str], dict[str, typing.Any]], None]]] = []
        self.count_min_max = (-1, -1)

        self.add_handler(["-h", "--help"], 0, lambda args_local, options: show_help_and_exit())

    def add_handler(self, names: list[str], local_args_count: int, func: typing.Callable[[list[str], dict[str, typing.Any]], None]) -> 'ArgumentsParser':
        self.handlers.append(
            (names, local_args_count, func)
        )
        return self

    def add_option_boolean(self, names: list[str], option_name: str, value: bool = True) -> 'ArgumentsParser':
        self.add_handler(names, 0, lambda args_local, options: handlers.set(options, option_name, value))
        return self

    def add_option_set(self, names: list[str], option_name: str, value: typing.Any) -> 'ArgumentsParser':
        self.add_handler(names, 0, lambda args_local, options: handlers.set(options, option_name, value))
        return self

    def add_option_with_one_local_arg(self, names: list[str], option_name: str) -> 'ArgumentsParser':
        self.add_handler(names, 1, lambda args_local, options: handlers.set(options, option_name, args_local[0]))
        return self

    def set_min_max_count(self, min_: int = -1, max_: int = -1) -> 'ArgumentsParser':
        self.count_min_max = (min_, max_)
        return self

    def get_iterator(self, list_args: list[str]) -> 'typing.Iterator[str|None]':
        for arg in list_args:
            yield arg
        while True:
            yield None

    def parse(self, args: list[str]) -> tuple[list[str], dict[str, typing.Any]]:
        # converting arguments that come together, like:
        # "-abc" => "-a -b -c"
        list_args: list[str] = []
        for a in args:
            if a.startswith("-") and not a.startswith("--"):
                list_args.extend(["-" + s for s in a[1:]])
            else:
                list_args.append(a)

        # this will be returned in the end of parsing
        result_args_positional: list[str] = []
        result_options: dict[str, typing.Any] = {}

        # mapping handlers' names to their callables
        handlers_dict: dict[str, tuple[int, typing.Callable[[list[str], dict[str, typing.Any]], None]]] = {}
        for names, args_count, func in self.handlers:
            for name in names:
                handlers_dict[name] = (args_count, func)

        # parsing
        next_arg = self.get_iterator(list_args).__next__
        arg = next_arg()
        while not arg is None:
            # if arg is a key
            if arg.startswith("-"):
                if arg in handlers_dict:
                    local_args_count, func = handlers_dict[arg]
                    # creating a local arguments list for the key handler
                    local_args_list: list[str] = []
                    for a in [next_arg() for j in range(local_args_count)]:
                        if not a is None:
                            local_args_list.append(a)
                        else:
                            show_error_and_exit(f"Not enough arguments for '{arg}'")
                    # calling the key handler
                    func(local_args_list, result_options)
                else:
                    show_error_and_exit(f'Unknown argument: "{arg}"')
            else:
                result_args_positional.append(arg)

            arg = next_arg()

        # checking the count of positional arguments
        count_min, count_max = self.count_min_max
        if len(result_args_positional) < count_min:
            show_error_and_exit(f"Not enough positional arguments. Minimum count is {count_min}")
        if count_max >= 0 and len(result_args_positional) > count_max:
            show_error_and_exit(f"Too many positional arguments. Maximum count is {count_max}")

        return (result_args_positional, result_options)


if __name__ == "__main__":

    ARGUMENTS_HELP_MESSAGE = "No one can help you."

    args_positional, options = ArgumentsParser() \
        .set_min_max_count(1, 2) \
        .add_option_set(["-b", "--bibtex"], "bibtex", "Yes") \
        .add_option_boolean(["-a"], "a", True) \
        .add_option_boolean(["-c"], "c", True) \
        .add_option_with_one_local_arg(["-d"], "d") \
        .parse(sys.argv[1:])

    print(options, args_positional)
