import pygame
import sys
import asyncio


class Colors:
    """Colors namespace"""

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    DARKRED = (70, 0, 0)
    YELLOW = (255, 255, 0)
    WEIRD = (0, 255, 255)
    GREY = (70, 70, 70)


class UIField:
    """Class handling user interface objects"""

    def __init__(self, text, center, z=5, big=False):
        self.big = big
        self.z = z
        self.center = center
        self.text = text
        if big:
            self.box = Game.FontBIG.render(text, True, Colors.RED)
        else:
            self.box = Game.Font.render(text, True, Colors.WHITE)
        self.rect = self.box.get_rect()
        self.rect.center = center

    def draw(self, scr):
        scr.blit(self.box, self.rect)

    def updateText(self, text):
        if self.big:
            self.box = Game.FontBIG.render(text, True, Colors.RED)
        else:
            self.box = Game.Font.render(text, True, Colors.WHITE)
        self.rect = self.box.get_rect()
        self.rect.center = self.center


class ButtonActions:
    """
    class containing actions that happen
    after pressing a button
    """

    @staticmethod
    def OnPlay(ui, game):
        """prepare game"""
        ui.createGameUI()
        game.createBackground("images/background.png")
        game.instantiateRaft()
        game.instantiateCandM()

    @staticmethod
    def doNothing(ui, game):
        """does nothing"""
        pass

    @staticmethod
    def OnExit(ui, game):
        sys.exit()

    @staticmethod
    def startAgain(ui, game):
        """resets the game to the beginning"""
        Game.gameObjects = []
        Game.cannibals = []
        Game.missionaries = []
        Game.asyncTasks = []
        UI.objs = []
        global graphstate
        graphstate = "-cccmmmb"
        game.dimSur = None
        ui.createMenu()


class Button(UIField):
    """Button - interactive ui object - child of UIField"""

    def __init__(self, text, center, onClick=None, z=5):
        self.big = False
        self.center = center
        self.text = text
        self.z = z
        self.box = Game.Font.render(text, True, Colors.WHITE)
        self.rect = self.box.get_rect()
        self.rect.center = center
        self.onClick = onClick if onClick != None else ButtonActions.doNothing

    def onHover(self):
        """called when mouse is pointing the button"""
        self.box = Game.Font.render(self.text, True, Colors.RED)
        self.rect = self.box.get_rect()
        self.rect.center = self.center

    def unHover(self):
        """called when mouse is no longer pointing the button"""
        self.box = Game.Font.render(self.text, True, Colors.WHITE)
        self.rect = self.box.get_rect()
        self.rect.center = self.center


class GameObject:
    def __init__(self, imgPath):
        self.img = pygame.image.load(imgPath)
        self.img = self.img.convert()
        self.rect = self.img.get_rect()
        self.animTick = 0
        self.state = "idle"
        self.animCounter = 0

    def lerp(self, startPos, endPos, t):
        """linear interpolation method"""
        valuex = endPos[0] * t + (1 - t) * startPos[0]
        valuey = endPos[1] * t + (1 - t) * startPos[1]
        w = self.rect.width
        h = self.rect.height
        self.rect = pygame.Rect(valuex - w / 2, valuey - h / 2, w, h)

    def moveToAsync(self, args):
        """gets called multiple of times asynchronously"""
        # args = (startPos,endPos,startTime,time)
        startPos = args["startPos"]
        endPos = args["endPos"]
        startTime = args["startTime"]
        time = args["duration"]
        self.state = "move"
        curTime = (pygame.time.get_ticks() - startTime) / (1000 * time)
        self.lerp(startPos, endPos, curTime)
        # when its finished
        if curTime >= 1:
            for task in Game.asyncTasks:
                if task["args"] == args:
                    self.state = "idle"
                    self.animTick = 0
                    self.animCounter = 0
                    Game.asyncTasks.remove(task)

    def moveTo(self, endPos, time):
        """starts asynchornous call"""
        Game.asyncTasks.append(
            {
                "obj": self,
                "func": "moveToAsync",
                "args": {
                    "startPos": self.rect.center,
                    "endPos": endPos,
                    "startTime": pygame.time.get_ticks(),
                    "duration": time,
                },
            }
        )


