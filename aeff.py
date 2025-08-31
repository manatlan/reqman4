from src.env import jzon_dumps
def revert(d):
    return d

class RevertibleDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__initial={}

    def scope_update(self,d):
        self.__initial = self.copy()
        super().update(d)

    def scope_revert(self):
        self.clear()
        if self.__initial:
            self.update(self.__initial)


assert d["a"]==42
assert d["z"]==1
assert d["x"]==dict(z=1,l=list("AZ"))

# update dict
d.scope_update(dict(z=99,x=dict(z=2,l=list("ZA"))))
assert d["a"]==42
assert d["z"]==99
assert d["x"]==dict(z=2,l=list("ZA"))

print(jzon_dumps(d))

# revert all before update ^
d.scope_revert()
assert d["a"]==42
assert d["z"]==1
assert d["x"]==dict(z=1,l=list("AZ"))
