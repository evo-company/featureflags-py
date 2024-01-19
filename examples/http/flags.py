from featureflags_client.http.types import Variable, VariableType

REQUEST_QUERY = Variable("request.query", VariableType.STRING)


class Defaults:
    TEST = False
    SOME_USELESS_FLAG = False
