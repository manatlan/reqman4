from src.reqman4 import common
import os
def test_config():
    assert common.load_reqman_conf("examples/classic/reqman.yml")

def test_guess():
    assert common.guess_reqman_conf( ["examples/classic/test_switchs.yml"] ) == os.path.abspath("examples/classic/reqman.yml")

def test_conf():
    ys=common.YScenario("""
root: 1
                        
--put2:
    root: 2
""")
    assert ys.conf["root"]==1
    ys.conf.apply("put2")
    assert ys.conf["root"]==2


def test_scenar_encoding():
    yml = 'root: "çébô" '
    ys=common.YScenario(yml)
    assert ys.conf["root"]=="çébô"      # the internal str stay in utf8

    e=lambda x: x.encode("utf8").decode("cp1252")
    d=lambda x: x.encode("cp1252").decode("utf8")
    yml = e('root: "çébô" ')
    ys=common.YScenario(yml)
    assert d(ys.conf["root"])=="çébô"   # the internal str stay in cp1252

    assert "çébô" in d(ys.save())   # the file stay in cp252 !


if __name__=="__main__":
    test_scenar_encoding()