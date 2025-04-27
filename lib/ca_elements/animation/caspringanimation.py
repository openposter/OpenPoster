from .caanimation import CAAnimation

class CASpringAnimation(CAAnimation):
    def __init__(self, element):
        super().__init__(element)
        self.type = "CASpringAnimation"

        # SPRING
        self.damping = self.element.get("damping")
        self.mass = self.element.get("mass")
        self.stiffness = self.element.get("stiffness")
        self.velocity = self.element.get("velocity")
        self.micarecalc = self.element.get("mica_autorecalculatesDuration")

    def create(self):
        e = super().create()

        # SPRING
        self.setValue(e, "damping", self.damping)
        self.setValue(e, "mass", self.mass)
        self.setValue(e, "stiffness", self.stiffness)
        self.setValue(e, "velocity", self.velocity)
        # TODO: check if this is necessary
        self.setValue(e, "mica_autorecalculatesDuration", self.micarecalc)

        return e