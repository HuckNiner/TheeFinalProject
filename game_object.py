class GameObject:
    def __init__(self, position, kind, id):
        self.position = position
        self.kind = kind
        self.id = id
        self.x_rotation = 0
        self.y_rotation = 0
        self.z_rotation = 0

    def tick(self):
        pass


class DoorObject(GameObject):
    def __init__(self, position, kind, id):
        super().__init__(position, kind, id)
        self.is_open = False
        self.original_position = position
        self.open_position = (position[0], position[1] + 1, position[2])

    def toggle_door(self):
        if self.is_open:
            self.position = self.original_position
        else:
            self.position = self.open_position

        self.is_open = not self.is_open
