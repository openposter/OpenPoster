import xml.etree.ElementTree as ET

class CAAnimation:
    def __init__(self, element):
        self.element = element
        self.tag = self.element.tag.replace(
            "{http://www.apple.com/CoreAnimation/1.0}", "")
        self.type = "CAAnimation"

        # BASIC
        self.keyPath = self.element.get("keyPath") or "position"

        # TIMING
        self.beginTime = self.element.get("beginTime")
        self.duration = self.element.get("duration")
        self.fillMode = self.element.get("fillMode")
        self.removedOnCompletion = self.element.get("removedOnCompletion")
        self.repeatCount = self.element.get("repeatCount")
        self.repeatDuration = self.element.get("repeatDuration")
        self.speed = self.element.get("speed")
        self.timeOffset = self.element.get("timeOffset")
        self.timingFunction = self.element.get("timingFunction")

    def create(self):
        e = ET.Element(self.tag)
        self.setValue(e, "type", self.type)

        # BASIC
        self.setValue(e, "keyPath", self.keyPath)

        # TIMING
        self.setValue(e, "beginTime", self.beginTime)
        self.setValue(e, "duration", self.duration)
        self.setValue(e, "fillMode", self.fillMode)
        self.setValue(e, "removedOnCompletion", self.removedOnCompletion)
        self.setValue(e, "repeatCount", self.repeatCount)
        self.setValue(e, "repeatDuration", self.repeatDuration)
        self.setValue(e, "speed", self.speed)
        self.setValue(e, "timeOffset", self.timeOffset)
        self.setValue(e, "timingFunction", self.timingFunction)

        return e

    def setValue(self, element, key, value):
        if value is not None:
            element.set(key, value)