from gtag import GTag,bind,State
from gtag.gui import A,Box,Button,Div,HBox,Input,Li,Nav,Section,Tabs,Text,Ul,VBox

"""
the most advanced gtag example, in the world ;-)
(mainly used for manual tests)
"""

class Inc(GTag):
    def init(self,v=0):
        self.cpt=v

    def build(self):    # called at __init__()
        return HBox(
                Button("-",onclick=self.bind.addV(-1) ),         #<- bind GuyCompo event
                Text(self.bind.cpt,style="text-align:center"),
                Button("+",onclick=self.bind.addV(1) ),          #<- bind GuyCompo event
            )

    def addV(self,v):
        self.cpt+=v


class MBox(GTag):
    def init(self,content):
        self.content=content

    @bind
    def build(self):
        if self.content!=None:
            o = Div(klass="modal is-active")
            o.add( Div(klass="modal-background",onclick=self.bind.close()) )
            o.add( Div( Box(self.content),klass="modal-content") )
            o.add( Div(klass="modal-close is-large",aria_label="close",onclick=self.bind.close()) )
            return o

    def close(self):
        self.content=None


class MyTabs(GTag):
    def init(self,selected:int):
        self.selected=selected
        self.tabs=[]

    def addTab(self,title):
        self.tabs.append(title)

    @bind
    def renderUL(self):
        u=Ul()
        for idx,title in enumerate(self.tabs):
            isActive="is-active" if self.selected==idx+1 else None
            u.add( Li(A(title,onclick=self.bind.select(idx+1)), klass=isActive ) )
        return u

    def build(self): # dynamic rendering !
        return Tabs( self.renderUL() )

    def select(self,idx):
        self.selected=idx


class MyInput(GTag):

    def init(self,txt):
        self.v=txt

    def build(self):
        return Input(type="text",value=self.v,onchange=self.bind.onchange("this.value"))

    def onchange(self,txt):
        self.v = txt

class Page1(GTag):

    def init(self,nb,txt):
        self.nb=nb
        self.txt=txt

    @bind
    def compute(self):
        b=Div()
        for i in range( int(self.nb) ):
            b.add( "⭐" )
        return b

    def build(self):
        return VBox(
            MyInput(self.bind.txt ),
            Text(self.bind.txt),
            Inc(self.bind.nb),
            Inc(self.bind.nb),
            Box(self.bind.nb, self.compute()),
            Button("Show mbox",onclick=self.bind.setMBoxMsg("'hello'")) #TODO: find better !!!
        )

    def setMBoxMsg(self,txt):
        self.state.setMBox( Inc(42) )

class Page2(GTag):

    def init(self,b):
        self.nb=b

    def build(self):
        return Div(
            Box("A test page, with a binding value:", self.bind.nb),
            Inc(self,self.bind.nb),
            Button("show",onclick=self.bind.kik())
        )
    def kik(self):
        self.state.setMBox("yo")

class Page3(GTag):

    def init(self,sel):
        self.selected=sel

    def build(self):    # called at __init__()
        t=MyTabs(self.bind.selected)
        t.addTab("tab1")
        t.addTab("tab2")
        t.addTab("tab3")
        return Div(t,Box(self.renderContent()))

    @bind
    def renderContent(self):
        return "Content %s" % self.selected


class TestApp(GTag):
    size=(500,400)

    def init(self):
        self.nb=12
        self.txt="yolo"

    @bind
    def build(self): # DYNAMIC RENDERING HERE !
        divBrand=Div( klass="navbar-brand" )
        divBrand.add( A("<b>GTag Test App</b>",klass="navbar-item") )
        divBrand.add( A('<span aria-hidden="true"></span><span aria-hidden="true"></span><span aria-hidden="true"></span>',
                        role="button",
                        klass="navbar-burger burger",
                        aria_label="menu",
                        aria_expanded="false",
                        data_target="navbarBasicExample",
                        onclick="this.classList.toggle('is-active');document.querySelector('.navbar-menu').classList.toggle('is-active')") )

        menu=Div(klass="navbar-start")
        menu.add( A("Page1", klass="navbar-item", onclick=self.bind.setPage(1)))
        menu.add( A("Page2 (%s)"% int(self.state.nb), klass="navbar-item", onclick=self.bind.setPage(2)))
        menu.add( A("Page3", klass="navbar-item", onclick=self.bind.setPage(3)))
        menu.add( A("Exit", klass="navbar-item", onclick=self.bind.doExit() ) )

        divMenu=Div( menu, klass="navbar-menu" )


        if self.state.page==1:
            page=Page1(self.bind.nb,self.bind.txt)
        elif self.state.page==2:
            page=Page2(self.state.nb)
        elif self.state.page==3:
            page=Page3(self.state.selectedTab)



        return Div(
            Nav( divBrand, divMenu, role="navigation",aria_label="main navigation"),
            Section( Div( "<br>", page, klass="container") ),
            MBox( self.state.msg )
        )

    def doExit(self):
        self.exit(-1)

    def setPage(self,n):
        self.state.page.set(n)

class MyState(State): # a global STATE to share things between components
    def setMBox(self,txt):
        self.msg.set(txt)

if __name__=="__main__":
    app=TestApp( MyState(nb=12,msg=None,page=1,selectedTab=1) )
    print( app.run(log=False) )
    # print( app.serve(log=False) )