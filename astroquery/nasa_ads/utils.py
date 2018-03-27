

def _get_data_from_xml(doclist, fieldname, nohitreturn=None):
    """Get the fieldname (i.e. author, title etc)
    from minidom.parseString().childNodes[0].childNodes list
    """
    result = []
    for element in doclist:
        fieldlist = element.getElementsByTagName(fieldname)
        try:
            tmp = fieldlist[0]
        except IndexError:
            fields = [nohitreturn]
        fields = []
        for field in fieldlist:  # this is useful for e.g. author field
            fields.append(field.childNodes[0].data)
        result.append(fields)
    return result