class Raft(GameObject):
    """Handles the raft object"""

    def __init__(self):
        self.img = pygame.image.load("images/raft.png")
        self.img = self.img.convert_alpha()
        self.rect = self.img.get_rect()
        self.pos = {"right": (830, 650), "left": (430, 650)}
        self.rect.center = (830, 650)
        Raft.slot1 = {
            "person": None,
            "pos": (self.rect.left + 50, self.rect.bottom - 150),
        }
        Raft.slot2 = {
            "person": None,
            "pos": (self.rect.right - 50, self.rect.bottom - 150),
        }
        self.animTick = 0
        Raft.state = "idle"
        Raft.side = "right"
        self.otherside = "left"
        self.animCounter = 0

    def moveBoat(self, args):
        """asynchornous method, moves the boat"""
        Raft.state = "move"

        startPos = self.pos[Raft.side]
        endPos = self.pos[self.otherside]
        startTime = args["startTime"]
        time = args["duration"]
        curTime = (pygame.time.get_ticks() - startTime) / (1000 * time)
        self.lerp(startPos, endPos, curTime)

        a = Raft.slot1["person"]
        b = Raft.slot2["person"]

        if a != None:
            a.rect.center = (self.rect.left + 50, self.rect.bottom - 150)
        if b != None:
            b.rect.center = (self.rect.right - 50, self.rect.bottom - 150)
        # when it's finished
        if curTime >= 1:
            for task in Game.asyncTasks:
                if task["args"] == args:
                    Raft.state = "idle"
                    temp = Raft.side
                    Raft.side = self.otherside
                    self.otherside = temp
                    if a != None:
                        a.side = Raft.side
                    Raft.slot1["pos"] = (self.rect.left + 50, self.rect.bottom - 150)
                    if b != None:
                        b.side = Raft.side
                    Raft.slot2["pos"] = (self.rect.right - 50, self.rect.bottom - 150)
                    global graphstate
                    if isinstance(a, Cannibal) and b is None:
                        graphstate = gameGraph[graphstate]["c"]
                    elif isinstance(b, Cannibal) and a is None:
                        graphstate = gameGraph[graphstate]["c"]
                    elif isinstance(a, Cannibal) and isinstance(b, Cannibal):
                        graphstate = gameGraph[graphstate]["2c"]
                    elif isinstance(a, Missionary) and b is None:
                        graphstate = gameGraph[graphstate]["m"]
                    elif isinstance(b, Missionary) and a is None:
                        graphstate = gameGraph[graphstate]["m"]
                    elif isinstance(a, Missionary) and isinstance(b, Missionary):
                        graphstate = gameGraph[graphstate]["2m"]
                    elif isinstance(a, Cannibal) and isinstance(b, Missionary):
                        graphstate = gameGraph[graphstate]["cm"]
                    elif isinstance(a, Missionary) and isinstance(b, Cannibal):
                        graphstate = gameGraph[graphstate]["cm"]

                    Game.asyncTasks.remove(task)

    def anim(self):
        """animates the boat"""
        if self.state == "idle" or self.state == "move":
            self.img = pygame.image.load("images/raft.png")
            self.img = self.img.convert_alpha()
        if self.state == "hovered":
            self.img = pygame.image.load("images/rhovered.png")
            self.img = self.img.convert_alpha()
            Raft.state = "idle"

    def onClick(self):
        """gets called when boat is clicked and handles click"""
        self.img = pygame.image.load("images/raft.png")
        self.img = self.img.convert_alpha()
        c1 = Raft.slot1["person"]
        c2 = Raft.slot2["person"]
        if (
            (c1 != None and c1.state == "idle" and c2 is None and self.state == "idle")
            or (
                c2 != None
                and c2.state == "idle"
                and c1 is None
                and self.state == "idle"
            )
            or (
                c1 != None
                and c2 != None
                and c1.state == c2.state == self.state == "idle"
            )
        ):
            Game.asyncTasks.append(
                {
                    "obj": self,
                    "func": "moveBoat",
                    "args": {"startTime": pygame.time.get_ticks(), "duration": 3},
                }
            )

    def onHover(self):
        """changes raft's state to hovoered"""
        if Raft.state == "idle":
            Raft.state = "hovered"


