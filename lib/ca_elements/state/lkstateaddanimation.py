import xml.etree.ElementTree as ET

from ..animation.cakeyframeanimation import CAKeyframeAnimation
from ..animation.caspringanimation import CASpringAnimation

class LKStateAddAnimation:
    def __init__(self, element):
        self.element = element
        self.targetId = self.element.get("targetId")
        self.keyPath = self.element.get("keyPath")
        
        self.animations = []
        self._animations = self.element.findall(
            "{http://www.apple.com/CoreAnimation/1.0}animation")
        if self._animations is not None:
            for animation in self._animations:
                if animation.get("type") == "CAKeyframeAnimation":
                    self.animations.append(CAKeyframeAnimation(animation))
                elif animation.get("type") == "CASpringAnimation":
                    self.animations.append(CASpringAnimation(animation))

    def create(self):
        e = ET.Element('LKStateAddAnimation')
        e.set("targetId", self.targetId)
        e.set("keyPath", self.keyPath)
        if self._animations is not None:
            for animation in self.animations:
                e.append(animation.create())
        return e