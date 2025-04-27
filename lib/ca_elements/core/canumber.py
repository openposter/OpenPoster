import xml.etree.ElementTree as ET

class CANumber:
    def __init__(self, element):
        self.element = element
        self.type = self.element.tag.replace(
            "{http://www.apple.com/CoreAnimation/1.0}", "")
        self.value = self.element.get("value")

    def create(self):
        e = ET.Element(self.type)
        e.set("value", self.value)

        return e