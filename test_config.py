import src.config as config
import os
def test_config():
    assert config.load_reqman_conf("examples/reqman.conf")

def test_guess():
    assert config.guess_reqman_conf( ["examples/test_switchs.yml"] ) == os.path.abspath("examples/reqman.conf")

