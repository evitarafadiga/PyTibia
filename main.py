import multiprocessing
import numpy as np
import pyautogui
from rx import interval, of, operators, pipe, timer
from rx.scheduler import ThreadPoolScheduler
from rx.subject import Subject
import time
import battleList.core
import battleList.typing
from chat import core
import gameplay.cavebot
import gameplay.decision
import gameplay.resolvers
import gameplay.typings
import gameplay.waypoint
import hud.creatures
import hud.core
import hud.slot
import radar.core
from radar.types import waypointType
from gameplay.taskExecutor import TaskExecutor
import utils.array
import utils.core
import utils.image
import eventlet
import socketio
import pygetwindow

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0


gameContext = {
    'backpacks': {
        'main': 'brocade backpack',
        'gold': 'beach backpack',
        'loot': 'fur backpack',
    },
    'battleListCreatures': np.array([], dtype=battleList.typing.creatureType),
    'beingAttackedCreature': None,
    'cavebot': {
        'running': True,
        'waypoints': {
            'currentIndex': None,
            'points': np.array([
                # mino dar
                # ('walk', (33215, 32456, 8), 0, {}),
                # ('moveUpNorth', (33215, 32456, 8), 0, {}),
                # ('walk', (33215, 32412, 7), 0, {}),
                # ('walk', (33235, 32381, 7), 0, {}),
                # ('walk', (33277, 32345, 7), 0, {}),
                # ('walk', (33289, 32309, 7), 0, {}),
                # ('walk', (33300, 32294, 7), 0, {}),
                # ('walk', (33307, 32278, 7), 0, {}),
                # ('walk', (33320, 32282, 7), 0, {}),
                # ('walk', (33308, 32289, 7), 0, {}),
                # ('refillChecker', (33308, 32289, 7), 0, {
                #     'minimumOfManaPotions': 1,
                #     'minimumOfHealthPotions': 1,
                #     'minimumOfCapacity': 200,
                #     'successIndex': 5,
                # }),
                
                # lava ank
                # ('walk', (33127, 32830, 7), 0, {}),
                # ('walk', (33126, 32834, 7), 0, {}),
                # ('depositItems', (33126, 32841, 7), 0, {}),
                ('walk', (33125, 32833, 7), 0, {}),
                ('walk', (33114, 32830, 7), 0, {}),
                ('walk', (33098, 32830, 7), 0, {}),
                ('walk', (33098, 32793, 7), 0, {}),
                ('walk', (33088, 32788, 7), 0, {}),
                ('moveUpNorth', (33088, 32788, 7), 0, {}),
                ('walk', (33088, 32785, 6), 0, {}),
                ('moveDownNorth', (33088, 32785, 6), 0, {}),
                ('walk', (33073, 32760, 7), 0, {}),
                ('useShovel', (33072, 32760, 7), 0, {}),
                ('walk', (33095, 32761, 8), 0, {}),
                ('walk', (33084, 32770, 8), 0, {}),
                ('walk', (33062, 32762, 8), 0, {}),
                ('walk', (33072, 32760, 8), 0, {}),
                ('walk', (33076, 32757, 8), 0, {}),
                ('walk', (33072, 32759, 8), 0, {}),
                ('refillChecker', (33072, 32760, 8), 0, {
                    'minimumOfManaPotions': 1,
                    'minimumOfHealthPotions': 1,
                    'minimumOfCapacity': 200,
                    'successIndex': 10,
                }),
                # ('walk', (33072, 32760, 8), 0, {}),
                # ('useRope', (33072, 32760, 8), 0, {}),
                # ('walk', (33088, 32783, 7), 0, {}),
                # ('moveUpSouth', (33088, 32783, 7), 0, {}),
                # ('walk', (33088, 32786, 6), 0, {}),
                # ('moveDownSouth', (33088, 32786, 6), 0, {}),
                # ('walk', (33098, 32793, 7), 0, {}),
                # ('walk', (33099, 32830, 7), 0, {}),
                # ('walk', (33125, 32833, 7), 0, {}),
                # ('walk', (33126, 32834, 7), 0, {}),
                # ('depositItems', (33126, 32834, 7), 0, {}),
                # ('refillChecker', (33127, 32834, 7), 0, {}),
                # ('walk', (33128, 32827, 7), 0, {}),
                # ('moveUpNorth', (33128, 32827, 7), 0, {}),
                # ('walk', (33130, 32817, 6), 0, {}),
                # ('moveUpNorth', (33130, 32817, 6), 0, {}),
                # ('walk', (33128, 32811, 5), 0, {}),
                # ('refill', (33128, 32810, 5), 0, {}),
                # ('walk', (33130, 32815, 5), 0, {}),
                # ('moveDownSouth', (33130, 32815, 5), 0, {}),
                # ('walk', (33124, 32814, 6), 0, {}),
                # ('moveDownWest', (33124, 32814, 6), 0, {}),
            ], dtype=waypointType),
            'state': None
        },
    },
    'comingFromDirection': None,
    'corpsesToLoot': np.array([], dtype=hud.creatures.creatureType),
    'currentGroupTask': None,
    'hotkeys': {
        'healthPotion': 'f1',
        'manaPotion': 'f2',
        'rope': 'f8',
        'shovel': 'f9',
    },
    'hud': {
        'coordinate': None,
        'img': None,
    },
    'lastCoordinateVisited': None,
    'lastPressedKey': None,
    'lastWay': 'waypoint',
    'monsters': np.array([], dtype=hud.creatures.creatureType),
    'players': np.array([], dtype=hud.creatures.creatureType),
    'previousCoordinate': None,
    'coordinate': None,
    'refill': {
        'health': {
            'item': 'health potion',
            'quantity': 140,
        },
        'mana': {
            'item': 'mana potion',
            'quantity': 30,
        },
    },
    'resolution': 1080,
    'targetCreature': None,
    'screenshot': None,
    'way': None,
    'window': None
}
hudCreatures = np.array([], dtype=hud.creatures.creatureType)
taskExecutor = TaskExecutor()


