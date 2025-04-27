import xml.etree.ElementTree as ET

from .lkstatetransitionelement import LKStateTransitionElement

class LKStateTransition:
    def __init__(self, element):
        self.element = element
        self.fromState = self.element.get("fromState")
        self.toState = self.element.get("toState")

        self.elements = []
        self._elements = self.element.find(
            "{http://www.apple.com/CoreAnimation/1.0}elements")
        if self._elements is not None:
            for element in self._elements:
                self.elements.append(LKStateTransitionElement(element))

    def create(self):
        e = ET.Element('LKStateTransition')
        e.set("fromState", self.fromState)
        e.set("toState", self.toState)

        if self._elements is not None:
            elements = ET.SubElement(e, 'elements')
            for element in self.elements:
                elements.append(element.create())

        return e