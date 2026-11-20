from ..utils.dict_utils import isDict
from ..utils.type_utils import isList, isString, isUUID

from .models import FormAnswer, FormGroupInstance, FormInstance
import logging

from ..utils.objs.graph import DataDirectedGraph


class FormAnswerData:

    @classmethod
    def convertFieldType(cls, field_type):
        return field_type

    def __init__(self, question_id, question_code, question_field_type, answer_value):
        self.id = question_id
        self.code = question_code
        self.answer_type = self.__class__.convertFieldType(question_field_type)
        self.answer = answer_value

class FormGroupData:

    @classmethod
    def findBadIndexes(cls, answer_list=[]):
        str_ret = "--- Bad Indexes for FormAnswerData ---\n"
        for i in range(len(answer_list)):
            if isinstance(answer_list[i], FormAnswerData):
                continue
            else:
                str_ret += f"\t{i}: {type(answer_list[i])} --> {answer_list[i]}\n"
        return str_ret

    def __init__(self, group_id, group_code, answer_list=[]):
        if isUUID(group_id):
            self.id = group_id
        else:
            raise TypeError(f"Expected a UUID, or a representation of one. Instead got: {type(group_id)} --> {group_id}")
        if isString(group_code):
            self.code = group_code
        else:
            raise TypeError(f"Expected a non-empty string, instead got: {type(group_code)}")
        if isList(answer_list, minLen=0, allValidFunc=lambda x: isinstance(x, FormAnswerData)):
            self.answers = {}
            for ans in answer_list:
                if isString(ans.code):
                    self.answers[ans.code] = ans
                else:
                    continue
        else:
            raise TypeError(f"Expected a list with all elements being a FormAnswerData object, instead got: {self.__class__.findBadIndexes(answer_list)}")

    def generateAnswerDict(self):
        ans_dict = {}
        for ans in self.answers:
            if isinstance(ans, FormAnswerData):
                # Convert answers into a dictionary that can be mapped by question_code
                
                # Should check field_type here, but will ignore it for now
                cur_val = ans_dict.get(ans.code, None)
                if cur_val == None: # Nothing important existed there before, overwrite
                    ans_dict[ans.code] = ans.answer
                elif isList(cur_val):   # There existed multiple values here, or at least a list of values already
                    cur_val.append(ans.answer)
                    ans_dict[ans.code] = cur_val
                else:   # There already existed a value here that was not in list form yet, make it into a list and add the new value
                    new_val = [cur_val, ans.answer]
                    ans_dict[ans.code] = new_val
            else:
                continue
        return ans_dict

class DirectedFormInstanceGraph(DataDirectedGraph):

    logger = logging.getLogger()

    def __init__(self):
        super.__init__()

    @classmethod
    def createFormAnswerData(cls, form_answer):
        if isinstance(form_answer, FormAnswer):
            return FormAnswerData(form_answer.question.id, form_answer.question.code, form_answer.question.field_type, form_answer.value)
        else:
            raise TypeError(f"Expected a FormAnswer, instead got: {form_answer}")

    @classmethod
    def createFormGroupData(cls, group_instance):
        if isinstance(group_instance, FormGroupInstance):
            answer_list = []
            for answer in group_instance.answers.all():
                try:
                    answer_list.append(cls.createFormAnswerData(answer))
                except TypeError as e:
                    cls.logger.error(e)
                    continue
            return FormGroupData(group_instance.id, group_instance.group.code, answer_list)
        else:
            raise TypeError(f"Expected a FormGroupInstance, instead got: {group_instance}")

    @classmethod
    def createFromFormInstance(cls, id):
        try:
            instance = FormInstance.objects.get(pk=id)
        except FormInstance.DoesNotExist as e:
            instance = None
            cls.logger.error(e)
        finally:
            if instance != None:
                if instance.groups.exists():    # This represents FormGroupInstances, not FormGroups
                    graph = cls()
                    for group in instance.groups.all():
                        try:
                            graph.addDataVertex(group.id, cls.createFormGroupData(group))
                            if group.children.exists():
                                for child in group.children.all():
                                    graph.addEdge(group.id, child.id)
                            else:
                                continue
                        except TypeError as e:
                            cls.logger.error(e)
                            continue
                    if not graph.isEmpty():
                        return graph
                    else:
                        return None
                else:
                    return None
            else:
                return None
                    