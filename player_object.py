from panda3d.core import Quat, CollisionNode, CollisionSphere, BitMask32, CollisionHandlerQueue
from pubsub import pub
from game_object import GameObject

class PlayerObject(GameObject):
    def __init__(self, position, kind, id, game_logic):
        super().__init__(position, kind, id)
        self.game_logic = game_logic
        pub.subscribe(self.input_event, 'input')
        self.speed = 0.2

        c_node = CollisionNode(f"playerCollider-{id}")
        c_node.setFromCollideMask(BitMask32.bit(1))
        c_node.setIntoCollideMask(BitMask32.allOff())
        c_node.addSolid(CollisionSphere(0, 0, 0, 0.5))
        self.collider = base.render.attachNewNode(c_node)
        self.collider.setPos(*self.position)

        self.queue = CollisionHandlerQueue()
        base.cTrav.addCollider(self.collider, self.queue)

        # Key detector
        key_node = CollisionNode("playerKeyDetector")
        key_node.setFromCollideMask(BitMask32.bit(2))
        key_node.setIntoCollideMask(BitMask32.allOff())
        key_node.addSolid(CollisionSphere(0, 0, 0, 0.5))
        self.key_checker = base.render.attachNewNode(key_node)
        self.key_checker.setPos(*self.position)
        self.key_queue = CollisionHandlerQueue()
        base.cTrav.addCollider(self.key_checker, self.key_queue)

    def input_event(self, events=None):
        if events:
            q = Quat()
            q.setHpr((self.z_rotation, self.x_rotation, self.y_rotation))
            dx = dy = dz = 0

            if 'forward' in events:
                f = q.getForward()
                dx += f[0]; dy += f[1]; dz += f[2]
            if 'backward' in events:
                f = q.getForward()
                dx -= f[0]; dy -= f[1]; dz -= f[2]
            if 'left' in events:
                r = q.getRight()
                dx -= r[0]; dy -= r[1]; dz -= r[2]
            if 'right' in events:
                r = q.getRight()
                dx += r[0]; dy += r[1]; dz += r[2]

            if dx or dy or dz:
                new_pos = (
                    self.position[0] + dx * self.speed,
                    self.position[1] + dy * self.speed,
                    self.position[2] + dz * self.speed
                )

                self.collider.setPos(*new_pos)
                base.cTrav.traverse(base.render)
                self.queue.sortEntries()

                if self.queue.getNumEntries() == 0:
                    self.position = new_pos

                self.collider.setPos(*self.position)
                self.key_checker.setPos(*self.position)

                base.cTrav.traverse(base.render)
                self.key_queue.sortEntries()

                for entry in self.key_queue.getEntries():
                    into_node = entry.getIntoNode()
                    if into_node.getName() == "key":
                        parent = into_node.getParent()
                        if parent:
                            parent.removeNode()
                        self.game_logic.collected_keys += 1
