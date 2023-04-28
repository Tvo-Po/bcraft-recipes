from app.database import tools


class BitwiseAndCounter:
    def __init__(self, counter=0):
        self.counter = counter

    def __rand__(self, other):
        self.counter += other.counter + 1
        return self

    def __and__(self, other):
        return BitwiseAndCounter(self.counter + other.counter + 1)


class QueryMock:
    def __init__(self):
        self.total_object_chaining_count = 0
        self.filtered = False

    def filter(self, counter):
        self.total_object_chaining_count = counter.counter
        self.filtered = True
        return self


def test_filter_condition_chain_from_none():
    f = (
        tools.FilterConditionChain(None)
        & BitwiseAndCounter()
        & BitwiseAndCounter()
        & None
    )  # type: ignore
    result = f.resolve(QueryMock())
    assert result.filtered
    assert result.total_object_chaining_count == 1


def test_filter_condition_chain_nones():
    f = tools.FilterConditionChain(None) & None & None & None & None
    result = f.resolve(QueryMock())
    assert not result.filtered
    assert result.total_object_chaining_count == 0


def test_filter_condition_chain_without_none():
    f = (
        tools.FilterConditionChain(BitwiseAndCounter())
        & BitwiseAndCounter()
        & BitwiseAndCounter()
        & BitwiseAndCounter()
    )  # type: ignore
    result = f.resolve(QueryMock())
    assert result.filtered
    assert result.total_object_chaining_count == 3
