class CheckSyntaxError(Exception):
    pass

def assert_syntax( condition:bool, msg:str):
    if not condition: raise CheckSyntaxError( msg )