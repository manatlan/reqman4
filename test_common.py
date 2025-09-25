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

if __name__=="__main__":
    test_conf()