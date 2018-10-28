import traceback

class LawError(Exception):
    def __init__(self, law=None, error_detail="", *args, **kwargs):
        if law is None:
            self._law_num = "UNK"
            self._law_name = "UNK" 
            self._code = "UNK" 
        else:
            self._law = law
            self._code = law.code
            try:
                self._law_num = law.lawnum
            except:
                self._law_num = "UNK"
            try:
                self._law_name = law.name
            except:
                self._law_name = "UNK" 
            
        self.error_detail = "\n" + error_detail + "\n"        

    def __str__(self):                      # エラーメッセージ
        return (
            "## {0} ##".format(self.__class__.__name__) +\
            "\nLawName: \t"+self._law_name +\
            "\nLawNum:  \t"+self._law_num +\
            "\nCode:    \t"+str(self._code) + self.error_detail +\
            "\n\n"
            )

class EncodingError(LawError):
    pass

class ProvisionError(LawError):
    pass

class HieralchyError(LawError):
    pass

class XMLStructureError(LawError):
    pass

class LawElementNumberError(LawError):
    pass
