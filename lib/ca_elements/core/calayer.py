import xml.etree.ElementTree as ET

from .cgimage import CGImage

from ..state.lkstate import LKState
from ..state.lkstatetransition import LKStateTransition

from ..animation.cakeyframeanimation import CAKeyframeAnimation
from ..animation.camatchmoveanimation import CAMatchMoveAnimation

class CALayer:
    def __init__(self, element):
        self.element = element
        self.id = self.element.get('id')
        self.name = self.element.get('name')
        self.position = self.element.get('position').split(" ")
        self.bounds = self.element.get('bounds').split(" ")
        self.hidden = True if self.element.get('hidden') == 0 else False
        self.transform = self.element.get('transform')
        self.anchorPoint = self.element.get('anchorPoint')
        self.geometryFlipped = self.element.get('geometryFlipped')
        self.opacity = self.element.get('opacity')
        self.zPosition = self.element.get('zPosition')
        self.backgroundColor = self.element.get('backgroundColor')
        self.cornerRadius = self.element.get('cornerRadius')
        
        # Store the layer class type (CALayer, CATextLayer, etc.)
        self.layer_class = self.element.get('class')
        
        # Handle CATextLayer specific properties
        if self.layer_class == "CATextLayer":
            self.string = self.element.get('string')
            self.fontSize = self.element.get('fontSize')
            self.fontFamily = self.element.get('fontFamily')
            self.alignmentMode = self.element.get('alignmentMode')
            self.color = self.element.get('color')
        
        self._content = self.element.find(
            '{http://www.apple.com/CoreAnimation/1.0}contents')
        if self._content is not None:
            if self._content.get('type') == "CGImage":
                self.content = CGImage(self._content.get('src'))
            # TODO: support more than just CGImage :skull:

        self.sublayers = {}
        self._sublayerorder = []
        self._sublayers = self.element.find(
            "{http://www.apple.com/CoreAnimation/1.0}sublayers")
        if self._sublayers is not None:
            for layer in self._sublayers:
                if layer.tag == "{http://www.apple.com/CoreAnimation/1.0}CALayer":
                    self.sublayers[layer.get('id')] = CALayer(layer)
                    self._sublayerorder.append(layer.get('id'))
                # TODO: support more specialized layer types in the future

        self.states = {}
        self._states = self.element.find(
            "{http://www.apple.com/CoreAnimation/1.0}states")
        if self._states is not None:
            for state in self._states:
                self.states[state.get("name")] = LKState(state)

        self.stateTransitions = []
        self._stateTransitions = self.element.find(
            "{http://www.apple.com/CoreAnimation/1.0}stateTransitions")
        if self._stateTransitions is not None:
            for transition in self._stateTransitions:
                self.stateTransitions.append(LKStateTransition(transition))

        self.animations = []
        self._animations = self.element.find(
            "{http://www.apple.com/CoreAnimation/1.0}animations")
        if self._animations is not None:
            for animation in self._animations:
                if animation.get("type") == "CAKeyframeAnimation":
                    self.animations.append(CAKeyframeAnimation(animation))
                elif animation.get("type") == "CAMatchMoveAnimation":
                    self.animations.append(CAMatchMoveAnimation(animation))

    def findlayer(self, uniqueid):
        # must be a unique value or it will return the first instance it finds because im too lazy - retron
        for id in self._sublayerorder:
            possiblelayer = self.sublayers.get(id)
            if possiblelayer.id == uniqueid:
                return possiblelayer
            else:
                if possiblelayer._sublayerorder is not []:
                    recursion = possiblelayer.findlayer(uniqueid)
                    if recursion is not None:
                        return recursion
        # if nothing is found
        return None

    def findanimation(self, keyPath):
        # this will only return first animation with a certain keyPath (not sure if its valid for multiple to exist) - retron
        for animation in self.animations:
            if animation.keyPath == keyPath:
                return animation
        # none are found
        return None

    def create(self):
        e = ET.Element('CALayer')
        e.set('id', self.id)
        e.set('name', self.name)
        e.set('position', " ".join(self.position))
        e.set('bounds', " ".join(self.bounds))
        if self.hidden:
            e.set('hidden', True)
        if self.transform is not None:
            e.set('transform', self.transform)
        if self.anchorPoint is not None:
            e.set('anchorPoint', self.anchorPoint)
        if self.geometryFlipped is not None:
            e.set('geometryFlipped', self.geometryFlipped)
        if self.opacity is not None:
            e.set('opacity', self.opacity)
        if self.zPosition is not None:
            e.set('zPosition', self.zPosition)
        if self.backgroundColor is not None:
            e.set('backgroundColor', self.backgroundColor)
        if self.cornerRadius is not None:
            e.set('cornerRadius', self.cornerRadius)
        
        # Set layer class type if it exists
        if self.layer_class is not None:
            e.set('class', self.layer_class)
            
        # Handle CATextLayer specific properties
        if self.layer_class == "CATextLayer":
            if hasattr(self, 'string') and self.string is not None:
                e.set('string', self.string)
            if hasattr(self, 'fontSize') and self.fontSize is not None:
                e.set('fontSize', self.fontSize)
            if hasattr(self, 'fontFamily') and self.fontFamily is not None:
                e.set('fontFamily', self.fontFamily)
            if hasattr(self, 'alignmentMode') and self.alignmentMode is not None:
                e.set('alignmentMode', self.alignmentMode)
            if hasattr(self, 'color') and self.color is not None:
                e.set('color', self.color)

        if self._content is not None:
            content = ET.SubElement(e, 'contents')
            if isinstance(self.content, CGImage):
                content.set('type', 'CGImage')
                content.set('src', self.content.src)

        if len(self._sublayerorder) > 0:
            sublayers = ET.SubElement(e, 'sublayers')
            for layer in self._sublayerorder:
                sublayers.append(self.sublayers.get(layer).create())

        if self.states != {}:
            states = ET.SubElement(e, 'states')
            for _, state in self.states.items():
                states.append(state.create())

        if self.stateTransitions != []:
            stateTransitions = ET.SubElement(e, 'stateTransitions')
            for stateTransition in self.stateTransitions:
                stateTransitions.append(stateTransition.create())

        if self.animations != []:
            animations = ET.SubElement(e, 'animations')
            for animation in self.animations:
                animations.append(animation.create())

        return e