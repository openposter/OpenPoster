from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QObject, QTimer, QEvent
from PySide6.QtGui import QColor, QPen, QBrush, QTransform, QCursor, QPainterPath, QPainter
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsItem, QGraphicsPathItem, QApplication, QStyleOptionGraphicsItem, QWidget
import math
import platform

class HandleType:
    TopLeft = 0
    Top = 1
    TopRight = 2
    Right = 3
    BottomRight = 4
    Bottom = 5
    BottomLeft = 6
    Left = 7
    Rotation = 8

class ResizeHandle(QGraphicsRectItem):
    """Visual handle for resizing operations"""
    def __init__(self, handle_type, parent=None):
        super().__init__(parent)
        self.handle_type = handle_type
        self.setRect(-4, -4, 8, 8)
        self.setBrush(QBrush(QColor(100, 150, 255)))
        self.setPen(QPen(QColor(50, 100, 200), 1))
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        
        cursor_map = {
            HandleType.TopLeft: Qt.SizeFDiagCursor,
            HandleType.Top: Qt.SizeVerCursor,
            HandleType.TopRight: Qt.SizeBDiagCursor,
            HandleType.Right: Qt.SizeHorCursor,
            HandleType.BottomRight: Qt.SizeFDiagCursor,
            HandleType.Bottom: Qt.SizeVerCursor,
            HandleType.BottomLeft: Qt.SizeBDiagCursor,
            HandleType.Left: Qt.SizeHorCursor,
            HandleType.Rotation: Qt.PointingHandCursor
        }
        self.setCursor(cursor_map.get(handle_type, Qt.ArrowCursor))

