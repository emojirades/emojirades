def set_handler_args(self, *args, handler_params, **kwargs):
    for arg, pos in handler_params:
        if pos is not None:
            if len(args) > pos:
                setattr(self, arg, args[pos])
            else:
                raise TypeError(
                    f"{self} is missing a required positional argument"
                    + f"'{arg}' in position {pos}"
                )
        elif arg in kwargs:
            setattr(self, arg, kwargs[arg])
        else:
            raise TypeError(f"{self} is missing a required keyword argument '{arg}'")
