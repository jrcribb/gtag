from gtag import GTag,ReactiveProp,bind
from gtag.tags import A,Body,Box,Button,Div,HBox,Input,Li,Nav,Section,Tabs,Text,Ul,VBox
from gtag.tags import Tag
import types

class Star(Tag): # a Star tag for the tests bellow
    tag="Star"
    def __init__(self,v):
        super().__init__("*(%s)"%v)
        self.id="%s" % hex(id(self))[2:]

class StaticComputed(GTag): # GOOD PRATICE !!
    """ A gtag component with a property bind'ed and a method binded (computed) """
    def __init__(self,n):
        self.n=n
        super().__init__()

    @bind # -> ReactiveMethod
    def stars(self):
        return Text( *[Star(i) for i in range(int(self.n))] )

    @bind
    def nnn(self,c):
        return c * self.n

    def build(self):
        return Text(self.nnn("X"), self.stars() )

t=StaticComputed(2)
print(t)
# t.run()