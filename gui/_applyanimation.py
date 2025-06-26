from PySide6.QtCore import QPointF, QVariantAnimation, QTimeLine, QEasingCurve
from PySide6.QtWidgets import QGraphicsItemAnimation

class ApplyAnimation:
    def __init__(self, scene):
        self.scene = scene

    def applyAnimationsToPreview(self, animation_element) -> None:
        targetId = animation_element.targetId
        
        keyPath = getattr(animation_element, "keyPath", None)
        if keyPath is None:
            print("Warning: animation_element missing keyPath attribute")
            return
            
        for item in self.scene.items():
            if hasattr(item, "data") and item.data(0) == targetId:
                if hasattr(animation_element, "animations"):
                    for anim in animation_element.animations:
                        if anim.type == "CAKeyframeAnimation":
                            self.applyKeyframeAnimationToItem(item, keyPath, anim)
    
    def applyKeyframeAnimationToItem(self, item, keyPath, anim) -> None:
        if keyPath is None:
            print("Warning: keyPath is None")
            return
            
        animation = QVariantAnimation()
        
        try:
            if hasattr(anim, "duration"):
                if isinstance(anim.duration, (int, float)):
                    duration_ms = int(float(anim.duration) * 1000)
                else:
                    duration_ms = int(float(anim.duration) * 1000)
            else:
                duration_ms = 1000
                
            animation.setDuration(duration_ms)
        except (ValueError, TypeError) as e:
            print(f"Error setting animation duration: {e}")
            animation.setDuration(1000)
            
        if hasattr(anim, "keyTimes") and anim.keyTimes and hasattr(anim, "values") and anim.values:
            keyframes = []
            
            for i, keyTime in enumerate(anim.keyTimes):
                if i < len(anim.values):
                    try:
                        time_pct = 0
                        if hasattr(keyTime, 'value') and keyTime.value is not None:
                            time_pct = float(keyTime.value)
                        
                        value_obj = anim.values[i]
                        anim_value = 0
                        if hasattr(value_obj, 'value') and value_obj.value is not None:
                            anim_value = float(value_obj.value)
                            
                        keyframes.append((time_pct, anim_value))
                    except (ValueError, TypeError) as e:
                        print(f"Error parsing keyframe: {e}")
                    
            if "position.x" in keyPath:
                animation.setStartValue(item.x())
                for time_pct, value in keyframes:
                    try:
                        animation.setKeyValueAt(time_pct, value)
                    except (ValueError, TypeError) as e:
                        print(f"Error setting keyframe at {time_pct} with value {value}: {e}")
                
                if keyframes:
                    animation.setEndValue(keyframes[-1][1])
                
                def updatePosX(value):
                    item.setX(value)
                
                animation.valueChanged.connect(updatePosX)
                
            elif "position.y" in keyPath:
                animation.setStartValue(item.y())
                for time_pct, value in keyframes:
                    try:
                        animation.setKeyValueAt(time_pct, value)
                    except (ValueError, TypeError) as e:
                        print(f"Error setting keyframe at {time_pct} with value {value}: {e}")
                
                if keyframes:
                    animation.setEndValue(keyframes[-1][1])
                
                def updatePosY(value):
                    item.setY(value)
                
                animation.valueChanged.connect(updatePosY)
        
        if hasattr(self, 'animations_playing') and self.animations_playing:
            animation.start()
        
        if not hasattr(self, 'animations'):
            self.animations = []
            
        if hasattr(animation, 'duration') and animation.duration() > 0:
            self.animations.append((animation, anim))
        
    def applyTransitionAnimationToPreview(self, targetId, keyPath, animation) -> None:
        if keyPath is None:
            print("Warning: keyPath is None")
            return
            
        for item in self.scene.items():
            if hasattr(item, "data") and item.data(0) == targetId:
                if animation.type == "CASpringAnimation":
                    self.applySpringAnimationToItem(item, keyPath, animation)
                    
    def applySpringAnimationToItem(self, item, keyPath, animation) -> None:
        damping = 10.0
        mass = 1.0
        stiffness = 100.0
        velocity = 0.0
        duration = 0.8
        
        if hasattr(animation, "damping"):
            try:
                damping = float(animation.damping)
            except (ValueError, TypeError):
                pass
                
        if hasattr(animation, "mass"):
            try:
                mass = float(animation.mass)
            except (ValueError, TypeError):
                pass
                
        if hasattr(animation, "stiffness"):
            try:
                stiffness = float(animation.stiffness)
            except (ValueError, TypeError):
                pass
                
        if hasattr(animation, "velocity"):
            try:
                velocity = float(animation.velocity)
            except (ValueError, TypeError):
                pass
                
        if hasattr(animation, "duration"):
            try:
                duration = float(animation.duration)
            except (ValueError, TypeError):
                pass
                
        timeline = QTimeLine(int(duration * 1000))
        timeline.setEasingCurve(QEasingCurve.OutElastic)
        timeline.setLoopCount(1)
        
        animation_obj = QGraphicsItemAnimation()
        animation_obj.setItem(item)
        animation_obj.setTimeLine(timeline)
        
        if "position.y" in keyPath:
            current_y = item.pos().y()
            target_y = current_y + 50
            animation_obj.setPosAt(0.0, QPointF(item.pos().x(), current_y))
            animation_obj.setPosAt(1.0, QPointF(item.pos().x(), target_y))
        elif "position.x" in keyPath:
            current_x = item.pos().x()
            target_x = current_x + 50
            animation_obj.setPosAt(0.0, QPointF(current_x, item.pos().y()))
            animation_obj.setPosAt(1.0, QPointF(target_x, item.pos().y()))
        elif "opacity" in keyPath:
            pass
        
        if hasattr(self, 'animations_playing') and self.animations_playing:
            timeline.start()
        
        if not hasattr(self, 'animations'):
            self.animations = []
        self.animations.append((timeline, animation))