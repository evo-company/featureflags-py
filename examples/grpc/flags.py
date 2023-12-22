from featureflags.grpc.types import Types, Variable

REQUEST_QUERY = Variable("request.query", Types.STRING)


class Defaults:
    TEST = False
    SOME_USELESS_FLAG = False
