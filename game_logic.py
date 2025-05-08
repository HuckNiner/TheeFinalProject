from game_object import GameObject, DoorObject
from pubsub import pub
from player_object import PlayerObject

class GameLogic:
    def __init__(self):
        self.properties = {}
        self.game_objects = {}
        self.next_id = 0
        self.total_keys = 0
        self.collected_keys = 0

    def tick(self):
        for obj in self.game_objects.values():
            obj.tick()

    def create_object(self, position, kind):
        if kind == "player":
            obj = PlayerObject(position, kind, self.next_id, self)
        elif kind == "door":
            obj = DoorObject(position, kind, self.next_id)
        else:
            obj = GameObject(position, kind, self.next_id)

        self.next_id += 1
        self.game_objects[obj.id] = obj
        pub.sendMessage('create', game_object=obj)
        return obj

    def load_world(self):
        wall_coords = [
            (0, 0), (0, 2), (0, 4), (0, 6), (2, 6), (4, 6), (8, 6), (4, 4), (8, 4),
            (4, -2), (6, -2), (8, -2), (8, 2), (12, 2), (10, -2), (12, -2), (12, 0),
            (12, 4), (12, 6), (12, 8), (12, 10), (8, 10), (8, 8), (6, 10), (4, 10),
            (2, 10), (0, 10), (0, 8), (4, 0),
        ]
        for x, y in wall_coords:
            self.create_object([x, y, 0], "crate")

        self.create_object([0, -4, 1], "player")
        self.create_object([12, 6, 1], "door")

        self.total_keys = 3
        self.collected_keys = 0
        self.create_object([6, 4, 1], "key")
        self.create_object([2, 8, 1], "key")
        self.create_object([10, 0, 1], "key")

    def get_property(self, key):
        return self.properties.get(key, None)

    def set_property(self, key, value):
        self.properties[key] = value
