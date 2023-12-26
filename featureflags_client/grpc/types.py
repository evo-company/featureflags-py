from dataclasses import dataclass

from featureflags_protobuf.graph_pb2 import Variable as VariableProto


class Types:
    """Enumerates possible variable types, e.g. ``Types.STRING``

    .. py:attribute:: STRING

        String type

    .. py:attribute:: NUMBER

        Number type, represented as ``float`` in Python, ``double`` in ProtoBuf

    .. py:attribute:: TIMESTAMP

        Timestamp type, represented as ``datetime`` in Python,
        ``google.protobuf.Timestamp`` in ProtoBuf

    .. py:attribute:: SET

        Set of strings type

    """

    STRING = VariableProto.STRING
    NUMBER = VariableProto.NUMBER
    TIMESTAMP = VariableProto.TIMESTAMP
    SET = VariableProto.SET


@dataclass
class Variable:
    """Variable definition

    Example:

    .. code-block:: python

        USER_ID = Variable('user.id', Types.STRING)

    :param name: variable's name
    :param type: variable's type, one of :py:class:`Types`
    """

    name: int
    type: VariableProto.Type
