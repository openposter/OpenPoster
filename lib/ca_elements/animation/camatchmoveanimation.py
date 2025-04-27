import xml.etree.ElementTree as ET

from .caanimation import CAAnimation
from ..core.cgpoint import CGPoint

class CAMatchMoveAnimation(CAAnimation):
    def __init__(self, element):
        super().__init__(element)
        self.type = "CAMatchMoveAnimation"

        # MATCH MOVE
        self.additive = self.element.get("additive")
        self.appliesX = self.element.get("appliesX")
        self.appliesY = self.element.get("appliesY")
        self.appliesScale = self.element.get("appliesScale")
        self.appliesRotation = self.element.get("appliesRotation")
        self.targetsSuperlayer = self.element.get("targetsSuperlayer")
        self.usesNormalizedCoordinates = self.element.get(
            "usesNormalizedCoordinates")

        self.sourceLayer = None
        self._sourceLayer = self.element.find(
            "{http://www.apple.com/CoreAnimation/1.0}sourceLayer")
        if self._sourceLayer is not None:
            self.sourceLayer = self._sourceLayer

        self.sourcePoints = []
        self._sourcePoints = self.element.find(
            "{http://www.apple.com/CoreAnimation/1.0}sourcePoints")
        if self._sourcePoints != []:
            for sourcePoint in self._sourcePoints:
                self.sourcePoints.append(CGPoint(sourcePoint))

        self.animationType = None
        self._animationType = self.element.find(
            "{http://www.apple.com/CoreAnimation/1.0}animationType")
        if self._animationType is not None:
            self.animationType = self._animationType

    def create(self):
        e = super().create()

        # MATCH MOVE
        self.setValue(e, "additive", self.additive)
        self.setValue(e, "appliesX", self.appliesX)
        self.setValue(e, "appliesY", self.appliesY)
        self.setValue(e, "appliesScale", self.appliesScale)
        self.setValue(e, "appliesRotation", self.appliesRotation)
        self.setValue(e, "targetsSuperLayer", self.targetsSuperlayer)
        self.setValue(e, "usesNormalizedCoordinates",
                      self.usesNormalizedCoordinates)

        if self.sourceLayer is not None:
            sourceLayer = ET.SubElement(e, "sourceLayer")
            self.setValue(sourceLayer, "object",
                          self.sourceLayer.get("object"))

        if self.sourcePoints != []:
            sourcePoints = ET.SubElement(e, "sourcePoints")
            for sourcePoint in self.sourcePoints:
                sourcePoints.append(sourcePoint.create())

        if self.animationType is not None:
            ET.SubElement(e, "animationType")

        return e