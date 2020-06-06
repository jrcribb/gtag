from gtag import GTag,Tag
import pytest

# @pytest.mark.skip(reason="could coz trouble with vscode <> chrome")
def test_GTagApp_run():
    class My(GTag):
        size=(100,100)
        def build(self):
            self.script=self.bind.evtExit(42) # produce js (bindUpdate)
            return Tag.div("hello")
        def evtExit(self,p):
            self.exit(p)


    m=My()
    assert isinstance(m._tag,Tag)
    assert ">hello<" in str(m)
    assert m.run()==42


# @pytest.mark.skip(reason="could coz trouble with vscode <> chrome")
def test_GTagApp_run_with_start():
    class My(GTag):
        size=(100,100)
        def build(self):
            return Tag.div("hello")
        async def evtExit(self):
            self.exit(43)

    m=My()
    assert m.run(start=m.evtExit())==43

#@pytest.mark.skip(reason="TODO")
def test_GTagApp_run_with_start_param():
    class My(GTag):
        size=(100,100)
        def build(self):
            return Tag.div("hello")
        async def evtExit(self,p,txt,b):
            self.exit("%s%s%s"%(p,txt,b))


    m=My()
    assert m.run(start=m.evtExit(43,"jj",False))=="43jjFalse"

@pytest.mark.skip(reason="TODO")
def test_GTagApp_run_with_start_ag():
    class My(GTag):
        size=(100,100)
        def build(self):
            return Tag.div("hello")
        async def evtExit(self):
            print("yo")
            yield
            self.exit(44)

    m=My()
    assert m.run(start=m.evtExit())==44


# @pytest.mark.skip(reason="could coz trouble with vscode <> chrome")
def test_GTagApp_serve():
    class My(GTag):
        size=(100,100)
        def build(self):
            self.script=self.bind.evtExit(42) # produce js (bindUpdate)
            return Tag.div("hello")
        def evtExit(self,p):
            self.exit(p)

    m=My()
    assert isinstance(m._tag,Tag)
    assert ">hello<" in str(m)
    assert m.serve()==42


