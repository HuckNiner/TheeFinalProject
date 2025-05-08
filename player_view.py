from direct.showbase.ShowBaseGlobal import aspect2d
from pubsub import pub
from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, TextNode
from view_object import ViewObject, DoorView, KeyView

class PlayerView:
    def __init__(self, game_logic):
        self.game_logic = game_logic
        self.view_objects = {}
        self.lights_on = True

        # Lighting
        self.ambient_light = AmbientLight("ambient")
        self.ambient_light.setColor((0.5, 0.5, 0.5, 1))
        self.ambient_np = base.render.attachNewNode(self.ambient_light)
        base.render.setLight(self.ambient_np)

        self.directional_light = DirectionalLight("directional")
        self.directional_light.setColor((0.8, 0.8, 0.8, 1))
        self.directional_np = base.render.attachNewNode(self.directional_light)
        self.directional_np.setHpr(0, -60, 0)
        base.render.setLight(self.directional_np)

        # Key Counter UI
        self.key_text = TextNode('keyUI')
        self.key_text.setAlign(TextNode.ALeft)
        self.key_text_node = aspect2d.attachNewNode(self.key_text)
        self.key_text_node.setScale(0.05)
        self.key_text_node.setPos(-1.3, 0, 0.9)

        pub.subscribe(self.toggle_light, 'input')
        pub.subscribe(self.new_game_object, 'create')

    def toggle_light(self, events=None):
        if 'toggleLight' in events:
            self.lights_on = not self.lights_on
            if self.lights_on:
                base.render.setLight(self.ambient_np)
                base.render.setLight(self.directional_np)
            else:
                base.render.clearLight(self.ambient_np)
                base.render.clearLight(self.directional_np)

    def new_game_object(self, game_object):
        if game_object.kind == "player":
            return

        if game_object.kind == "door":
            view = DoorView(game_object)
        elif game_object.kind == "key":
            view = KeyView(game_object)
        else:
            view = ViewObject(game_object)

        self.view_objects[game_object.id] = view

    def tick(self):
        for view in self.view_objects.values():
            view.tick()

        # Update key counter
        self.key_text.setText(
            f"Keys: {self.game_logic.collected_keys} / {self.game_logic.total_keys}"
        )
