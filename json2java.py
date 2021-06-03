# You can get the schema at https://www.liquid-technologies.com/online-json-to-schema-converter
# Use "List Validation" in Array rules setting

import json
from genson import SchemaBuilder

def getClassName(snakeStr):
    camel = toLowerCamelCase(snakeStr)
    name = camel.title()[0] + camel[1:]
    if name == "List" or name == "Object":
        name = "Item" + name
    return name


def toLowerCamelCase(snakeStr):
    components = snakeStr.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def mostGenericType(typesList):
    mostGeneric = typesList[0]
    for type in typesList:
        if mostGeneric == 'string':
            if type == 'number' or type == 'integer':
                mostGeneric = 'null'
            else:
                mostGeneric = 'string'
        elif mostGeneric == 'integer':
            if type == 'number':
                mostGeneric = 'number'
            elif type == 'integer':
                mostGeneric = 'integer'
            else:
                mostGeneric = 'null'
        elif mostGeneric == 'number':
            if type == 'number' or 'integer':
                mostGeneric = 'number'
            else:
                mostGeneric = 'null'
        elif mostGeneric == 'object':
            mostGeneric = 'object'
        else:
            if type == 'object':
                mostGeneric = 'object'
            else:
                mostGeneric = 'null'
    return mostGeneric


def recursiveJson2Java(schema, name, isTopLevel, topLevelOnly, levelIndent):
    if "type" in schema:
        schemaType = schema["type"]
    else:
        schemaType = mostGenericType(list(map(lambda x: x["type"], schema["anyOf"])))
        schema = list(filter(lambda x: x["type"] == schemaType, schema["anyOf"]))[0]

    if type(schemaType) == list:
        schemaType = mostGenericType(schemaType)

    if schemaType == "object":
        className = getClassName(name)
        res = ""
        if "properties" in schema and (not topLevelOnly or isTopLevel):
            res += levelIndent + "public " + ("" if isTopLevel else "static ") + "class " + className + " {\n"
            for prop in schema["properties"]:
                res += recursiveJson2Java(schema["properties"][prop], prop, False, topLevelOnly, levelIndent + "    ")
            res += levelIndent + "}\n"
        else:
            className = "Map<String, Object>"

        if not isTopLevel:
            res += levelIndent + "public " + className + " " + toLowerCamelCase(name) + ";\n"

        return res
    elif schemaType == "array":
        if "items" not in schema or schema["items"] is None or "type" not in schema["items"]:
            itemsType = 'null'
        else:
            itemsType = schema["items"]["type"]

        if itemsType == "object":
            className = getClassName(name.rstrip("s"))
            res = levelIndent + "public List<" + className + "> " + toLowerCamelCase(name) + ";\n"
            if not topLevelOnly:
                recRes = recursiveJson2Java(schema["items"], className, False, topLevelOnly, levelIndent)
                recRes = '\n'.join(recRes.split('\n')[:-2]) + "\n"
                res += recRes
            return res
        elif itemsType == "string":
            return levelIndent + "public List<String> " + toLowerCamelCase(name) + ";\n"
        elif itemsType == "integer":
            return levelIndent + "public List<Integer> " + toLowerCamelCase(name) + ";\n"
        elif itemsType == "number":
            return levelIndent + "public List<Float> " + toLowerCamelCase(name) + ";\n"
        elif itemsType == "boolean":
            return levelIndent + "public List<Boolean> " + toLowerCamelCase(name) + ";\n"
        elif itemsType == "null":
            return levelIndent + "public List<Object> " + toLowerCamelCase(name) + "; // Was null in JSON\n"
        else:
            print("UNKNOWN TYPE '" + itemsType + "' in array")
            return "ERROR\n"
    elif schemaType == "string":
        return levelIndent + "public String " + toLowerCamelCase(name) + ";\n"
    elif schemaType == "integer":
        return levelIndent + "public Integer " + toLowerCamelCase(name) + ";\n"
    elif schemaType == "number":
        return levelIndent + "public Float " + toLowerCamelCase(name) + ";\n"
    elif schemaType == "boolean":
        return levelIndent + "public Boolean " + toLowerCamelCase(name) + ";\n"
    elif schemaType == "null":
        return levelIndent + "public Object " + toLowerCamelCase(name) + "; // Was null in JSON\n"
    else:
        print("UNKNOWN TYPE '" + schemaType + "'")
        return "ERROR\n"


name = input("Gimme a name (ANY name) for the Java class\n")

isTopLevelOnly = "S" in input("Would you like to have a Shallow (Maps) or Deep (Model objects) model?\n")

lines = ""
x = input("Gimme a json, and I'll do the magic\n")
while x:
    lines += x + "\n"
    x = input()

schemaBuilder = SchemaBuilder()
schemaBuilder.add_object(json.loads(lines))
schema = schemaBuilder.to_schema()

print(recursiveJson2Java(schema, name, True, isTopLevelOnly, ""))