class Cannibal(GameObject):
    """class Handling cannibals"""

    def __init__(self, slot):
        self.imgpath = "images/idle0"
        self.img = pygame.image.load(self.imgpath + ".png")
        self.animTick = 0
        self.state = "idle"
        self.side = "right"
        self.slot = slot
        self.pos = {
            "right": (1050 + 70 * slot, 350 + 115 * slot),
            "left": (180 - 50 * slot, 400 + 100 * slot),
        }
        self.animCounter = 0
        self.idleSheet = tuple(
            pygame.image.load("images/" + "idle" + str(i) + ".png") for i in range(2)
        )
        self.moveSheet = tuple(
            pygame.image.load("images/" + "move" + str(i) + ".png") for i in range(2)
        )
        self.rect = self.img.get_rect()
        self.rect.center = self.pos["right"]

    def anim(self):
        """animates cannibal"""
        if self.state == "idle":
            if self.animTick % Game.frameRate == 0:
                self.img = self.idleSheet[self.animCounter % len(self.idleSheet)]
                self.img = self.img.convert_alpha()
                self.animCounter += 1
        if self.state == "move":
            if self.animTick % (Game.frameRate / 8) == 0:
                self.img = self.moveSheet[self.animCounter % len(self.moveSheet)]
                self.img = self.img.convert_alpha()
                self.animCounter += 1
        if self.state == "hovered":
            self.img = pygame.image.load("images/hovered.png")
            self.img = self.img.convert_alpha()
            self.state = "idle"
            self.animTick = -1
            self.animCounter = 0
        self.animTick += 1

    def onClick(self):
        if self.state == "idle" and Raft.state == "idle":
            if Raft.slot1["person"] == self:
                Raft.slot1["person"] = None
                self.moveTo(self.pos[self.side], 1)
            elif Raft.slot2["person"] == self:
                Raft.slot2["person"] = None
                self.moveTo(self.pos[self.side], 1)
            elif Raft.slot1["person"] is None and self.side == Raft.side:
                self.moveTo(Raft.slot1["pos"], 1)
                Raft.slot1["person"] = self
            elif Raft.slot2["person"] is None and self.side == Raft.side:
                self.moveTo(Raft.slot2["pos"], 1)
                Raft.slot2["person"] = self

    def onHover(self):
        if self.state == "idle" and Raft.state == "idle":
            self.state = "hovered"


class Missionary(GameObject):
    """handles missionaries"""

    def __init__(self, slot):
        self.imgpath = "images/midle0"
        self.img = pygame.image.load(self.imgpath + ".png")
        self.animTick = 0
        self.state = "idle"
        self.side = "right"
        self.slot = slot
        self.pos = {
            "right": (900 + 50 * slot, 375 + 115 * slot),
            "left": (330 - 50 * slot, 425 + 100 * slot),
        }
        self.animCounter = 0
        self.idleSheet = tuple(
            pygame.image.load("images/" + "midle" + str(i) + ".png") for i in range(2)
        )
        self.moveSheet = tuple(
            pygame.image.load("images/" + "mmove" + str(i) + ".png") for i in range(2)
        )
        self.rect = self.img.get_rect()
        self.rect.center = self.pos["right"]

    def anim(self):
        if self.state == "idle":
            if self.animTick % Game.frameRate == 0:
                self.img = self.idleSheet[self.animCounter % len(self.idleSheet)]
                self.img = self.img.convert_alpha()
                self.animCounter += 1
        if self.state == "move":
            if self.animTick % (Game.frameRate / 8) == 0:
                self.img = self.moveSheet[self.animCounter % len(self.moveSheet)]
                self.img = self.img.convert_alpha()
                self.animCounter += 1
        if self.state == "hovered":
            self.img = pygame.image.load("images/mhovered.png")
            self.img = self.img.convert_alpha()
            self.state = "idle"
            self.animTick = -1
            self.animCounter = 0
        self.animTick += 1

    def onClick(self):
        if self.state == "idle" and Raft.state == "idle":
            if Raft.slot1["person"] == self:
                Raft.slot1["person"] = None
                self.moveTo(self.pos[self.side], 1)
            elif Raft.slot2["person"] == self:
                Raft.slot2["person"] = None
                self.moveTo(self.pos[self.side], 1)
            elif Raft.slot1["person"] is None and self.side == Raft.side:
                self.moveTo(Raft.slot1["pos"], 1)
                Raft.slot1["person"] = self
            elif Raft.slot2["person"] is None and self.side == Raft.side:
                self.moveTo(Raft.slot2["pos"], 1)
                Raft.slot2["person"] = self

    def onHover(self):
        if self.state == "idle" and Raft.state == "idle":
            self.state = "hovered"


