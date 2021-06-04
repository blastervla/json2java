import json
import os

from colorama import Fore, Style, init
from genson import SchemaBuilder


def clearScreen():
    os.system('cls' if os.name == 'nt' else 'clear')


def getClassName(snakeStr):
    camel = toLowerCamelCase(snakeStr)
    className = camel.title()[0] + camel[1:]
    if className == "List" or className == "Object":
        className = "Item" + className
    return className


def toLowerCamelCase(snakeStr):
    components = snakeStr.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


# Didn't give much thought to this, it's pretty ugly
# TODO: Refactor and give this a bit more love
def mostGenericType(typesList):
    mostGeneric = typesList[0]
    for candidateType in typesList:
        if mostGeneric == 'string':
            if candidateType == 'number' or candidateType == 'integer':
                mostGeneric = 'null'
            else:
                mostGeneric = 'string'
        elif mostGeneric == 'integer':
            if candidateType == 'number':
                mostGeneric = 'number'
            elif candidateType == 'integer':
                mostGeneric = 'integer'
            else:
                mostGeneric = 'null'
        elif mostGeneric == 'number':
            if candidateType == 'number' or 'integer':
                mostGeneric = 'number'
            else:
                mostGeneric = 'null'
        elif mostGeneric == 'object':
            mostGeneric = 'object'
        else:
            if candidateType == 'object':
                mostGeneric = 'object'
            else:
                mostGeneric = 'null'
    return mostGeneric


# noinspection PyShadowingNames
def recursiveJson2Java(schema, name, isTopLevel, topLevelOnly, levelIndent):
    if "type" in schema:
        schemaType = schema["type"]
    else:
        schemaType = mostGenericType(list(map(lambda x: x["type"], schema["anyOf"])))
        schema = list(filter(lambda x: x["type"] == schemaType, schema["anyOf"]))[0]

    if type(schemaType) == list:
        schemaType = mostGenericType(schemaType)

    if schemaType == "object":
        return toJavaObject(schema, name, isTopLevel, topLevelOnly, levelIndent)
    elif schemaType == "array":
        return toJavaList(schema, name, topLevelOnly, levelIndent)
    else:  # primitive
        return toJavaPrimitivesOrThrowError(schemaType, name, levelIndent)


# noinspection PyShadowingNames
def toJavaList(schema, name, topLevelOnly, levelIndent):
    if "items" not in schema or schema["items"] is None or "type" not in schema["items"]:
        itemsType = 'null'
    else:
        itemsType = schema["items"]["type"]
    if itemsType == "object":
        className = getClassName(name.rstrip("s")) if not topLevelOnly else "Map<String, Object>"
        res = levelIndent + "public List<" + className + "> " + toLowerCamelCase(name) + ";\n"
        if not topLevelOnly:
            recRes = recursiveJson2Java(schema["items"], className, False, topLevelOnly, levelIndent)
            recRes = '\n'.join(recRes.split('\n')[:-2]) + "\n"
            res += recRes
        return res
    else:
        return toJavaPrimitivesOrThrowError(itemsType, name, levelIndent)


# noinspection PyShadowingNames
def toJavaPrimitivesOrThrowError(primitiveType, name, levelIndent):
    if primitiveType == "string":
        return levelIndent + "public String " + toLowerCamelCase(name) + ";\n"
    elif primitiveType == "integer":
        return levelIndent + "public Integer " + toLowerCamelCase(name) + ";\n"
    elif primitiveType == "number":
        return levelIndent + "public Float " + toLowerCamelCase(name) + ";\n"
    elif primitiveType == "boolean":
        return levelIndent + "public Boolean " + toLowerCamelCase(name) + ";\n"
    elif primitiveType == "null":
        return levelIndent + "public Object " + toLowerCamelCase(name) + "; // Was null in JSON\n"
    else:
        print("UNKNOWN TYPE '" + primitiveType + "'")
        return "ERROR\n"


# noinspection PyShadowingNames
def toJavaObject(schema, name, isTopLevel, topLevelOnly, levelIndent):
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


# ====== MAIN FLOW ====== #

init()

name = input(Style.NORMAL + Fore.CYAN + "Gimme a name (ANY name) for the Java class\n" + Style.RESET_ALL)

isTopLevelOnly = "S" in input(Fore.CYAN + "Would you like to have a ["
                              + Style.RESET_ALL + Style.BRIGHT + "S"
                              + Style.RESET_ALL + Fore.CYAN + Style.NORMAL + "]hallow (Maps) or["
                              + Style.RESET_ALL + Style.BRIGHT + "D"
                              + Style.RESET_ALL + Fore.CYAN + Style.NORMAL + "]eep (Model objects) model?\n"
                              + Style.RESET_ALL)

lines = ""
x = input(Fore.CYAN
          + "Gimme a json, hit ENTER twice, and I'll do the magic\nTIP: Input it with line breaks if it's"
            "really big, since some terminals only admit a maximum amount of characters per line.\n "
          + Style.RESET_ALL)
while x:
    lines += x + "\n"
    x = input()

schemaBuilder = SchemaBuilder()
schemaBuilder.add_object(json.loads(lines))
schema = schemaBuilder.to_schema()

print(Style.RESET_ALL + Fore.CYAN + "\n\n======================================")
print(Style.RESET_ALL + Fore.CYAN + "====== Javification in progress ======")
print(Style.RESET_ALL + Fore.CYAN + "======================================\n\n" + Style.RESET_ALL)

clearScreen()

print(recursiveJson2Java(schema, name, True, isTopLevelOnly, ""))