def main():
    sio = socketio.Server()
    app = socketio.WSGIApp(sio)

    def getGameContextForSocket(context):
        waypoints = [[[int(waypoint['coordinate'][0]), int(waypoint['coordinate'][1]), int(waypoint['coordinate'][2])], int(waypoint['tolerance']), waypoint['options']]
                     for waypoint in context['cavebot']['waypoints']['points']]
        return {
            'backpacks': context['backpacks'],
            'cavebot': {
                'waypoints': waypoints,
            },
            'hotkeys': context['hotkeys'],
            'refill': context['refill'],
            'window': context['window'],
        }

    @sio.event
    def connect(sid, environ):
        print('connect ', sid)

    @sio.on('getContext')
    def getContext(data):
        global gameContext
        return None, getGameContextForSocket(gameContext)

    @sio.on('getWindows')
    def getWindows(_):
        windowsTitles = pygetwindow.getAllTitles()
        nonEmptyWindowsTitles = [windowTitle for windowTitle in windowsTitles if windowTitle != '']
        return None, nonEmptyWindowsTitles

    @sio.on('setContext')
    def handleSetContext(_, data):
        global gameContext
        gameContext['backpacks'] = data['backpacks']
        gameContext['hotkeys'] = data['hotkeys']
        gameContext['refill'] = data['refill']
        gameContext['window'] = data['window']
        return None, getGameContextForSocket(gameContext)

    @sio.on('setHotkey')
    def setHotkey(_, data):
        global gameContext
        gameContext['hotkeys'][data['action']] = data['hotkey']
        return None, getGameContextForSocket(gameContext)

    @sio.on('setRefillItem')
    def setRefillItem(_, data):
        global gameContext
        potionType = data['type']
        gameContext['refill'][potionType]['item'] = data['item']
        gameContext['refill'][potionType]['quantity'] = data['quantity']
        return None, getGameContextForSocket(gameContext)

    @sio.event
    def disconnect(sid):
        print('disconnect ', sid)

    # optimal_thread_count = multiprocessing.cpu_count()
    # threadPoolScheduler = ThreadPoolScheduler(optimal_thread_count)
    thirteenFps = 0.00833333333
    fpsObserver = interval(thirteenFps)

    def handleScreenshot(_):
        global gameContext
        screenshot = utils.image.RGBtoGray(utils.core.getScreenshot())
        gameContext['screenshot'] = screenshot
        return gameContext

    fpsWithScreenshot = fpsObserver.pipe(
        operators.map(handleScreenshot),
    )

    def handleCoordinate(context):
        global gameContext
        context['coordinate'] = radar.core.getCoordinate(
            context['screenshot'], previousCoordinate=context['previousCoordinate'])
        print(context['coordinate'])
        context['previousCoordinate'] = context['coordinate']
        gameContext = context
        return context

    coordinatesObserver = fpsWithScreenshot.pipe(
        operators.filter(lambda result: result['screenshot'] is not None),
        operators.filter(
            lambda result: gameContext['cavebot']['running'] == True),
        operators.map(handleCoordinate)
    )

    def handleBattleListCreatures(context):
        global gameContext
        copyOfContext = context.copy()
        copyOfContext['battleListCreatures'] = battleList.core.getCreatures(
            copyOfContext['screenshot'])
        gameContext = copyOfContext
        return copyOfContext

    battleListObserver = coordinatesObserver.pipe(
        operators.map(handleBattleListCreatures)
    )

    def handleHudCoordinate(context):
        global gameContext
        copyOfContext = context.copy()
        hudSize = hud.core.hudSizes[copyOfContext['resolution']]
        copyOfContext['hud']['coordinate'] = hud.core.getCoordinate(
            copyOfContext['screenshot'], hudSize)
        gameContext = copyOfContext
        return copyOfContext

    hudCoordinateObserver = battleListObserver.pipe(
        operators.filter(lambda result: result['coordinate'] is not None),
        operators.map(handleHudCoordinate)
    )

    def handleHudImg(context):
        global gameContext
        copyOfContext = context.copy()
        hudSize = hud.core.hudSizes[copyOfContext['resolution']]
        copyOfContext['hudImg'] = hud.core.getImgByCoordinate(
            copyOfContext['screenshot'], copyOfContext['hud']['coordinate'], hudSize)
        gameContext = copyOfContext
        return copyOfContext

    hudImgObserver = hudCoordinateObserver.pipe(
        operators.map(handleHudImg)
    )

    def resolveDirection(context):
        global gameContext
        copyOfContext = context.copy()
        comingFromDirection = None
        if copyOfContext['previousCoordinate'] is None:
            copyOfContext['previousCoordinate'] = copyOfContext['coordinate']
        coordinateDidChange = np.all(
            copyOfContext['previousCoordinate'] == copyOfContext['coordinate']) == False
        if coordinateDidChange:
            coordinate = copyOfContext['coordinate']
            if coordinate[2] != copyOfContext['previousCoordinate'][2]:
                comingFromDirection = None
            elif coordinate[0] != copyOfContext['previousCoordinate'][0] and coordinate[1] != copyOfContext['previousCoordinate'][1]:
                comingFromDirection = None
            elif coordinate[0] != copyOfContext['previousCoordinate'][0]:
                comingFromDirection = 'left' if coordinate[
                    0] > copyOfContext['previousCoordinate'][0] else 'right'
            elif coordinate[1] != copyOfContext['previousCoordinate'][1]:
                comingFromDirection = 'top' if coordinate[
                    1] > copyOfContext['previousCoordinate'][1] else 'bottom'
            copyOfContext['previousCoordinate'] = copyOfContext['coordinate']
        copyOfContext['comingFromDirection'] = comingFromDirection
        gameContext = copyOfContext
        return copyOfContext

    directionObserver = hudImgObserver.pipe(operators.map(resolveDirection))

    def resolveCreatures(context):
        global gameContext, hudCreatures
        copyOfContext = context.copy()
        hudCreatures = hud.creatures.getCreatures(
            copyOfContext['battleListCreatures'], copyOfContext['comingFromDirection'], copyOfContext['hud']['coordinate'], copyOfContext['hudImg'], copyOfContext['coordinate'], copyOfContext['resolution'])
        monsters = hud.creatures.getCreatureByType(hudCreatures, 'monster')
        players = hud.creatures.getCreatureByType(hudCreatures, 'player')
        copyOfContext['monsters'] = monsters
        copyOfContext['players'] = players
        gameContext = copyOfContext
        return copyOfContext

    hudCreaturesObserver = directionObserver.pipe(
        operators.map(resolveCreatures))

    def handleLoot(context):
        global gameContext
        copyOfContext = context.copy()
        corpsesToLoot = np.array([], dtype=hud.creatures.creatureType)
        beingAttackedIndexes = np.where(
            hudCreatures['isBeingAttacked'] == True)[0]
        hasCreatureBeingAttacked = len(beingAttackedIndexes) > 0
        if core.hasNewLoot(copyOfContext['screenshot']) and copyOfContext['beingAttackedCreature']:
            corpsesToLoot = np.append(copyOfContext['corpsesToLoot'], [
                                      copyOfContext['beingAttackedCreature']], axis=0)
        beingAttackedCreature = None
        if hasCreatureBeingAttacked:
            beingAttackedCreature = hudCreatures[beingAttackedIndexes[0]]
        copyOfContext['beingAttackedCreature'] = beingAttackedCreature
        copyOfContext['corpsesToLoot'] = corpsesToLoot
        gameContext = copyOfContext
        return copyOfContext

    lootObserver = hudCreaturesObserver.pipe(operators.map(handleLoot))

    def handleDecision(context):
        global gameContext
        copyOfContext = context.copy()
        copyOfContext['way'] = gameplay.decision.getWay(
            copyOfContext['corpsesToLoot'], copyOfContext['monsters'], copyOfContext['coordinate'])
        gameContext = copyOfContext
        return copyOfContext

    decisionObserver = lootObserver.pipe(
        operators.map(handleDecision)
    )

    def handleTasks(context):
        global gameContext
        copyOfContext = context.copy()
        if copyOfContext['cavebot']['waypoints']['currentIndex'] == None:
            copyOfContext['cavebot']['waypoints']['currentIndex'] = radar.core.getClosestWaypointIndexFromCoordinate(
                copyOfContext['coordinate'], copyOfContext['cavebot']['waypoints']['points'])
        currentWaypointIndex = copyOfContext['cavebot']['waypoints']['currentIndex']
        print('currentWaypointIndex', currentWaypointIndex)
        nextWaypointIndex = utils.array.getNextArrayIndex(
            copyOfContext['cavebot']['waypoints']['points'], currentWaypointIndex)
        print('nextWaypointIndex', nextWaypointIndex)
        currentWaypoint = copyOfContext['cavebot']['waypoints']['points'][currentWaypointIndex]
        print('currentWaypoint', currentWaypoint)
        nextWaypoint = copyOfContext['cavebot']['waypoints']['points'][nextWaypointIndex]
        waypointsStateIsEmpty = copyOfContext['cavebot']['waypoints']['state'] == None
        if waypointsStateIsEmpty:
            copyOfContext['cavebot']['waypoints']['state'] = gameplay.waypoint.resolveGoalCoordinate(
                copyOfContext['coordinate'], currentWaypoint)
        result = copyOfContext['coordinate'] == copyOfContext['cavebot']['waypoints']['state']['checkInCoordinate']
        didReachWaypoint = np.all(result) == True
        if copyOfContext['currentGroupTask'] == None:
            print('no tasks, gerando')
            print('type ->', currentWaypoint['type'])
            copyOfContext['currentGroupTask'] = gameplay.resolvers.resolveTasksByWaypointType(
                copyOfContext, currentWaypoint)
        if copyOfContext['way'] == 'cavebot':
            isTryingToAttackClosestCreature = copyOfContext[
                'currentGroupTask'] is not None and copyOfContext['currentGroupTask'].name == 'groupOfAttackClosestCreature'
            if isTryingToAttackClosestCreature:
                print('to tentando atacar')
            else:
                targetCreature, currentGroupTask = gameplay.cavebot.resolveCavebotTasks(
                    copyOfContext)
                copyOfContext['targetCreature'] = targetCreature
                if currentGroupTask is not None:
                    if copyOfContext['lastPressedKey'] is not None:
                        pyautogui.keyUp(copyOfContext['lastPressedKey'])
                        copyOfContext['lastPressedKey'] = None
                    copyOfContext['currentGroupTask'] = currentGroupTask
        if didReachWaypoint:
            if copyOfContext['currentGroupTask'] == None or copyOfContext['currentGroupTask'].name == 'groupOfWalk' or copyOfContext['currentGroupTask'].name == 'groupOfSingleWalk':
                copyOfContext['cavebot']['waypoints']['currentIndex'] = nextWaypointIndex
                copyOfContext['cavebot']['waypoints']['state'] = gameplay.waypoint.resolveGoalCoordinate(
                    copyOfContext['coordinate'], nextWaypoint)
        gameContext = copyOfContext
        print(copyOfContext['currentGroupTask'])
        return copyOfContext

    def hasTaskToExecute(context):
        has = context['currentGroupTask'] is not None
        return has

    taskObserver = decisionObserver.pipe(
        operators.map(handleTasks),
        operators.filter(hasTaskToExecute),
    )

    def taskObservable(context):
        global gameContext, taskExecutor
        copyOfContext = context.copy()
        copyOfContext = taskExecutor.exec(copyOfContext)
        copyOfContext['lastCoordinateVisited'] = context['coordinate']
        gameContext = copyOfContext

    taskObserver.subscribe(taskObservable)

    # eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
