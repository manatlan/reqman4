class AssertSyntaxError(Exception):
    pass

def assert_syntax( condition:bool, msg:str):
    if not condition: raise AssertSyntaxError( msg )