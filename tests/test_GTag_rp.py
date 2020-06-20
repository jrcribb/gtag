if __name__=="__main__":
    import sys,os
    sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))

from gtag import GTag,Tag,value
from gtag import gtag
import pytest

def test_change_rp_values():
    class A(GTag):
        def init(self):
            self.v=1

    a=A()
    assert isinstance(a.v,gtag.ReactiveProp)
    assert a.v==1

    class B(GTag):
        def init(self,v):
            self.v=v

    b=B(a.v)
    assert isinstance(b.v,gtag.ReactiveProp)
    assert b.v==1

    a.v=2
    assert isinstance(a.v,gtag.ReactiveProp)
    assert isinstance(b.v,gtag.ReactiveProp)
    assert a.v==2
    assert b.v==2

    b.v=3
    assert isinstance(a.v,gtag.ReactiveProp)
    assert isinstance(b.v,gtag.ReactiveProp)
    assert a.v==3
    assert b.v==3

    a.v+=1
    assert isinstance(a.v,gtag.ReactiveProp)
    assert isinstance(b.v,gtag.ReactiveProp)
    assert a.v==4
    assert b.v==4

    a.v-=1
    assert isinstance(a.v,gtag.ReactiveProp)
    assert isinstance(b.v,gtag.ReactiveProp)
    assert a.v==3
    assert b.v==3

    a.v*=2
    assert isinstance(a.v,gtag.ReactiveProp)
    assert isinstance(b.v,gtag.ReactiveProp)
    assert a.v==6
    assert b.v==6

    a.v/=2
    assert isinstance(a.v,gtag.ReactiveProp)
    assert isinstance(b.v,gtag.ReactiveProp)
    assert a.v==3
    assert b.v==3


def test_concant_rp_values():
    class A(GTag):
        def init(self):
            self.v="1"

    a=A()
    assert isinstance(a.v,gtag.ReactiveProp)
    assert a.v=="1"

    class B(GTag):
        def init(self,v):
            self.v=v

    b=B(a.v)
    assert isinstance(b.v,gtag.ReactiveProp)
    assert b.v=="1"

    a.v+="x"
    assert isinstance(a.v,gtag.ReactiveProp)
    assert isinstance(b.v,gtag.ReactiveProp)
    assert a.v=="1x"
    assert b.v=="1x"
if __name__=="__main__":
    test_GTag()