import nosepipe

@nosepipe.isolate
def erroring_test():
    raise Exception()

@nosepipe.isolate
def failing_test():
    assert False