class EditableGraphicsItem(QObject):
    """A wrapper class that adds editing capabilities to QGraphicsItems"""
    itemChanged = Signal(QGraphicsItem)
    transformChanged = Signal(QTransform)
    itemSelected = Signal(str)
    
    def __init__(self, item, parent=None):
        super(EditableGraphicsItem, self).__init__(parent)
        self.item = item
        self.handles = {}
        self.boundingRect = None
        self.rotationHandle = None
        self.boundingBoxItem = None
        self.isEditing = False
        self.originalTransform = QTransform(item.transform())
        self.initialClickPos = QPointF()
        self.initialItemPos = QPointF()
        self.initialItemTransform = QTransform()
        self.initialBoundingRect = QRectF()
        self.initialRotation = 0
        self.currentRotation = 0
        self.handleSize = 8
        self.rotateHandleSize = 10
        self.rotateHandleOffset = 20
        self.currentHandle = None
        self.aspectRatioLocked = False
        
        self.item.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.item.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.item.setAcceptHoverEvents(True)
    
    def setupBoundingBox(self):
        """Create bounding box and handles for the item"""
        if not self.item.scene():
            return
            
        self.removeBoundingBox()
            
        scene = self.item.scene()
        rect = self.item.boundingRect()
        
        self.boundingBoxItem = QGraphicsRectItem(rect)
        self.boundingBoxItem.setPen(QPen(QColor(100, 150, 255), 1, Qt.DashLine))
        self.boundingBoxItem.setBrush(QBrush(Qt.transparent))
        self.boundingBoxItem.setParentItem(self.item)
        self.boundingBoxItem.setFlag(QGraphicsItem.ItemIgnoresTransformations, False)
        
        handle_positions = [
            (rect.topLeft(), HandleType.TopLeft),
            (QPointF(rect.center().x(), rect.top()), HandleType.Top),
            (rect.topRight(), HandleType.TopRight),
            (QPointF(rect.right(), rect.center().y()), HandleType.Right),
            (rect.bottomRight(), HandleType.BottomRight),
            (QPointF(rect.center().x(), rect.bottom()), HandleType.Bottom),
            (rect.bottomLeft(), HandleType.BottomLeft),
            (QPointF(rect.left(), rect.center().y()), HandleType.Left),
        ]
        
        for pos, handle_type in handle_positions:
            handle = ResizeHandle(handle_type)
            handle.setPos(pos)
            handle.setParentItem(self.item)
            handle.setFlag(QGraphicsItem.ItemIgnoresParentOpacity, True)
            self.handles[handle_type] = handle
        
        rotation_pos = QPointF(rect.center().x(), rect.top() - self.rotateHandleOffset)
        self.rotationHandle = ResizeHandle(HandleType.Rotation)
        self.rotationHandle.setPos(rotation_pos)
        self.rotationHandle.setParentItem(self.item)
        self.rotationHandle.setBrush(QBrush(QColor(255, 100, 100)))
        self.rotationHandle.setPen(QPen(QColor(200, 50, 50), 1))
        self.rotationHandle.setFlag(QGraphicsItem.ItemIgnoresParentOpacity, True)
    
    def removeBoundingBox(self):
        """Remove bounding box and handles"""
        try:
            if self.boundingBoxItem and not self.isItemDeleted(self.boundingBoxItem):
                scene = self.boundingBoxItem.scene()
                if scene:
                    scene.removeItem(self.boundingBoxItem)
                self.boundingBoxItem = None
        except (RuntimeError, AttributeError):
            self.boundingBoxItem = None
        
        handles_to_remove = list(self.handles.values())
        for handle in handles_to_remove:
            try:
                if not self.isItemDeleted(handle):
                    scene = handle.scene()
                    if scene:
                        scene.removeItem(handle)
            except (RuntimeError, AttributeError):
                pass
        self.handles.clear()
        
        try:
            if self.rotationHandle and not self.isItemDeleted(self.rotationHandle):
                scene = self.rotationHandle.scene()
                if scene:
                    scene.removeItem(self.rotationHandle)
                self.rotationHandle = None
        except (RuntimeError, AttributeError):
            self.rotationHandle = None

    def isItemDeleted(self, item):
        """Check if a QGraphicsItem has been deleted by Qt"""
        try:
            _ = item.pos()
            return False
        except (RuntimeError, AttributeError):
            return True
    
    def updateBoundingBox(self):
        """Update the position of bounding box and handles after item moves"""
        try:
            if self.isItemDeleted(self.item):
                # If the wrapped item itself is deleted, remove all adornments and stop.
                if self.boundingBoxItem or self.handles or self.rotationHandle:
                    print(f"Main item {id(self.item)} deleted. Removing its bounding box and handles.")
                self.removeBoundingBox()
                return

            # Ensure our bounding box graphics item is still valid and exists
            if not self.boundingBoxItem or self.isItemDeleted(self.boundingBoxItem):
                if self.boundingBoxItem and self.isItemDeleted(self.boundingBoxItem):
                    # It was deleted by Qt, so nullify our reference.
                    self.boundingBoxItem = None
                # Cannot update if the box item itself is gone.
                # setupBoundingBox would be needed to recreate it if desired.
                # print(f"BoundingBoxItem for item {id(self.item)} is None or deleted. Cannot update.")
                return 

            rect = self.item.boundingRect()
            self.boundingBoxItem.setRect(rect)
            
            handle_positions = {
                HandleType.TopLeft: rect.topLeft(),
                HandleType.Top: QPointF(rect.center().x(), rect.top()),
                HandleType.TopRight: rect.topRight(),
                HandleType.Right: QPointF(rect.right(), rect.center().y()),
                HandleType.BottomRight: rect.bottomRight(),
                HandleType.Bottom: QPointF(rect.center().x(), rect.bottom()),
                HandleType.BottomLeft: rect.bottomLeft(),
                HandleType.Left: QPointF(rect.left(), rect.center().y()),
            }
            
            active_handle_types = list(self.handles.keys()) # Iterate over a copy of keys
            for handle_type in active_handle_types:
                handle = self.handles.get(handle_type)
                if handle:
                    if not self.isItemDeleted(handle):
                        handle.setPos(handle_positions[handle_type])
                    else:
                        # Handle was deleted by Qt, remove our reference
                        del self.handles[handle_type]
            
            if self.rotationHandle:
                if not self.isItemDeleted(self.rotationHandle):
                    rotation_pos = QPointF(rect.center().x(), rect.top() - self.rotateHandleOffset)
                    self.rotationHandle.setPos(rotation_pos)
                else:
                    # Rotation handle was deleted by Qt
                    self.rotationHandle = None
                
        except (RuntimeError, AttributeError) as e:
            print(f"Error during updateBoundingBox for item {id(self.item if self.item else 'None')}: {e}")
            if self.item and self.isItemDeleted(self.item):
                print(f"Main item {id(self.item)} confirmed deleted after error. Removing bounding box.")
                self.removeBoundingBox()
            else:
                print(f"Error in updateBoundingBox, but main item not detected as deleted or item is None. Bounding box NOT removed solely due to this error.")
    
    def startEdit(self, handle_type, handle_pos):
        """Start edit operation (resize or rotate)"""
        self.isEditing = True
        self.currentHandle = handle_type
        self.initialClickPos = handle_pos
        self.initialItemPos = self.item.pos()
        self.initialItemTransform = QTransform(self.item.transform())
        self.initialBoundingRect = self.item.boundingRect()
        
        if handle_type == HandleType.Rotation:
            self.initialRotation = self.getItemRotation()
            center = self.item.mapToScene(self.initialBoundingRect.center())
            dx = handle_pos.x() - center.x()
            dy = handle_pos.y() - center.y()
            self.initialAngle = math.degrees(math.atan2(dy, dx))
        
        if hasattr(self.item, 'rect'):
            self.originalRect = self.item.rect()
        else:
            self.originalRect = self.item.boundingRect()
        
        if hasattr(self.item, 'path'):
            self.original_path_at_drag_start = self.item.path()
    
    def handleEditOperation(self, new_pos):
        """Handle move, resize, or rotate operations"""
        if not self.isEditing or not self.currentHandle:
            return
            
        if self.currentHandle == HandleType.Rotation:
            self.handleRotation(new_pos)
        else:
            self.handleResize(new_pos)
        
        self.updateBoundingBox()
        self.itemChanged.emit(self.item)
    
    def handleRotation(self, mouse_pos):
        """Handle rotation operation"""
        center = self.item.mapToScene(self.initialBoundingRect.center())
        
        dx = mouse_pos.x() - center.x()
        dy = mouse_pos.y() - center.y()
        current_angle = math.degrees(math.atan2(dy, dx))
        
        angle_diff = current_angle - self.initialAngle
        
        center_local = self.initialBoundingRect.center()

        new_transform = QTransform(self.initialItemTransform)
        new_transform.translate(center_local.x(), center_local.y())
        new_transform.rotate(angle_diff)
        new_transform.translate(-center_local.x(), -center_local.y())
        
        self.item.setTransform(new_transform)
    
    def handleResize(self, mouse_pos_scene):
        """Handle resize operation"""
        if not self.isEditing or not self.currentHandle or self.currentHandle == HandleType.Rotation:
            return

        current_mouse_local = self.item.mapFromScene(mouse_pos_scene)

        new_local_rect = QRectF(self.originalRect)

        if self.currentHandle == HandleType.TopLeft:
            new_local_rect.setTopLeft(current_mouse_local)
            new_local_rect.setBottomRight(self.originalRect.bottomRight()) 
        elif self.currentHandle == HandleType.Top:
            new_local_rect.setTop(current_mouse_local.y())
            new_local_rect.setBottom(self.originalRect.bottom())
        elif self.currentHandle == HandleType.TopRight:
            new_local_rect.setTopRight(current_mouse_local)
            new_local_rect.setBottomLeft(self.originalRect.bottomLeft()) 
        elif self.currentHandle == HandleType.Right:
            new_local_rect.setRight(current_mouse_local.x())
            new_local_rect.setLeft(self.originalRect.left())   
        elif self.currentHandle == HandleType.BottomRight:
            new_local_rect.setBottomRight(current_mouse_local)
            new_local_rect.setTopLeft(self.originalRect.topLeft())   
        elif self.currentHandle == HandleType.Bottom:
            new_local_rect.setBottom(current_mouse_local.y())
            new_local_rect.setTop(self.originalRect.top())   
        elif self.currentHandle == HandleType.BottomLeft:
            new_local_rect.setBottomLeft(current_mouse_local)
            new_local_rect.setTopRight(self.originalRect.topRight()) 
        elif self.currentHandle == HandleType.Left:
            new_local_rect.setLeft(current_mouse_local.x())
            new_local_rect.setRight(self.originalRect.right())

        new_local_rect = new_local_rect.normalized()
        
        # minimum size so you can see it I guess (change if needed)
        min_size = 50.0

        if new_local_rect.width() < min_size:
            if self.currentHandle in [HandleType.Left, HandleType.TopLeft, HandleType.BottomLeft]:
                new_local_rect.setLeft(new_local_rect.right() - min_size)
            elif self.currentHandle in [HandleType.Right, HandleType.TopRight, HandleType.BottomRight]:
                new_local_rect.setRight(new_local_rect.left() + min_size)
            else: 
                delta_w = min_size - new_local_rect.width()
                new_local_rect.adjust(-delta_w / 2, 0, delta_w / 2, 0)

        if new_local_rect.height() < min_size:
            if self.currentHandle in [HandleType.Top, HandleType.TopLeft, HandleType.TopRight]:
                new_local_rect.setTop(new_local_rect.bottom() - min_size)
            elif self.currentHandle in [HandleType.Bottom, HandleType.BottomLeft, HandleType.BottomRight]:
                new_local_rect.setBottom(new_local_rect.top() + min_size)
            else:
                delta_h = min_size - new_local_rect.height()
                new_local_rect.adjust(0, -delta_h / 2, 0, delta_h / 2)
        
        new_local_rect = new_local_rect.normalized()

        if new_local_rect.width() < min_size:
            new_local_rect.setWidth(min_size)
        if new_local_rect.height() < min_size:
            new_local_rect.setHeight(min_size)
        
        if hasattr(self.item, 'setRect'):
            self.item.setRect(new_local_rect)
        elif hasattr(self.item, 'path') and hasattr(self, 'original_path_at_drag_start'):
            op_bounds = self.original_path_at_drag_start.boundingRect()
            if op_bounds.width() == 0 or op_bounds.height() == 0: 
                self.updateBoundingBox()
                self.itemChanged.emit(self.item)
                return

            scale_x = new_local_rect.width() / op_bounds.width()
            scale_y = new_local_rect.height() / op_bounds.height()

            pivot = QPointF()
            if self.currentHandle == HandleType.TopLeft: pivot = op_bounds.bottomRight()
            elif self.currentHandle == HandleType.Top: pivot = QPointF(op_bounds.center().x(), op_bounds.bottom())
            elif self.currentHandle == HandleType.TopRight: pivot = op_bounds.bottomLeft()
            elif self.currentHandle == HandleType.Right: pivot = QPointF(op_bounds.left(), op_bounds.center().y())
            elif self.currentHandle == HandleType.BottomRight: pivot = op_bounds.topLeft()
            elif self.currentHandle == HandleType.Bottom: pivot = QPointF(op_bounds.center().x(), op_bounds.top())
            elif self.currentHandle == HandleType.BottomLeft: pivot = op_bounds.topRight()
            elif self.currentHandle == HandleType.Left: pivot = QPointF(op_bounds.right(), op_bounds.center().y())
            
            transform = QTransform().translate(pivot.x(), pivot.y()).scale(scale_x, scale_y).translate(-pivot.x(), -pivot.y())
            scaled_path = transform.map(self.original_path_at_drag_start)
            self.item.setPath(scaled_path)
            
        elif isinstance(self.item, QGraphicsEllipseItem):
             self.item.setRect(new_local_rect)
        else:
            if self.originalRect.width() == 0 or self.originalRect.height() == 0: 
                self.updateBoundingBox()
                self.itemChanged.emit(self.item)
                return

            scale_x = new_local_rect.width() / self.originalRect.width()
            scale_y = new_local_rect.height() / self.originalRect.height()

            pivot_in_item_coords = QPointF()
            if self.currentHandle == HandleType.TopLeft:    pivot_in_item_coords = self.originalRect.bottomRight()
            elif self.currentHandle == HandleType.Top:       pivot_in_item_coords = QPointF(self.originalRect.center().x(), self.originalRect.bottom())
            elif self.currentHandle == HandleType.TopRight:  pivot_in_item_coords = self.originalRect.bottomLeft()
            elif self.currentHandle == HandleType.Right:     pivot_in_item_coords = QPointF(self.originalRect.left(), self.originalRect.center().y())
            elif self.currentHandle == HandleType.BottomRight:pivot_in_item_coords = self.originalRect.topLeft()
            elif self.currentHandle == HandleType.Bottom:    pivot_in_item_coords = QPointF(self.originalRect.center().x(), self.originalRect.top())
            elif self.currentHandle == HandleType.BottomLeft:pivot_in_item_coords = self.originalRect.topRight()
            elif self.currentHandle == HandleType.Left:      pivot_in_item_coords = QPointF(self.originalRect.right(), self.originalRect.center().y())
            
            new_transform = QTransform(self.initialItemTransform)
            new_transform.translate(pivot_in_item_coords.x(), pivot_in_item_coords.y())
            new_transform.scale(scale_x, scale_y)
            new_transform.translate(-pivot_in_item_coords.x(), -pivot_in_item_coords.y())
            self.item.setTransform(new_transform)

        self.updateBoundingBox()
        self.itemChanged.emit(self.item)
    
    def endEdit(self):
        """End current edit operation"""
        self.isEditing = False
        self.currentHandle = None
        self.transformChanged.emit(self.item.transform())
    
    def getItemRotation(self):
        """Get current rotation angle of the item"""
        transform = self.item.transform()
        return math.degrees(math.atan2(transform.m12(), transform.m11()))

