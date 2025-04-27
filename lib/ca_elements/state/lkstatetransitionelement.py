import xml.etree.ElementTree as ET

from ..animation.caspringanimation import CASpringAnimation

class LKStateTransitionElement:
    def __init__(self, element):
        self.element = element
        self.key = self.element.get("key")
        self.targetId = self.element.get("targetId")

        self.animations = []
        self._animations = self.element.findall(
            "{http://www.apple.com/CoreAnimation/1.0}animation")
        if self._animations is not None:
            for animation in self._animations:
                if animation.get("type") == "CASpringAnimation":
                    self.animations.append(CASpringAnimation(animation))

    def create(self):
        e = ET.Element('LKStateTransitionElement')
        e.set("key", self.key)
        e.set("targetId", self.targetId)
        if self._animations is not None:
            for animation in self.animations:
                e.append(animation.create())

        return e