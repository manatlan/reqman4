from src.reqman4 import common
import os
def test_config():
    assert common.load_reqman_conf("examples/classic/reqman.conf")

def test_guess():
    assert common.guess_reqman_conf( ["examples/classic/test_switchs.yml"] ) == os.path.abspath("examples/classic/reqman.conf")

