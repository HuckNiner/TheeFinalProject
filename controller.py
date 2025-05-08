from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import aspect2d, globalClock
from direct.task import Task
import sys
from panda3d.core import (
    CollisionNode, GeomNode, CollisionRay, CollisionHandlerQueue, CollisionTraverser,
    WindowProperties, TextNode, BitMask32
)
from pubsub import pub

from game_logic import GameLogic
from player_view import PlayerView
from game_object import DoorObject

controls = {
    'w': 'forward',
    'a': 'left',
    's': 'backward',
    'd': 'right',
    'w-repeat': 'forward',
    'a-repeat': 'left',
    's-repeat': 'backward',
    'd-repeat': 'right',
    'q': 'toggleTexture',
    'escape': 'toggleMouseMove',
    'f': 'toggleDoor',
    'e': 'interact',
    'l': 'toggleLight'  # Moved light toggle to L
}

class Main(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.disableMouse()
        self.render.setShaderAuto()

        self.input_events = {}
        self.CursorOffOn = 'Off'
        self.SpeedRot = 0.05
        self.props = WindowProperties()
        self.props.setCursorHidden(True)
        self.win.requestProperties(self.props)

        self.game_logic = GameLogic()
        self.player_view = PlayerView(self.game_logic)

        self.cTrav = CollisionTraverser()
        base.cTrav = self.cTrav

        # Mouse ray picker setup
        picker_node = CollisionNode('mouseRay')
        picker_node.setFromCollideMask(GeomNode.getDefaultCollideMask())
        picker_node.setIntoCollideMask(BitMask32.allOff())
        self.pickerRay = CollisionRay()
        picker_node.addSolid(self.pickerRay)
        picker_np = self.camera.attachNewNode(picker_node)
        self.rayQueue = CollisionHandlerQueue()
        self.cTrav.addCollider(picker_np, self.rayQueue)

        for key in controls:
            self.accept(key, self.input_event, [controls[key]])

        self.player = None
        self.won = False
        self.win_timer = 0

        # Timer setup
        self.time_left = 120  # seconds
        self.timer_text = TextNode('timer')
        self.timer_text.setAlign(TextNode.ACenter)
        self.timer_node = aspect2d.attachNewNode(self.timer_text)
        self.timer_node.setScale(0.08)
        self.timer_node.setPos(0, 0, 0.9)

    def go(self):
        pub.subscribe(self.new_player_object, 'create')
        self.game_logic.load_world()

        self.camera.set_pos(0, -20, 0)
        self.camera.look_at(0, 0, 0)
        self.taskMgr.add(self.tick)
        self.run()

    def new_player_object(self, game_object):
        if game_object.kind == "player":
            self.player = game_object

    def input_event(self, event):
        self.input_events[event] = True

        if event == 'toggleDoor':
            if self.game_logic.collected_keys >= self.game_logic.total_keys:
                picked_object = self.get_nearest_object()
                if picked_object and isinstance(picked_object.game_object, DoorObject):
                    pub.sendMessage('toggleDoor', events={'toggleDoor'})

        elif event == 'interact':
            picked = self.get_nearest_object()
            if picked and picked.game_object.kind == "key":
                picked.deleted()  # Remove cube safely
                del self.player_view.view_objects[picked.game_object.id]
                del self.game_logic.game_objects[picked.game_object.id]
                self.game_logic.collected_keys += 1

    def get_nearest_object(self):
        self.pickerRay.setFromLens(self.camNode, 0, 0)
        self.cTrav.traverse(self.render)
        if self.rayQueue.getNumEntries() > 0:
            self.rayQueue.sortEntries()
            entry = self.rayQueue.getEntry(0)
            picked_np = entry.getIntoNodePath().findNetTag('selectable')
            if not picked_np.isEmpty() and picked_np.getPythonTag("owner"):
                return picked_np.getPythonTag("owner")
        return None

    def tick(self, task):
        if not self.player:
            return Task.cont

        if 'toggleMouseMove' in self.input_events:
            self.CursorOffOn = 'On' if self.CursorOffOn == 'Off' else 'Off'
            self.props.setCursorHidden(self.CursorOffOn == 'Off')
            self.win.requestProperties(self.props)

        if self.input_events:
            pub.sendMessage('input', events=self.input_events)

        picked_object = self.get_nearest_object()
        if picked_object:
            picked_object.selected()

        if self.CursorOffOn == 'Off':
            md = self.win.getPointer(0)
            x, y = md.getX(), md.getY()
            if self.win.movePointer(0, self.win.getXSize() // 2, self.win.getYSize() // 2):
                self.player.z_rotation = self.camera.getH() - (x - self.win.getXSize() / 2) * self.SpeedRot
                self.player.x_rotation = self.camera.getP() - (y - self.win.getYSize() / 2) * self.SpeedRot
                self.player.x_rotation = max(min(self.player.x_rotation, 90), -90)

        self.camera.setHpr(self.player.z_rotation, self.player.x_rotation, self.player.y_rotation)
        self.camera.set_pos(*self.player.position)

        self.game_logic.tick()
        self.player_view.tick()
        self.update_timer()

        if not self.won:
            self.check_win_condition()
        else:
            self.win_timer += globalClock.getDt()
            if self.win_timer > 3:
                sys.exit()

        if self.game_logic.get_property("quit"):
            sys.exit()

        self.input_events.clear()
        return Task.cont

    def update_timer(self):
        dt = globalClock.getDt()
        self.time_left -= dt

        if self.time_left <= 0 and not self.won:
            self.time_left = 0
            self.show_game_over()
            self.won = True
            self.win_timer = 0

        minutes = int(self.time_left) // 60
        seconds = int(self.time_left) % 60
        self.timer_text.setText(f"{minutes:02}:{seconds:02}")

    def check_win_condition(self):
        if self.game_logic.collected_keys < self.game_logic.total_keys:
            return  # Not enough keys yet

        for obj in self.game_logic.game_objects.values():
            if isinstance(obj, DoorObject):
                px, py, _ = self.player.position
                dx, dy, _ = obj.position
                dist_sq = (px - dx) ** 2 + (py - dy) ** 2
                if dist_sq < 1.5:
                    self.show_win_message()
                    self.won = True

    def show_win_message(self):
        self.win_text = TextNode('win')
        self.win_text.setText("YOU ESCAPED!")
        self.win_text.setAlign(TextNode.ACenter)
        self.win_node = aspect2d.attachNewNode(self.win_text)
        self.win_node.setScale(0.2)
        self.win_node.setPos(0, 0, 0)

    def show_game_over(self):
        self.lose_text = TextNode('lose')
        self.lose_text.setText("GAME OVER")
        self.lose_text.setAlign(TextNode.ACenter)
        self.lose_node = aspect2d.attachNewNode(self.lose_text)
        self.lose_node.setScale(0.2)
        self.lose_node.setPos(0, 0, 0)

if __name__ == '__main__':
    main = Main()
    main.go()
