def func ():
    def f ():
       print({"x":"test"})
    # exec("def private():\n\tprint({'x':'test'})\nglobal f\nf = private")
    print(locals())
    f()

func()