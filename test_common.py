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
    assert "put2" in ys.conf.switchs.keys()
    
    assert ys.conf["root"]==1
    ys.conf.apply("put2")
    assert ys.conf["root"]==2


def test_scenar_encoding():
    # utf8 file
    yml = 'root: "çébô" '
    ys=common.YScenario(yml)
    assert ys.conf["root"]=="çébô"      # the internal str stay in utf8
    assert b"\xc3\xa7\xc3\xa9b\xc3\xb4" in ys.save()

    # cp1252 file
    yml = 'root: "çébô" '.encode("utf8").decode("cp1252")
    ys=common.YScenario(yml)
    assert ys.conf["root"]=="çébô"   # the internal str stay in utf8
    assert b"\xe7\xe9b\xf4" in ys.save()

def test_YScenario_encoding():
    assert common.YScenario("a: 'éé'".encode("utf8").decode("cp1252")).encoding == "cp1252"
    assert common.YScenario("a: 1111".encode("utf8").decode("cp1252")).encoding == "utf8"   #no strange carac, can be utf8 !

def _valid_tests(string:str,ll:list):
    for obj in ll:
        b = common.BytesUtf8(obj)
        print(type(obj),b.encoding, [obj])
        d=common.YamlObject().load( b )
        assert d["val"]==string # UTF8
        assert isinstance(d["val"],str)

        t=lambda x: x.encode(b.encoding)
        assert t(d['val']) == t(string)


def test_eurostring():
    string = "cébô 50£ où 50$ oü 50€" # Europe occidentale

    ll=[
        f'val: {string}'.encode('cp1252'),
        f'val: {string}'.encode('utf8'),
        f'val: {string}',
        f'val: {string}'.encode('utf8').decode('cp1252'),
    ]

    _valid_tests(string,ll)

def test_utfstring():
    string = "cébô ⭐🔥$£€ тест テスト 測試 امتحان"

    ll=[
        f'val: {string}'.encode('utf8'),
        f'val: {string}',
    ]

    _valid_tests(string,ll)



if __name__=="__main__":
    test_scenar_encoding()