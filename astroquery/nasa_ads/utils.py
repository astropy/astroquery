

def _get_data_from_xml(doclist, fieldname, nohitreturn=None):
    """Get the fieldname (i.e. author, title etc)
    from minidom.parseString().childNodes[0].childNodes list
    """
    result = []
    for element in doclist:
        try:
            fields = element[fieldname]
        except KeyError:
            fields = [nohitreturn]
        result.append(fields)
    return result
