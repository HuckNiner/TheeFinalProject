from panda3d.core import CollisionNode, CollisionBox, Point3, BitMask32
from pubsub import pub

class ViewObject:
    def __init__(self, game_object):
        self.game_object = game_object
        self.cube = base.loader.loadModel("models/cube")
        self.cube.reparentTo(base.render)

        self.cube.setTag('selectable', '')
        self.cube.setPythonTag("owner", self)
        self.cube.setPos(*game_object.position)
        self.cube.setScale(1, 1, 1)

        self.crate_texture = base.loader.loadTexture("textures/crate.png")
        self.metal_texture = base.loader.loadTexture("textures/metal.png")
        self.chrome_texture = base.loader.loadTexture("textures/chrome.png")

        self.cube.setTexture(self.crate_texture)

        if game_object.kind == "crate":
            c_node = CollisionNode("wall")
            c_node.setFromCollideMask(BitMask32.allOff())
            c_node.setIntoCollideMask(BitMask32.bit(1))
            c_box = CollisionBox(Point3(0, 0, 0), 0.5, 0.5, 0.5)
            c_node.addSolid(c_box)
            self.cube.attachNewNode(c_node)

        self.toggle_texture_pressed = False
        self.is_selected = False
        pub.subscribe(self.toggle_texture, 'input')

    def deleted(self):
        if self.cube:
            self.cube.removeNode()
            self.cube = None

    def selected(self):
        self.is_selected = True

    def toggle_texture(self, events=None):
        if 'toggleTexture' in events:
            self.toggle_texture_pressed = True

    def tick(self):
        if self.cube:
            h = self.game_object.z_rotation
            p = self.game_object.x_rotation
            r = self.game_object.y_rotation
            self.cube.setHpr(h, p, r)

        if self.toggle_texture_pressed and self.is_selected and self.cube:
            self.cube.setTexture(self.chrome_texture)
            self.toggle_texture_pressed = False


class DoorView(ViewObject):
    def __init__(self, game_object):
        super().__init__(game_object)
        self.cube.setScale(1, 0.2, 2)
        self.cube.setTexture(self.chrome_texture)
        pub.subscribe(self.toggle_door, 'toggleDoor')

    def toggle_door(self, events=None):
        if 'toggleDoor' in events and self.is_selected:
            self.game_object.toggle_door()
            self.cube.setPos(*self.game_object.position)


class KeyView(ViewObject):
    def __init__(self, game_object):
        super().__init__(game_object)
        self.cube.setScale(0.3, 0.3, 0.3)
        self.cube.setTexture(self.metal_texture)
        pos = self.cube.getPos()
        self.cube.setZ(pos.getZ() + 0.1)

        c_node = CollisionNode("key")
        c_node.setIntoCollideMask(BitMask32.bit(2))
        c_box = CollisionBox(Point3(0, 0, 0), 0.3, 0.3, 0.3)
        c_node.addSolid(c_box)
        self.cube.attachNewNode(c_node)

    def deleted(self):
        if self.cube:
            self.cube.removeNode()
            self.cube = None
