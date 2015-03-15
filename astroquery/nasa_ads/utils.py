

def get_data_from_xml(doclist, fieldname, nohitreturn=None):
    result = []
    for element in doclist:
        fieldlist = element.getElementsByTagName(fieldname)
        try:
            tmp = fieldlist[0]
        except IndexError:
            fields = [nohitreturn]
        fields = []
        for field in fieldlist: # this is useful for e.g. author field
            fields.append(field.childNodes[0].data.encode("utf-8"))
        result.append(fields)
    return result
