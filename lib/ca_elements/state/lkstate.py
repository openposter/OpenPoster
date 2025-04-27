import xml.etree.ElementTree as ET

from .lkstatesetvalue import LKStateSetValue
from .lkstateaddanimation import LKStateAddAnimation

class LKState:
    def __init__(self, element):
        self.element = element
        self.name = self.element.get("name")

        self.elements = []
        self._elements = self.element.find(
            "{http://www.apple.com/CoreAnimation/1.0}elements")
        if self._elements is not None:
            for element in self._elements:
                if element.tag == "{http://www.apple.com/CoreAnimation/1.0}LKStateSetValue":
                    self.elements.append(LKStateSetValue(element))
                elif element.tag == "{http://www.apple.com/CoreAnimation/1.0}LKStateAddAnimation":
                    self.elements.append(LKStateAddAnimation(element))

    def create(self):
        e = ET.Element('LKState')
        e.set("name", self.name)
        if self._elements is not None:
            elements = ET.SubElement(e, 'elements')
            for element in self.elements:
                elements.append(element.create())

        return e