class CheckerboardGraphicsScene(QGraphicsScene):
    itemSelectedOnCanvas = Signal(str)
    
    def __init__(self, parent=None):
        super(CheckerboardGraphicsScene, self).__init__(parent)
        self.backgroundColor1 = QColor(200, 200, 200)
        self.backgroundColor2 = QColor(230, 230, 230)
        self.checkerboardSize = 20
        self.editMode = False
        self.currentEditableItem = None
        self.activeHandle = None
        self.isDragging = False
        self.lastMousePos = QPointF()
        self.editableItems = {}

    def setBackgroundColor(self, color1, color2):
        """Set the background colors for the checkerboard pattern"""
        self.backgroundColor1 = color1
        self.backgroundColor2 = color2
        self.update()

    def drawBackground(self, painter, rect):
        super(CheckerboardGraphicsScene, self).drawBackground(painter, rect)
        
        painter.save()
        painter.fillRect(rect, self.backgroundColor1)
        
        left = int(rect.left()) - (int(rect.left()) % self.checkerboardSize)
        top = int(rect.top()) - (int(rect.top()) % self.checkerboardSize)
        
        for x in range(left, int(rect.right()), self.checkerboardSize):
            for y in range(top, int(rect.bottom()), self.checkerboardSize):
                if (x // self.checkerboardSize + y // self.checkerboardSize) % 2 == 0:
                    painter.fillRect(x, y, self.checkerboardSize, self.checkerboardSize, self.backgroundColor2)
        
        painter.restore()
    
    def setEditMode(self, enabled):
        """Enable or disable edit mode"""
        self.editMode = enabled
        
        if enabled:
            items_to_cleanup = []
            for item, editable_item in self.editableItems.items():
                try:
                    if not self.isItemDeleted(item):
                        editable_item.setupBoundingBox()
                    else:
                        items_to_cleanup.append(item)
                except (RuntimeError, AttributeError):
                    items_to_cleanup.append(item)
            
            for item in items_to_cleanup:
                if item in self.editableItems:
                    del self.editableItems[item]
        else:
            self.deselectAllItems()
            self.currentEditableItem = None

    def makeItemEditable(self, item):
        """Make a graphics item editable"""
        if item not in self.editableItems:
            editable_item = EditableGraphicsItem(item, self)
            self.editableItems[item] = editable_item
            
            editable_item.itemChanged.connect(self.onItemChanged)
            editable_item.itemSelected.connect(self.itemSelectedOnCanvas.emit)
            
            return editable_item
        return self.editableItems[item]

    def mousePressEvent(self, event):
        """Handle mouse press events for editing"""
        if not self.editMode:
            super(CheckerboardGraphicsScene, self).mousePressEvent(event)
            return
            
        item = self.itemAt(event.scenePos(), QTransform())
        print(f"Mouse press on item: {item}")
        
        if item and isinstance(item, ResizeHandle):
            parent_item = item.parentItem()
            print(f"  Handle type: {item.handle_type}, Parent: {parent_item}")
            if parent_item in self.editableItems:
                editable_item = self.editableItems[parent_item]
                editable_item.startEdit(item.handle_type, event.scenePos())
                self.currentEditableItem = editable_item
                self.isDragging = True
                event.accept()
                return
        elif item and item in self.editableItems:
            self.selectItem(item)
            super(CheckerboardGraphicsScene, self).mousePressEvent(event)
            return
        else:
            self.deselectAllItems()
            
        super(CheckerboardGraphicsScene, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events for editing"""
        if self.editMode and self.isDragging and self.currentEditableItem:
            print(f"Dragging in scene: pos={event.scenePos()}, dragging={self.isDragging}")
            self.currentEditableItem.handleEditOperation(event.scenePos())
            event.accept()
        else:
            super(CheckerboardGraphicsScene, self).mouseMoveEvent(event)
            
            if self.editMode and self.currentEditableItem:
                self.currentEditableItem.updateBoundingBox()

    def mouseReleaseEvent(self, event):
        """Handle mouse release events for editing"""
        if self.editMode and self.isDragging and self.currentEditableItem:
            self.currentEditableItem.endEdit()
            self.isDragging = False
            event.accept()
            print(f"Edit ended, isDragging={self.isDragging}")
        else:
            super(CheckerboardGraphicsScene, self).mouseReleaseEvent(event)
        
        if self.editMode and self.currentEditableItem:
            self.currentEditableItem.updateBoundingBox()
    
    def selectItem(self, item):
        """Select an item for editing"""
        self.deselectAllItems()
        
        if item in self.editableItems and not self.isItemDeleted(item):
            try:
                editable_item = self.editableItems[item]
                editable_item.setupBoundingBox()
                self.currentEditableItem = editable_item
                self.itemSelectedOnCanvas.emit(str(id(item)))
            except (RuntimeError, AttributeError):
                if item in self.editableItems:
                    del self.editableItems[item]
    
    def deselectAllItems(self):
        """Deselect all items"""
        items_to_cleanup = []
        for item, editable_item in self.editableItems.items():
            try:
                if not self.isItemDeleted(item):
                    editable_item.removeBoundingBox()
                else:
                    items_to_cleanup.append(item)
            except (RuntimeError, AttributeError):
                items_to_cleanup.append(item)
        
        for item in items_to_cleanup:
            if item in self.editableItems:
                del self.editableItems[item]
                
        self.currentEditableItem = None
    
    def isItemDeleted(self, item):
        """Check if a QGraphicsItem has been deleted by Qt"""
        try:
            _ = item.pos()
            return False
        except (RuntimeError, AttributeError):
            return True
    
    def onItemChanged(self, item):
        """Handle item change events"""
        pass

class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None, min_zoom=0.05, max_zoom=10.0):
        super(CustomGraphicsView, self).__init__(parent)
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.current_zoom_level = 1.0
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        
        self.is_panning = False
        self.last_pan_point = QPointF()
        
        self.editMode = False
        
        self.gesture_active = False
        self.initial_pinch_distance = 0.0
        self.initial_zoom_level = 1.0
        
        self.grabGesture(Qt.PinchGesture)
        
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

    def setEditMode(self, enabled):
        """Enable or disable edit mode"""
        self.editMode = enabled
        
        if enabled:
            self.setDragMode(QGraphicsView.NoDrag)
        else:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        
        if self.scene() and hasattr(self.scene(), 'setEditMode'):
            self.scene().setEditMode(enabled)

    def wheelEvent(self, event):
        if not self.scene() or not self.scene().items():
            event.accept()
            return
            
        if hasattr(event, 'source') and event.source() == Qt.MouseEventSynthesizedBySystem:
            if event.modifiers() == Qt.ControlModifier:
                self.handleZoom(event.angleDelta().y())
            else:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - event.angleDelta().x())
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - event.angleDelta().y())
        else:
            if event.modifiers() == Qt.ControlModifier:
                self.handleZoom(event.angleDelta().y())
            else:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - event.angleDelta().x())
                self.verticalScrollBar().setValue(self.verticalScrollBar().value() - event.angleDelta().y())
            
        event.accept()
    
    def handleZoom(self, delta):
        zoom_factor = 1.0 + (delta / 1200.0)

        new_zoom_level = self.current_zoom_level * zoom_factor
        
        if new_zoom_level < self.min_zoom:
            new_zoom_level = self.min_zoom
        elif new_zoom_level > self.max_zoom:
            new_zoom_level = self.max_zoom
        
        zoom_change = new_zoom_level / self.current_zoom_level
        self.scale(zoom_change, zoom_change)
        self.current_zoom_level = new_zoom_level
    
    def mousePressEvent(self, event):
        if not self.editMode and event.button() == Qt.LeftButton:
            self.is_panning = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super(CustomGraphicsView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.editMode and self.is_panning:
            delta = event.pos() - self.last_pan_point
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.last_pan_point = event.pos()
            event.accept()
        else:
            super(CustomGraphicsView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if not self.editMode and event.button() == Qt.LeftButton and self.is_panning:
            self.is_panning = False
            self.setCursor(Qt.OpenHandCursor if self.dragMode() == QGraphicsView.ScrollHandDrag else Qt.ArrowCursor)
            event.accept()
        else:
            super(CustomGraphicsView, self).mouseReleaseEvent(event)
            
    def event(self, event):
        """Handle all events including touch gestures"""
        if event.type() == QEvent.Gesture:
            try:
                return self.handleGestureEvent(event)
            except Exception as e:
                print(f"Gesture handling error: {e}")
                
        return super(CustomGraphicsView, self).event(event)
    
    def handleGestureEvent(self, event):
        """Handle touch gesture events for zooming on macOS"""
        try:
            if hasattr(Qt, 'PinchGesture'):
                pinch_gesture = event.gesture(Qt.PinchGesture)
                if pinch_gesture:
                    self.handlePinchGesture(pinch_gesture)
                    return True
        except Exception as e:
            print(f"Error handling gesture: {e}")
        return False
    
    def handlePinchGesture(self, gesture):
        """Handle pinch gesture for zooming"""
        try:
            if hasattr(gesture, 'state'):
                if gesture.state() == Qt.GestureStarted:
                    self.gestureInProgress = True
                    self.lastGestureValue = gesture.scaleFactor()
                elif gesture.state() == Qt.GestureUpdated and self.gestureInProgress:
                    scale_change = gesture.scaleFactor() / self.lastGestureValue
                    self.lastGestureValue = gesture.scaleFactor()
                    
                    current_scale = self.transform().m11()
                    new_scale = current_scale * scale_change
                    new_scale = max(self.min_zoom, min(self.max_zoom, new_scale))
                    
                    if current_scale != 0:
                        scale_factor = new_scale / current_scale
                        if abs(scale_factor - 1.0) > 1e-9:
                            self.scale(scale_factor, scale_factor)
                elif gesture.state() in [Qt.GestureFinished, Qt.GestureCanceled]:
                    self.gestureInProgress = False
        except Exception as e:
            print(f"Error in pinch gesture: {e}")
            self.gestureInProgress = False

    def updateContentFittingZoom(self, sceneRect):
        if sceneRect.isEmpty():
            return

        padded_rect = sceneRect.adjusted(-30, -30, 30, 30)
        
        view_width = self.viewport().width()
        view_height = self.viewport().height()
        
        if view_width <= 0 or view_height <= 0:
            return
            
        scale_x = view_width / padded_rect.width()
        scale_y = view_height / padded_rect.height()
        
        fitting_scale = min(scale_x, scale_y)
        
        self.contentFittingZoom = max(0.01, fitting_scale * 0.9)

def create_sample_scene():
    """Create a sample scene with editable items"""
    scene = CheckerboardGraphicsScene()
    
    rect_item = QGraphicsRectItem(0, 0, 100, 60)
    rect_item.setBrush(QBrush(QColor(255, 100, 100)))
    rect_item.setPos(50, 50)
    scene.addItem(rect_item)
    
    ellipse_item = QGraphicsEllipseItem(0, 0, 80, 80)
    ellipse_item.setBrush(QBrush(QColor(100, 255, 100)))
    ellipse_item.setPos(200, 100)
    scene.addItem(ellipse_item)
    
    scene.makeItemEditable(rect_item)
    scene.makeItemEditable(ellipse_item)
    
    return scene