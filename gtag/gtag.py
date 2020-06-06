#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# #############################################################################
#    Apache2 2020 - manatlan manatlan[at]gmail(dot)com
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
#    more: https://github.com/manatlan/guy
# #############################################################################

import guy,sys,asyncio,hashlib,html,inspect,types
import typing as T


isAsyncGenerator=lambda x: "async_generator" in str(type(x)) #TODO: howto better ?

value=lambda x: x.get() if isinstance(x,ReactiveProp) else x

def log(*a):
    #~ print(*a)
    pass


class MyMetaclass(type):
    def __getattr__(self,name:str) -> any:
        def _(*a,**k) -> Tag:
            t=Tag(*a,**k)
            t.tag=name
            return t
        return _

class Tag(metaclass=MyMetaclass):
    __metaclass__ = MyMetaclass
    """ This is a helper to produce a "HTML TAG" """
    tag="div" # default one
    klass=None

    def __init__(self,*contents,**attrs):
        #~ assert "id" not in attrs.keys()
        self.id=None
        self.__contents=list(contents)
        self.__dict__.update(attrs)

    def add(self,*elt):
        self.__contents.extend(elt)

    def __str__(self):
        attrs={k:v for k,v in self.__dict__.items() if not k.startswith("_")} # clone the dict (important)!
        klass= attrs.get("klass") or self.klass
        if "klass" in attrs: del attrs["klass"]
        if klass: attrs["class"]=klass
        if self.id: attrs["id"]=self.id
        rattrs=[]
        for k,v in attrs.items():
            if v is not None and k not in ["tag"]:
                if isinstance(v,bool):
                    if v: rattrs.append(k)
                else:
                    rattrs.append( '%s="%s"'%(k.replace("_","-") if k!="klass" else "class",html.escape( str(v) )) )

        return """<%(tag)s%(attrs)s>%(content)s</%(tag)s>""" % dict(
            tag=self.tag,
            attrs=" ".join([""]+rattrs) if rattrs else "",
            content=" ".join([str(i) for i in self.__contents if i is not None]),
        )
    def __repr__(self):
        return "<%s>" % self.__class__.__name__


class CSS(Tag):
    def __init__(self,content):
        self._md5=hashlib.md5("css:".encode()+content.encode()).hexdigest()
        if content.startswith("http"):
            self.tag="link"
            super().__init__(type="text/css",rel="stylesheet",href=content)
        else:
            self.tag="style"
            super().__init__(content,type="text/css")

class JS(Tag):
    tag="script"
    def __init__(self,content):
        self._md5=hashlib.md5("js:".encode()+content.encode()).hexdigest()
        if content.startswith("http"):
            super().__init__(type="text/javascript",src=content)
        else:
            super().__init__(content,type="text/javascript")

class ReactiveProp:
    def __init__(self,dico:dict,attribut:str):
        self.__instance=dico
        self.__attribut=attribut
    def set(self,v):
        self.__instance[self.__attribut]=v
    def get(self):
        return self.__instance[self.__attribut]


    def __eq__(self, v):
        return self.get() == value(v)

    def __ne__(self, v):
        return self.get() != value(v)

    def __lt__(self, v):
        return self.get() < value(v)

    def __le__(self, v):
        return self.get() <= value(v)

    def __ge__(self, v):
        return self.get() >= value(v)

    def __gt__(self, v):
        return self.get() > value(v)


    def __iadd__(self,v):
        vv=self.get() + value(v)
        self.set( vv )
        return self

    def __int__(self):
        return int(self.get())
    def __bool__(self):
        return bool(self.get())
    def __str__(self):
        return str(self.get())

    def __repr__(self):
        iid=self.__instance.id if hasattr(self.__instance,"id") else str(self.__instance)
        return "<%s instance=%s attr=%s>" % (self.__class__.__name__,iid,self.__attribut)
    #TODO: add a lot of __slot__ ;-)



