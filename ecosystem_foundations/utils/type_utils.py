
import uuid


def isString(val, minLength=1):
    if type(val) == str and len(val) >= minLength:
        return True
    else:
        return False
    
def isInteger(val, validatorFunc=None):
    if type(val) == int:
        if callable(validatorFunc):
            return validatorFunc(val)
        else:
            return True
    else:
        return False
    
def isFloat(val, validatorFunc=None):
    if type(val) == float:
        if callable(validatorFunc):
            return validatorFunc(val)
        else:
            return True
    else:
        return False
    
def isNumber(val, validatorFunc=None):
    return isInteger(val, validatorFunc) or isFloat(val, validatorFunc)
     
def isList(val, minLen=1, allValidFunc=None, anyValidFunc=None):
    if type(val) == list and len(val) >= minLen:
        allValid = True
        anyValid = True
        if callable(allValidFunc):
            allValid = all(allValidFunc(x) for x in val)
        if callable(anyValidFunc):
            anyValid = any(anyValidFunc(x) for x in val)
        return allValid and anyValid
    else:
        return False

def isUUID(pk):
    """ UUID checking that is Required """
    if isinstance(pk, uuid.UUID):
        return True
    else:
        try:
            uuid.UUID(str(pk))
            return True
        except Exception:
            return False

def findBadIndexes(cls, answer_list=[], checkFunc=None):
    if callable(checkFunc):
        str_ret = "--- Bad Indexes for FormAnswerData ---\n"
        if(isList(answer_list)):
            for i in range(len(answer_list)):
                if isinstance(answer_list[i], FormAnswerData):
                    continue
                else:
                    str_ret += f"\t{i}: {type(answer_list[i])} --> {answer_list[i]}\n"
        return str_ret
    else:
        return f"Can not find bad indexes if checkFunc is not callable: {type(checkFunc)}"