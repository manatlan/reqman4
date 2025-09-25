from src.reqman4 import common
import os
def test_config():
    assert common.load_reqman_conf("examples/classic/reqman.yml")

def test_guess():
    assert common.guess_reqman_conf( ["examples/classic/test_switchs.yml"] ) == os.path.abspath("examples/classic/reqman.yml")