def local( method ): # gtag.event decorator
    """ Decorator to make a gtag.method() able to start after init !
    """
    Capacity(method).set(Capacity.LOCAL)
    return method

class Capacity:
    LOCAL="local"
    def __init__(self,method:callable):
        self.__method=method
    def has( self, capacity ):
        if hasattr(self.__method,"capacities"):
            return capacity in self.__method.capacities
    def set( self, capacity ):
        if not hasattr(self.__method,"capacities"):
            self.__method.capacities=[]
        self.__method.capacities.append(capacity)
    @property
    def hasLocal( self ):
        return self.has(Capacity.LOCAL)



class GtagProxy:
    """ Expose props(as ReactiveProps)/method from a gtag """
    def __init__(self,instance):
        self.__instance=instance
    def __getattr__(self,name:str):
        if name in ["id","main","parent"]:
            return getattr(self.__instance,name)
        elif name in self.__instance.__dict__.keys(): # bind a data attribut  -> return a ReactiveProp
            o=self.__instance.__dict__[name]
            if isinstance(o,ReactiveProp):
                return o
            else:
                return ReactiveProp(self.__instance.__dict__,name)
        elif name in dir(self.__instance):   # bind a self.method    -> return a js/string for a guy's call in js side
            def _(*a,**k):
                method=getattr(self.__instance,name)
                return method(*a,**k)
            return _
        else:
            raise Exception("Unknown method/attribut '%s' in '%s'"%(name,repr(self.__instance)))
    def __repr__(self):
        return repr(self.__instance)