class Game:
    """Handles various game related events"""

    def __init__(self, res):
        pygame.init()
        Game.gameObjects = []
        Game.cannibals = []
        Game.missionaries = []
        Game.asyncTasks = []
        Game.FontBIG = pygame.font.Font("fonts/font.ttf", 120)
        Game.Font = pygame.font.Font("fonts/font.ttf", 40)
        Game.raft = None
        self.dimSur = None
        self.scr = pygame.display.set_mode(res)
        self.fps = pygame.time.Clock()
        Game.frameRate = 120

    def createBackground(self, path):
        backGnd = GameObject(path)
        backGnd.rect = pygame.Rect(0, 0, backGnd.rect.width, backGnd.rect.height)
        Game.gameObjects.append(backGnd)
        self.backGnd = backGnd

    def instantiateCandM(self):
        """
        Instantiates 3 cannibals
        and 3 missionaries
        """
        m1 = Missionary(0)
        Game.gameObjects.append(m1)
        Game.missionaries.append(m1)
        can1 = Cannibal(0)
        Game.gameObjects.append(can1)
        Game.cannibals.append(can1)
        m2 = Missionary(1)
        Game.gameObjects.append(m2)
        Game.missionaries.append(m2)
        can2 = Cannibal(1)
        Game.gameObjects.append(can2)
        Game.cannibals.append(can2)
        can3 = Cannibal(2)
        Game.gameObjects.append(can3)
        Game.cannibals.append(can3)
        m3 = Missionary(2)
        Game.gameObjects.append(m3)
        Game.missionaries.append(m3)

    def instantiateRaft(self):
        raft = Raft()
        Game.gameObjects.append(raft)
        Game.raft = raft

    def update(self):
        """animates and draws every gameObject"""
        if self.raft != None:
            self.raft.anim()
        for can in Game.cannibals:
            can.anim()
        for m in Game.missionaries:
            m.anim()
        for obj in Game.gameObjects:
            self.scr.blit(obj.img, obj.rect)
        if self.dimSur != None:
            self.scr.blit(self.dimSur, (0, 0))
        self.fps.tick(Game.frameRate)

    def dimScreen(self, time):
        """
        gets called when player lost
        and dims the screen
        """
        sur = pygame.Surface((1280, 720))
        Game.asyncTasks.append(
            {
                "obj": self,
                "func": "dim",
                "args": {
                    "sur": sur,
                    "startAlpha": 255,
                    "endAlpha": 0,
                    "startTime": pygame.time.get_ticks(),
                    "duration": time,
                },
            }
        )

    def dim(self, args):
        """asynchronous dim"""
        # args = (startPos,endPos,startTime,time)
        sur = args["sur"]
        startAlpha = args["startAlpha"]
        endAlpha = args["endAlpha"]
        startTime = args["startTime"]
        time = args["duration"]
        t = (pygame.time.get_ticks() - startTime) / (1000 * time)

        alpha = startAlpha * t + (1 - t) * endAlpha
        self.dimSur = sur
        self.dimSur.set_alpha(alpha)
        self.dimSur.fill((0, 0, 0))

        if t >= 1:
            for task in Game.asyncTasks:
                if task["args"] == args:
                    UI.drawEnd()
                    Game.asyncTasks.remove(task)

    def onLoss(self):
        """handles loss event"""
        self.dimScreen(3)
        left = 0
        right = 0
        for can in self.cannibals:
            if can.side == "left":
                left += 1
            else:
                right += 1
        if left > right:
            side = "left"
        else:
            side = "right"
        if side == "right":
            for can in self.cannibals:
                if can.side == side:
                    can.moveTo((950, 490), 10)
            for m in self.missionaries:
                if m.side == side:
                    m.moveTo((950 + 15 * m.slot, 490 + 15 * m.slot), 1)
        if side == "left":
            for can in self.cannibals:
                if can.side == side:
                    can.moveTo((280, 490), 10)
            for m in self.missionaries:
                if m.side == side:
                    m.moveTo((280 - 15 * m.slot, 490 + 15 * m.slot), 1)


