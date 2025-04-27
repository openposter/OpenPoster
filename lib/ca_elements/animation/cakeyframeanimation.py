import xml.etree.ElementTree as ET

from .caanimation import CAAnimation
from ..core import CANumber

class CAKeyframeAnimation(CAAnimation):
    def __init__(self, element):
        super().__init__(element)
        if self.tag == "p":
            self.key = self.element.get("key")
        self.type = "CAKeyframeAnimation"

        # KEYFRAME
        self.calculationMode = self.element.get("calculationMode")
        self.additive = self.element.get("additive")
        self.cumulative = self.element.get("cumulative")

        self.keyTimes = []
        self._keyTimes = self.element.find(
            "{http://www.apple.com/CoreAnimation/1.0}keyTimes")
        if self._keyTimes is not None:
            for keyTime in self._keyTimes:
                self.keyTimes.append(CANumber(keyTime))
                
        self.timingFunctions = []
        self._timingFunctions = self.element.find(
            "{http://www.apple.com/CoreAnimation/1.0}timingFunctions")
        if self._timingFunctions is not None:
            for timingFunction in self._timingFunctions:
                self.timingFunctions.append(timingFunction)

        self.values = []
        self._values = self.element.find(
            "{http://www.apple.com/CoreAnimation/1.0}values")
        if self._values is not None:
            for value in self._values:
                self.values.append(CANumber(value))

    def create(self):
        e = super().create()

        # KEYFRAME
        self.setValue(e, "calculationMode", self.calculationMode)
        self.setValue(e, "additive", self.additive)
        self.setValue(e, "cumulative", self.cumulative)
        
        if self.tag == "p":
            self.setValue(e, "key", self.key)

        if self.keyTimes:
            keyTimes = ET.SubElement(e, "keyTimes")
            for keyTime in self.keyTimes:
                keyTimes.append(keyTime.create())
                
        if self.timingFunctions:
            timingFunctions = ET.SubElement(e, "timingFunctions")
            for timingFunction in self.timingFunctions:
                timingFunctions.append(timingFunction)

        if self.values:
            values = ET.SubElement(e, "values")
            for value in self.values:
                values.append(value.create())

        return e