class GTag:
    """
    The magic thing ;-)
    """
    size=None
    _call=None # first event to call at start !
    """ size of the windowed runned gtag (tuple (width,height) or guy.FULLSCREEN or None) """

    # implicit parent version (don't need to pass self(=parent) when creating a gtag)
    def __init__(self,*a,**k):
        self._tag=None
        self.script=None

        if "parent" in k.keys(): # clonage (only main tags, so parent is None)
            #(but could be used to reparent a gtag manually)
            parent=k["parent"]
            del k["parent"]
        else:
            # guess parent
            frame = sys._getframe(1)
            arguments = frame.f_code.co_argcount
            if arguments == 0:
                parent=None
            else:
                caller_calls_self = frame.f_code.co_varnames[0]
                parent=frame.f_locals[caller_calls_self]
                assert isinstance(parent,GTag)
                if parent is self: parent=None  #for TU only

        self._id="%s_%s" % (self.__class__.__name__,hex(id(self))[2:])
        self._childs=[]     #<- this is cleared at each rendering
        self._args=a
        self._kargs=k
        self._parent=parent

        log("INIT",repr(self))
        self.init(*self._args,**self._kargs)

        self._tag = self.build()

        # Store the instance in the parent._childs
        if self._parent:
            self._parent._childs.append(self)

    def _tree(self):
        def _gc(g,lvl=0) -> list:
            ll=["+" + ("   "*lvl) + repr(g)]
            for obj in g.innerChilds:
                inners=_gc(obj,lvl+1)
                ll.extend( [i+' (INNER)' for i in inners] )
            for obj in g._childs:
                ll.extend( _gc(obj,lvl+1) )
            return ll
        return "\n".join(_gc(self,0))


    @property
    def innerChilds(self):
        return [v for k,v in self.__dict__.items() if k not in ["_tag","_parent"] and isinstance(v,GTag)]

    def _getChilds(self) -> dict:

        def _gc(g) -> dict:
            d={g.id:g}
            for obj in g.innerChilds:
                d.update( _gc(obj) )
            for obj in g._childs:
                d.update( _gc(obj) )
            return d

        return _gc(self)

    def _getRef(self,id): # -> GTag
        childs=self._getChilds()
        return childs[id]

    def _getMain(self):
        x=self
        while x._parent is not None:
            x=x._parent
        return x

    @property
    def id(self):
        return self._id


    @property
    def parent(self)-> any: #GTag
        """ return caller/binder to parent instance (None if gtag is the main) """
        if self._parent is None:
            return None
        else:
            return GtagProxy( self._parent )


    @property
    def main(self)-> any: #GTag
        """ return caller/binder to main instance """
        return GtagProxy( self._getMain() )



    @property
    def bind(self) -> any:
        """ to bind attribute or method !"""
        class Binder:
            def __getattr__(this,name:str):
                if name in self.__dict__.keys(): # bind a data attribut  -> return a ReactiveProp
                    o=self.__dict__[name]
                    if isinstance(o,ReactiveProp):
                        return o
                    else:
                        return ReactiveProp(self.__dict__,name)
                elif name in dir(self):   # bind a self.method    -> return a js/string for a guy's call in js side
                    def _(*args):
                        if args:
                            return "self.bindUpdate('%s',GID,'%s',%s)" % (self.id,name,",".join([str(i) for i in args]) ) #TODO: escaping here ! (and the render/str ?) json here !
                        else:
                            return "self.bindUpdate('%s',GID,'%s')" % (self.id,name)
                    return _
                else:
                    raise Exception("Unknown method/attribut '%s' in '%s'"%(name,self.__class__.__name__))
        return Binder()


    def _clone(self):
        assert self._parent==None,"Can't clone a gtag which is not the main"
        props={k:v for k,v in self.__dict__.items() if k[0]!="_" or k=="_call"}
        gtag = self.__class__(*self._args,**self._kargs,parent=None)
        gtag.__dict__.update(props)
        assert isinstance(gtag,GTag)
        log("^^^ CLONED ^^^",repr(self),"-->",repr(gtag))
        return gtag


    def _guessHeaders(self):
        """ try to found the headers, based of declarations of each gtag, and return the html elements to include in header
        """
        assert self._parent is None,"You are not on the main instance, you can't get a child"

        mklist=lambda x: x if isinstance(x,list) else [x]

        ll=[]
        for g in GTag.__subclasses__():
            if hasattr(g,"css"):
                for i in mklist(getattr(g,"css")):
                    if i:
                        c=CSS(i)
                        if c._md5 not in [l._md5 for l in ll]:
                            ll.append( c )
            if hasattr(g,"js"):
                for i in mklist(getattr(g,"js")):
                    if i:
                        c=JS(i)
                        if c._md5 not in [l._md5 for l in ll]:
                            ll.append( c )
        return ll


    def init(self,*a,**k):
        """ Override to make inits (replace the __init__(), but same role)"""
        pass

    def build(self) -> T.Union[Tag,None]:
        """ Override for static build
            SHOULD RETURN a "Tag" (not a GTag)
        """
        pass

    def _rebuild(self):
        self._childs=[]
        self._tag=self.build()

    def __str__(self):
        log("___rendering",repr(self))
        o= self._tag
        if o is None:
            return ""
        else:
            if isinstance(o,Tag):
                o.id=self.id
            elif isinstance(o,GTag):
                assert isinstance(o._tag,Tag)
                o=o._tag        #TODO: recursivity here ?!... wtf if gtag return a gtag
                o.id=self.id
            else:
                raise Exception("%s --build--> ???%s???" % (repr(self),type(o)))
            return str(o)

    def __repr__(self):
        return "<GTag: %s [parent:%s] (innerchilds=%s)>" % (
            self.id,
            self._parent.id if self._parent else "None",
            [i.id for i in self.innerChilds]
        )

    def __setattr__(self,k,v):
        o=self.__dict__.get(k)
        if isinstance(o,ReactiveProp):
            o.set( value(v) )
        else:
            super().__setattr__(k,v)

    def _getScripts(self) -> str:
        ll=[]
        for g in self._getChilds().values():
            js=g.script
            if js:
                ll.append( "(function(tag){%s})(document.getElementById('%s'))" % (str(js),g.id) )
        return ";".join(ll)


    def _update(self) -> dict:
        h=str(self)
        s=self._getScripts()
        log(">>>UPDATE:",repr(self))
        log(self._tree())
        return dict(script="""document.querySelector("#%s").innerHTML=`%s`;%s""" % (
            self.id, h,s
        ))

    def run(self,*a,start=None,**k) -> any:
        """ Run as Guy App (using Chrome) """
        self._call=start
        return GTagApp(self,False).run(*a,**k)

    def runCef(self,*a,start=None,**k) -> any:
        """ Run as Guy App (using Cef) """
        self._call=start
        return GTagApp(self,False).runCef(*a,**k)

    def serve(self,*a,start=None,**k) -> any:
        """ Run as Guy Server App """
        self._call=start
        return GTagApp(self,True).serve(*a,**k)



