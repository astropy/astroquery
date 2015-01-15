



def get_field(record, field):
    value = record.findAll(field)
    if len(value) == 0:
        return ""
    else:
        return value[0].text.encode("utf-8")
