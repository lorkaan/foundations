import uuid

from foundation.ecosystem_foundations.dynamicforms.models import FormProcessingConfig
from .registry import TRANSFORMATION_REGISTRY

from ..utils.type_utils import isString

from ..utils.dict_utils import isDict
from ..utils.engine.boolAstHandler import BooleanAstHandler


class BaseTransformationHandler:

    condition_evaluator = BooleanAstHandler
    condition_key = "condition"

    @classmethod
    def eval_condition(cls, obj, params, passWholeConifg=False, **kwargs):
        if passWholeConifg:
            if isDict(obj, keys=[cls.condition_key]):
                obj = obj.get(cls.condition_key, None)
            else:
                raise TypeError(f"Expected obj to be a Dictionary with the key {cls.condition_key}, instead got: {type(obj)} -> {obj}")
        if isDict(obj):
            return cls.condition_evaluator.run(obj, params or {}, **kwargs)
        else:
            raise TypeError(f"Expected obj to be a Dictionary, instead got: {type(obj)} -> {obj}")

class ModelDataTransformationHandler(BaseTransformationHandler):

    form_processing_config_field = "config"

    model_key = "model"

    field_type_key = "field_type"
    answer_tree_key = "answers"

    code_key = "code"   # In the config its easier to use codes to link to groups

    @classmethod
    def get_model(cls, obj, passWholeConifg=False):
        if passWholeConifg:
            if isDict(obj, keys=[cls.model_key]):
                obj = obj.get(cls.model_key, None)
            else:
                raise TypeError(f"Expected obj to be a Dictionary with the key {cls.condition_key}, instead got: {type(obj)} -> {obj}")
        if isString(obj):
            model = TRANSFORMATION_REGISTRY.get(obj)
            if(model == None):
                raise ValueError(f"Model: {obj} is not a registered Model for Transformation")
            else:
                return model
        else:
            raise TypeError(f"Expected a non-empty string for the model, instead got: {type(obj)} -> {obj}")

    @classmethod
    def getConfigsByFormType(cls, form_type_id): # Returns a Query Set
        try:
            form_type_id = uuid.UUID(form_type_id)
        except Exception as e:
            raise TypeError(f"Can not get UUID from: {type(form_type_id)} -> {form_type_id}\n\t{e}")
        return FormProcessingConfig.objects.filter(form_type__id=form_type_id).values_list(cls.form_processing_config_field, flat=True)

    @classmethod
    def 

    @classmethod
    def execute(cls, answerTree):
        if isDict(answerTree, [cls.field_type_key, cls.answer_tree_key]):
            field_type_id = answerTree.get(cls.field_type_key, None)
            if isString(field_type_id):
                configs = cls.getConfigsByFormType(field_type_id)
            else:
                raise TypeError(f"Expected the field '{cls.field_type_key} to be a non-empty string, instead got: {type(field_type_id)} -> {field_type_id}")
        else:
            raise TypeError(f"Expected answerTree to be a Dictionary with fields: [{cls.field_type_key}, {cls.answer_tree_key}].\nInstead got: {type(answerTree)}\n\t{answerTree}")
        



        