class GTagApp(guy.Guy):
    """ The main guy instance app, which cn run a gtag inside """

    def __init__(self,gtag,isMultipleSessionPossible=False):
        assert isinstance(gtag,GTag)
        self._originalGTag=gtag

        self.size=gtag.size

        if isMultipleSessionPossible:
            self._ses={}
        else:
            self._ses=None
        super().__init__()

    def render(self,path=None):
        hh=self._originalGTag._guessHeaders()

        return """<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script>
            if(!sessionStorage["gtag"]) sessionStorage["gtag"]=Math.random().toString(36).substring(2);
            var GID=sessionStorage["gtag"];

            async function forceUpdateManually(x) {console.log(x),eval(x)}

            async function getSessionId() {return GID}
            async function _render(html,script) {
                document.body.innerHTML=html;
                if(script) eval(script)
                console.log(script)
            }
        </script>
        %s
    </head>
    <body>
            <script src="guy.js"></script>
    </body>
</html>""" % "\n".join([str(h) for h in hh])

    async def init(self):
        if self._ses is not None: # web mode
            gid=await self.js.getSessionId()
            log("CREATE SESSION:",gid)
            gtag = self._ses.get(gid)
            if gtag is None:
                gtag = self._originalGTag._clone()
                self._ses[gid] = gtag
        else: # app mode
            gtag = self._originalGTag

        gtag.exit = self.exit

        log(">>>SERVE",repr(gtag))
        log(gtag._tree())

        #=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- call statement (old autostart system)
        caller=""
        if gtag._call:  # there is an event to call at start !
            if isAsyncGenerator(gtag._call) or asyncio.iscoroutine(gtag._call):
                caller=getattr(gtag.bind,gtag._call.__name__)()
        #=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

        await self.js._render( str(gtag), gtag._getScripts()+";"+caller )

    async def forceUpdate(self,g): #can't be called from client side !
        g._rebuild()
        js=g._update()["script"]    #TODO: not cute ... should unify way to render to client (currently: 3 ways)
        log(">>>Force UPDATE:",repr(g))
        await self.js.forceUpdateManually(js)

    async def bindUpdate(self,id:str,gid:str,method:str,*args):
        """ inner (js exposed) guy method, called by gtag.bind.<method>(*args) """
        if self._ses is None:
            gtag=self._originalGTag
        else:
            gtag=self._ses[gid]

        #////////////////////////////////////////////////////////////////// THE MAGIC TODO: move to gtag
        obj=gtag._getRef(id)

        log("BINDUPDATE on",repr(gtag),"----->",repr(obj),"%s(%s)"% (method,args))
        proc=getattr(obj,method)
        toRender=gtag if not Capacity(proc).hasLocal else obj

        if asyncio.iscoroutinefunction( proc ):
            rep=await proc(*args)
        else:
            rep=proc(*args)

        if rep:
            if isAsyncGenerator(rep):
                async for _ in rep: # could use yielded thing to update all or local ?!
                    await self.forceUpdate(toRender)
            else:
                raise Exception("wtf?")

        toRender._rebuild()
        return toRender._update() #UPDATE ALL (historic way)
        #////////////////////////////////////////////////////////////////// THE MAGIC
