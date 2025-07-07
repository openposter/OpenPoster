import xml.etree.ElementTree as ET

from .cgimage import CGImage

from ..state.lkstate import LKState
from ..state.lkstatetransition import LKStateTransition

from ..animation.cakeyframeanimation import CAKeyframeAnimation
from ..animation.camatchmoveanimation import CAMatchMoveAnimation

class CALayer:
    def __init__(self, id="", type="default", name="New Layer"): 
        # create default layer without reading from preexisting
        self.layer_class = "CALayer"
        self.id = id
        self.name = name
        self.position = ["0","0"]
        self.bounds = ["0", "0", "100", "100"]
        self.hidden = False
        self.transform = None
        self.anchorPoint = None
        self.geometryFlipped = "0"
        self.opacity = "1.0"
        self.zPosition = None
        self.backgroundColor = "0 0 0" # black
        self.cornerRadius = None

        if self.layer_class == "CALayer":
            self._content = None
            self.sublayers = {}
            self._sublayerorder = []
            self.states = {}
            self.stateTransitions = []
            self.animations = []

        if type == "text":
            self.layer_class = "CATextLayer"
            self.string = "Text Layer"
            self.font = "SF Pro Text Regular"
            self.tracking = "0"
            self.leading = "0"
            self.verticalAlignmentMode = "top"
            self.wrapped = "1"
            self.resizingMode = "auto"
            self.allowsEdgeAntialiasing = "1"
            self.allowsGroupOpacity = "1"
            self.contentsFormat = "AutomaticAppKit"
            self.cornerCurve = "circular"
            self.classIfAvailable = "LKTextLayer"
            self.backgroundColor = None

            self._content = None
            self.sublayers = {}
            self._sublayerorder = []
            self.states = {}
            self.stateTransitions = []
            self.animations = []
        elif type == "image":
            self.content = CGImage("image.png")
            self._content = {} # this is required because inspector code looks for it even though it shouldnt pls fix enkei
            self.sublayers = {}
            self._sublayerorder = []
            self.states = {}
            self.stateTransitions = []
            self.animations = []

        

    def load(self, element):
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
        
        self.layer_class = self.element.tag.split('}')[-1] if '}' in self.element.tag else self.element.tag
        
        # Handle CATextLayer specific properties
        if self.layer_class == "CATextLayer":
            self.tracking = self.element.get('tracking')
            self.leading = self.element.get('leading')
            self.verticalAlignmentMode = self.element.get('verticalAlignmentMode')
            self.wrapped = self.element.get('wrapped')
            self.resizingMode = self.element.get('resizingMode')
            self.allowsEdgeAntialiasing = self.element.get('allowsEdgeAntialiasing')
            self.allowsGroupOpacity = self.element.get('allowsGroupOpacity')
            self.contentsFormat = self.element.get('contentsFormat')
            self.cornerCurve = self.element.get('cornerCurve')
            self.classIfAvailable = self.element.get('classIfAvailable')

            font_element = self.element.find('{http://www.apple.com/CoreAnimation/1.0}font')
            if font_element is not None:
                self.font = font_element.get('value')
            
            string_element = self.element.find('{http://www.apple.com/CoreAnimation/1.0}string')
            if string_element is not None:
                self.string = string_element.get('value')
        
        self._content = self.element.find(
            '{http://www.apple.com/CoreAnimation/1.0}contents')
        if self._content is not None:
            if self._content.get('type') == "CGImage":
                self.content = CGImage(self._content.get('src'))

        self.sublayers = {}
        self._sublayerorder = []
        self._sublayers = self.element.find(
            "{http://www.apple.com/CoreAnimation/1.0}sublayers")
        if self._sublayers is not None:
            for layer_element in self._sublayers:
                layer_class_name = layer_element.tag.split('}')[-1] if '}' in layer_element.tag else layer_element.tag
                if layer_class_name:
                    new_layer = CALayer().load(layer_element)
                    self.sublayers[new_layer.id] = new_layer
                    self._sublayerorder.append(new_layer.id)

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
        return self

       
    def addlayer(self, layer): # layer = CALayer
        # add a child layer to the current layer
        self.sublayers[layer.id] = layer
        self._sublayerorder.append(layer.id)
        return self.findlayer(layer.id)

    def removelayer(self, layer_id):
        if layer_id in self.sublayers:
            del self.sublayers[layer_id]
            if layer_id in self._sublayerorder:
                self._sublayerorder.remove(layer_id)
            return True
        
        for sublayer in self.sublayers.values():
            if sublayer.removelayer(layer_id):
                return True
            
        return False

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
        e = ET.Element(self.layer_class if self.layer_class else 'CALayer')
        e.set('id', self.id)
        e.set('name', self.name)
        e.set('position', " ".join(self.position))
        e.set('bounds', " ".join(self.bounds))
        if self.hidden:
            e.set('hidden', 'true')
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
            
        # Handle CATextLayer specific properties
        if self.layer_class == "CATextLayer":
            if hasattr(self, 'tracking'): e.set('tracking', self.tracking)
            if hasattr(self, 'leading'): e.set('leading', self.leading)
            if hasattr(self, 'verticalAlignmentMode'): e.set('verticalAlignmentMode', self.verticalAlignmentMode)
            if hasattr(self, 'wrapped'): e.set('wrapped', self.wrapped)
            if hasattr(self, 'resizingMode'): e.set('resizingMode', self.resizingMode)
            if hasattr(self, 'allowsEdgeAntialiasing'): e.set('allowsEdgeAntialiasing', self.allowsEdgeAntialiasing)
            if hasattr(self, 'allowsGroupOpacity'): e.set('allowsGroupOpacity', self.allowsGroupOpacity)
            if hasattr(self, 'contentsFormat'): e.set('contentsFormat', self.contentsFormat)
            if hasattr(self, 'cornerCurve'): e.set('cornerCurve', self.cornerCurve)
            if hasattr(self, 'classIfAvailable'): e.set('classIfAvailable', self.classIfAvailable)

            if hasattr(self, 'font'):
                font_elem = ET.Element('font')
                font_elem.set('type', 'string')
                font_elem.set('value', self.font)
                e.append(font_elem)
            
            if hasattr(self, 'string'):
                string_elem = ET.Element('string')
                string_elem.set('type', 'string')
                string_elem.set('value', self.string)
                e.append(string_elem)

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
