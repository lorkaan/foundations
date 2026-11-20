from enum import StrEnum
from django.db.models.base import ModelBase

from .models import FormGroupModelDataBridge

from ..utils.type_utils import isString
from ..utils.dict_utils import isDict

from django.apps import apps
import logging
import inspect


class Protocol:

    logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        pass

    @classmethod
    def isValid(cls, obj):
        return False

class SourceType(StrEnum):
    ANSWER = "answer"
    LITERAL = "literal"
    PARENT = "parent"
    NODE = "node"
    GLOBAL = "global"
    CHILD = "child"

class SourceProtocol(Protocol):
    """
        This handles the Source Object protocol. This is how the Source of a data is defined to be handled.
    """    

    _type_enum_class = SourceType

    _value_key = "value"
    _question_code_key = "code"
    _bridge_key = "bridge"
    _src_type_key = "type"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        src_type = kwargs.get(self.__class__._src_type_key, None)
        if isString(src_type):
            try:
                self.src_type = self.__class__._type_enum_class(src_type)
            except Exception as e:
                self.__class__.logger.error(f"Source Protocol Error: {e}")
                self.src_type = None
        else:
            self.src_type = None
        self.bridge = kwargs.get(self.__class__._bridge_key, None)
        self.value = kwargs.get(self._value_key, None)
        self.question_code = kwargs.get(self._question_code_key, None)

    @classmethod
    def isValid(cls, obj):
        if not isinstance(obj, cls):
            return False

        if not isinstance(obj.src_type, cls._type_enum_class):
            return False

        if obj.src_type == SourceType.LITERAL:
            return obj.bridge is None and obj.question_code is None

        elif obj.src_type == SourceType.ANSWER:
            return isString(obj.question_code)

        elif obj.src_type == SourceType.PARENT:
            return isString(obj.bridge)

        elif obj.src_type == SourceType.NODE:
            return isString(obj.bridge)

        elif obj.src_type == SourceType.GLOBAL:
            return isString(obj.bridge)
        elif obj.src_type == SourceType.CHILD:
            return isString(obj.bridge)

        return False

    def get_reference(self):
        if self.__class__.isValid(self):
            if self.src_type == SourceType.LITERAL:
                return self.value
            elif self.src_type == SourceType.ANSWER:
                return self.question_code
            elif self.src_type == SourceType.PARENT:
                return self.bridge
            else:
                raise KeyError(f"Unknown SourceType: {self.src_type}")
        else:
            raise TypeError(f"Invalid Source Protocol: {self.__dict__}")


class ResolutionLookupProtocol(Protocol):

    _source_class = SourceProtocol

    _field_key = "field"
    _source_key = "source"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.field = kwargs.get(self.__class__._field_key, None)
        source_obj = kwargs.get(self.__class__._source_key, None)
        if isDict(source_obj):
            source = self.__class__._source_class(**source_obj)
            if self.__class__._source_class.isValid(source):
                self.source = source
            else:
                self.source = None
        else:
            self.source = None

    @classmethod
    def isValid(cls, obj):
        if not isinstance(obj, cls):
            return False

        if not isString(obj.field):
            return False

        if obj.source is not None:
            return cls._source_class.isValid(obj.source)

        return True

class ResolutionAction(StrEnum):
    SEARCH = "search"

