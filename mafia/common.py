WAIT_TIME_TO_START = 1


class Phase:
    DAY = False
    NIGHT = True


class Role:
    CIVILIAN = 0
    MAFIA = 1
    COMMISSAR = 2


class Winner:
    NONE = None
    CIVILIANS = False
    MAFIA = True


def get_role_name(role: int) -> str:
    if role == Role.CIVILIAN:
        return 'civilian'
    elif role == Role.MAFIA:
        return 'mafia'
    elif role == Role.COMMISSAR:
        return 'commissar'
    else:
        assert False, f'Found unknown role: {role}'
