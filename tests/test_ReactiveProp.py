from gtag import ReactiveProp

def test_ReactiveProp():
    class Pojo: pass
    p=Pojo()
    p.a=12
    p.b=42

    a=ReactiveProp(p,"a")
    assert "<ReactiveProp" in repr(a)
    assert int(a)==12
    assert p.__dict__["a"]==12
    a.set(42)
    assert p.__dict__["a"]==42
    assert str(a)=="42"
    assert type(a+1) == ReactiveProp
    assert a+1 == 44

    b=ReactiveProp(p,"b")
    assert a>b
    assert a>0
    assert a>=b
    assert a>=0
    assert b<=a
    assert b<a
    assert b<100
    assert not a==b
    assert a!=b

    assert a+b == 86




def test_WARNING():
    class Pojo: pass
    p=Pojo()
    p.a=42

    a=ReactiveProp(p,"a")

    assert str(a) == "42"
    assert "-%s-" % a == "-42-"

    p.a=43

    def tt():
        assert str(a) == "43"
        assert "-%s-" % a == "-43-"