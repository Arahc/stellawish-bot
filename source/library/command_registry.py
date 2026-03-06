CHECKERS = []

def registerChecker(func):
    CHECKERS.append(func)
    return func

def isAnyCommand(text: str) -> bool:
    return any(checker(text) for checker in CHECKERS)