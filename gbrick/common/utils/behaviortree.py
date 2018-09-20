class Behavior:
    def invoke(self, trace) -> bool: raise NotImplementedError


class Composite(Behavior):

    def __init__(self):
        self.child = []

    def add_child(self, node):
        self.child.append(node)

    def invoke(self, trace) -> bool:
        pass


class Selector(Composite):

    def invoke(self, trace) -> bool:
        for b in self.child:
            if b.invoke(trace) is True:
                return True
        return False


class Sequencer(Composite):

    def invoke(self, trace) -> bool:
        for b in self.child:
            if b.invoke(trace) is False:
                return False
        return True


class Indexer(Behavior):
    def __init__(self, p_invoke, *args, **kw):
        self.child = {}
        self.func_invoke = p_invoke
        self.args = args
        self.kw = kw

    def add_child(self, key, node):
        self.child.__setitem__(key, node)

    def invoke(self, trace) -> bool:
        key = self.func_invoke(*self.args, **self.kw)
        node = self.child.get(key)
        return node.invoke(trace)


class Action(Behavior):

    def __init__(self, p_invoke, *args, **kw):
        self.func_invoke = p_invoke
        self.arg = args
        self.kw = kw

    def invoke(self, trace) -> bool:
        trace.append(self.func_invoke.__name__)
        return self.func_invoke(*self.arg, **self.kw)


def hihihi():
    print('hi')

if __name__ == '__main__':
    print(hihihi.__name__)