class ResolutionProtocol(Protocol):

    _action_type_enum_class = ResolutionAction
    _lookup_class = ResolutionLookupProtocol

    _lookup_fields_key = "lookup"
    _resolution_action_type_key = "action"

    @classmethod
    def isValidLookupFields(cls, fieldDict):
        return isDict(fieldDict)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        resolution_action = kwargs.get(self.__class__._resolution_action_type_key, None)
        if isString(resolution_action):
            try:
                self.action = self.__class__._action_type_enum_class(resolution_action)
            except Exception as e:
                self.__class__.logger.error(e)
                self.action = None
        else:
            self.action = None
        lookup_fields = kwargs.get(self.__class__._lookup_fields_key, {})
        if self.__class__.isValidLookupFields(lookup_fields):
            cur_lookup = self.__class__._lookup_class(**lookup_fields)
            if self.__class__._lookup_class.isValid(cur_lookup):
                self.lookup = cur_lookup
            else:
                self.lookup = None
        else:
            self.lookup = None

    @classmethod
    def isValid(cls, obj):
        if not isinstance(obj, cls):
            return False

        if not isinstance(obj.action, cls._action_type_enum_class):
            return False

        if obj.action == ResolutionAction.SEARCH:
            return (
                isinstance(obj.lookup, cls._lookup_class)
                and cls._lookup_class.isValid(obj.lookup)
            )

        return False

class FieldConfigProtocolKeyRepresentation:

    def __init__(self, rep_cls, required=True):
        self.rep_cls = rep_cls
        self.required = required if type(required) == bool else False