class UI:
    """class handling User Interface"""

    def __init__(self, scr):
        UI.objs = []
        self.scr = scr
        self.center = scr.get_rect().center

    def addObject(self, obj):
        UI.objs.append(obj)

    def drawUI(self):
        for obj in UI.objs:
            obj.draw(self.scr)

    def createMenu(self):
        x = self.center[0]
        y = self.center[1]
        UI.objs = []
        self.addObject(UIField("Missionaries and", (x, y - 200), big=True))
        self.addObject(UIField("Cannibals", (x, y - 75), big=True))
        self.addObject(Button("Play", (x, y + 150), ButtonActions.OnPlay))
        self.addObject(Button("Exit", (x, y + 225), ButtonActions.OnExit))

    @staticmethod
    def drawEnd():
        UI.objs = []
        UI.objs.append((UIField("YOU LOST", (640, 360), big=True)))
        UI.drawAgain()

    @staticmethod
    def drawWin():
        UI.objs.append((UIField("YOU WON", (640, 360), big=True)))
        UI.drawAgain()

    def createGameUI(self):
        UI.objs = []

    @staticmethod
    def drawAgain():
        """draws again button after 2 seconds"""
        Game.asyncTasks.append(
            {"obj": UI, "func": "drawAgainAsync", "args": pygame.time.get_ticks()}
        )

    @staticmethod
    def drawAgainAsync(sTime):
        if (pygame.time.get_ticks() - sTime) > 2000:
            UI.objs.append(Button("Again?", (640, 560), ButtonActions.startAgain))
            for task in Game.asyncTasks:
                if task["args"] == sTime:
                    Game.asyncTasks.remove(task)


class MouseClass:
    """class handling clicks and hovers"""

    @staticmethod
    def GetObjClicked(mousePos):
        clicked = []
        clickedObj = None
        one = None
        for obj in UI.objs:
            if isinstance(obj, Button) and obj.rect.collidepoint(mousePos):
                clicked.append(obj)
        if gameGraph[graphstate] != "WIN":
            if Game.raft != None and Game.raft.rect.collidepoint(mousePos):
                clickedObj = Game.raft
            for i in range(len(Game.cannibals)):
                if Game.missionaries[i].rect.collidepoint(mousePos):
                    clickedObj = Game.missionaries[i]
                if Game.cannibals[i].rect.collidepoint(mousePos):
                    clickedObj = Game.cannibals[i]
            if clickedObj != None:
                clickedObj.onClick()
                return None
        if len(clicked) != 0:
            one = clicked[0]
            for obj in clicked:
                if obj.z > one.z:
                    one = obj
        return one

    @staticmethod
    def GetObjHovered(mousePos):
        hovered = None
        for obj in UI.objs:
            if isinstance(obj, Button):
                obj.unHover()
        for obj in UI.objs:
            if isinstance(obj, Button) and obj.rect.collidepoint(mousePos):
                hovered = obj

        if Game.raft != None and Game.raft.rect.collidepoint(mousePos):
            hovered = Game.raft
        for i in range(len(Game.cannibals)):
            if Game.missionaries[i].rect.collidepoint(mousePos):
                hovered = Game.missionaries[i]
            if Game.cannibals[i].rect.collidepoint(mousePos):
                hovered = Game.cannibals[i]
        if hovered != None:
            hovered.onHover()


def handleInput(ui, game):
    """initializes used buttons"""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            mPos = pygame.mouse.get_pos()
            temp = MouseClass.GetObjClicked(mPos)
            if temp != None:
                temp.onClick(ui, game)
    MouseClass.GetObjHovered(pygame.mouse.get_pos())


