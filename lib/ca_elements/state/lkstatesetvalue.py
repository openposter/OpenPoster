import xml.etree.ElementTree as ET

class LKStateSetValue:
    def __init__(self, element):
        self.element = element
        self.targetId = self.element.get("targetId")
        self.keyPath = self.element.get("keyPath")
        self.value = self.element[0].get("value")
        self.valueType = self.element[0].get("type")

    def create(self):
        e = ET.Element('LKStateSetValue')
        e.set("targetId", self.targetId)
        e.set("keyPath", self.keyPath)
        val = ET.SubElement(e, 'value')
        val.set("value", self.value)
        val.set("type", self.valueType)

        return e