class FieldConfigProtocol(Protocol):

    _source_class = SourceProtocol
    _resolution_class = ResolutionProtocol

    _source_key = "source"
    _resolution_key = "resolution"

    _keys = {
        _source_key: FieldConfigProtocolKeyRepresentation(_source_class),
        _resolution_key: FieldConfigProtocolKeyRepresentation(_resolution_class, required=False)
    }

    def getSource(self):
        return getattr(self, self.__class__._source_key, None)

    def getResolution(self):
        return getattr(self, self.__class__._resolution_key, None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for k, v in self.__class__._keys.items():
            if not isinstance(v, FieldConfigProtocolKeyRepresentation):
                raise TypeError(f"Can not get Config for: {type(v)} --> {v}")
            else:
                cur = kwargs.get(k, None)
                if isDict(cur):
                    obj = v.rep_cls(**cur)
                    if v.rep_cls.isValid(obj):
                        setattr(self, k, obj)
                    else:
                        if v.required:
                            raise TypeError(f"Got an Invalid Config: {obj}")
                        else:
                            setattr(self, k, None)
                else:
                    if v.required:
                        raise TypeError(f"Expected a Non-empty dictionary: {cur}")
                    else:
                        setattr(self, k, None)

    @classmethod
    def isValid(cls, obj):
        if not isinstance(obj, cls):
            return False

        for key, definition in cls._keys.items():

            if not isinstance(definition, FieldConfigProtocolKeyRepresentation):
                raise TypeError(
                    f"During Validation: Can not get Config for: "
                    f"{type(definition)} --> {definition}"
                )

            value = getattr(obj, key, None)

            if value is None:
                if definition.required:
                    return False
                continue

            if not isinstance(value, definition.rep_cls):
                return False

            if not definition.rep_cls.isValid(value):
                return False

        return True

# Edit below to Add the full Configuration Protocol

class FieldMappingProtocol(Protocol):

    _mapping_representation_cls = FieldConfigProtocol

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mapping = {}
        self.errors = {}
        for k, v in kwargs.items():
            try:
                if not isString(k):
                    raise TypeError("Mapping key must be a string.")

                if not isDict(v):
                    raise TypeError("Mapping configuration must be a dictionary.")

                cur = self.__class__._mapping_representation_cls(**v)

                if self.__class__._mapping_representation_cls.isValid(cur):
                    self.mapping[k] = cur
                else:
                    self.errors[k] = "Invalid field configuration."

            except Exception as e:
                self.errors[k] = str(e)

    @classmethod
    def isValid(cls, obj):
        if isinstance(obj, cls):
            if isDict(obj.errors) or not isDict(obj.mapping):
                return False
            for v in obj.mapping.values():
                if cls._mapping_representation_cls.isValid(v):
                    continue
                else:
                    return False
            return True
        else:
            return False



class InputConfigProtocol(FieldMappingProtocol):
    """
        This defines the protocol or structure of the JSON representing the description of a Nodes Input Data.
    """

    _input_definition_key = "fields"

    def __init__(self, **kwargs):
        fields = kwargs.pop(self.__class__._input_definition_key, None)
        if not isDict(fields):
            raise TypeError(f"Expected a Dictionary, instead got: {type(fields)}")
        super().__init__(**fields)


class OperationsConfigProtocol(Protocol):

    def __init__(self, **kwargs):
        pass


class OutputConfigProtocol(Protocol):

    def __init__(self, **kwargs):
        pass


class NodeConfigProtocol(Protocol):

    _input_key = "input"
    _input_config_cls = InputConfigProtocol
    _operations_key = "operations"
    _operations_config_cls = OperationsConfigProtocol
    _output_key = "output"
    _output_config_cls = OutputConfigProtocol

    def __init__(self, **kwargs):
        input_defintion = kwargs.pop(self.__class__._input_key, {})
        if isDict(input_defintion):
            self.input = self.__class__._input_config_cls(**input_defintion)
        else:
            raise ValueError(f"Every Node requires Input Definition. Got: {type(input_defintion)} --> {input_defintion}")
        output_defintion = kwargs.pop(self.__class__._output_key, {})
        if isDict(output_defintion):
            self.output = self.__class__._output_config_cls(**output_defintion)
        else:
            raise ValueError(f"Every Node requires Input Definition. Got: {type(output_defintion)} --> {output_defintion}")
        operation_defintion = kwargs.pop(self.__class__._operations_key, {})
        if isDict(operation_defintion):
            self.operations = self.__class__._operations_config_cls(**operation_defintion)
        else:
            self.operations = None
        super().__init__(**kwargs)

    def getInput(self):
        if isinstance(self.input, self.__class__._input_config_cls):
            return self.input
        else:
            raise TypeError(f"Input was expected to be of type InputConfigProtocol, instead got: {type(self.input)}")

    def getInputFields(self):
        if isinstance(self.input, self.__class__._input_config_cls):
            return self.input.mapping
        else:
            raise TypeError(f"Input was expected to be of type InputConfigProtocol, instead got: {type(self.input)}")

    def getOperations(self):
        return self.operations

    def getOutput(self):
        return self.output
            

class InputNodeConfigProtocol(NodeConfigProtocol):
    """
        Protocol for defining the Input Node Configuration
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class OutputNodeAction(StrEnum):
    CREATE = "create"
    SEARCH = "search"   # This lets a node that has a model be an input to another node via a dependency

class OutputNodeConfigProtocol(NodeConfigProtocol):
    """
        Protocol for defining the Output Node Configuration

        Output Node is a slightly misleading name as the only definition for this kind of Node is to be linked to
        a specific Model in the Database that isn't a FormGroup. E.g. Models that are supposed to have instances created
        via processing this Node. The Search Action exists for the rare instance when a Node Lookup might be necessary, and
        dependencies are used since lookups are generally considered 'heavy' actions, vs a normal Input and Operation action which
        should just be normal processing (but could also be 'heavy' actions but dont involve SQL queries themselves)
    """

    _action_config_key = "action"

    def __init__(self, **kwargs):
        action_str = kwargs.pop(self.__class__._action_config_key, None)
        if isString(action_str):
            try:
                self.action = OutputNodeAction(action_str)
            except Exception as e:
                raise ValueError(f"Could not determine Action: {str(e)}")
        else:
            raise ValueError(f"Action was not given in the configuration. {type(action_str)} --> {action_str}")
        super().__init__(**kwargs)

class HiddenNodeConfigProtocol(NodeConfigProtocol):
    """
        Protocol for defining the Hidden or Operation Node Configuration
    """

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

class InputOutputConfigProtocol(OutputNodeConfigProtocol, InputNodeConfigProtocol):

    def __init__(self, **kwargs):
    
        super().__init__(**kwargs)


class ExecutionConfigProtocol(Protocol):
    pass