def handleAsync():
    """iterates over ongoing asynchronous calls"""
    for task in Game.asyncTasks:
        func = getattr(task["obj"], task["func"])
        func(task["args"])


async def main():
    """sets up Game object, contains main loop"""
    game = Game((1280, 720))
    ui = UI(game.scr)
    ui.createMenu()

    # main loop
    while True:
        handleAsync()
        global graphstate
        if gameGraph[graphstate] == "FAILURE":
            game.onLoss()
            graphstate = "-cccmmmb"
        if gameGraph[graphstate] == "WIN":
            UI.drawWin()
        game.scr.fill(Colors.BLACK)
        handleInput(ui, game)
        game.update()
        ui.drawUI()
        pygame.display.flip()
        await asyncio.sleep(0)


# current state of gamegraph
graphstate = "-cccmmmb"

FAILURE = "FAILURE"
WIN = "WIN"
# logic graph of the game
gameGraph = {
    "-cccmmmb": {
        "c": "bc-ccmmm",
        "m": "bm-cccmm",
        "2c": "bcc-cmmm",
        "2m": "bmm-cccm",
        "cm": "bcm-ccmm",
    },
    "m-cccmmb": FAILURE,
    "mm-cccmb": FAILURE,
    "mmm-cccb": {"c": "bcmmm-cc", "2c": "bccmmm-c"},
    "c-ccmmmb": {
        "c": "bcc-cmmm",
        "2c": "bccc-mmm",
        "m": "bcm-ccmm",
        "2m": "bcmm-ccm",
        "cm": "bccm-cmm",
    },
    "cc-cmmmb": {"c": "bccc-mmm", "m": "bccm-cmm", "2m": "bccmm-cm", "cm": "bcccm-mm"},
    "ccc-mmmb": {"m": "bcccm-mm", "2m": "bcccmm-m"},
    "cm-ccmmb": {
        "c": "bccm-cmm",
        "m": "bcmm-ccm",
        "2c": "bcccm-mm",
        "2m": "bcmmm-cc",
        "cm": "bccmm-cm",
    },
    "ccm-cmmb": FAILURE,
    "cccm-mmb": FAILURE,
    "cmm-ccmb": FAILURE,
    "ccmm-cmb": {"c": "bcccmm-m", "m": "bccmmm-c", "cm": "bcccmmm-"},
    "cccmm-mb": FAILURE,
    "cmmm-ccb": {"c": "bccmmm-c", "2c": "bcccmmm-"},
    "ccmmm-cb": {"c": "bcccmmm-"},
    "bm-cccmm": FAILURE,
    "bmm-cccm": FAILURE,
    "bmmm-ccc": {"m": "mm-cccmb", "2m": "m-cccmmb"},
    "bc-ccmmm": {"c": "-cccmmmb"},
    "bcc-cmmm": {"c": "c-ccmmmb", "2c": "-cccmmmb"},
    "bccc-mmm": {"c": "cc-cmmmb", "2c": "c-ccmmmb"},
    "bcm-ccmm": {"c": "m-cccmmb", "m": "c-ccmmmb", "cm": "-cccmmmb"},
    "bccm-cmm": FAILURE,
    "bcccm-mm": FAILURE,
    "bcmm-ccm": FAILURE,
    "bccmm-cm": {
        "c": "cmm-ccmb",
        "m": "ccm-cmmb",
        "2c": "mm-cccmb",
        "2m": "cc-cmmmb",
        "cm": "cm-ccmmb",
    },
    "bcccmm-m": FAILURE,
    "bcmmm-cc": {"c": "mmm-cccb", "m": "cmm-ccmb", "2m": "cm-ccmmb", "cm": "mm-cccmb"},
    "bccmmm-c": {
        "c": "cmmm-ccb",
        "m": "ccbb-cmb",
        "2c": "mmm-cccb",
        "2m": "ccm-cmmb",
        "cm": "cmm-ccmb",
    },
    "bcccmmm-": WIN,
}
# makes sure that module won't run when imported by another module
if __name__ == "__main__":
    asyncio.run(main())
