import math
import numpy as np
import pathlib
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
import radar.config
import radar.core
import utils.core
import utils.image
import utils.matrix
from wiki.creatures import creatures


currentPath = pathlib.Path(__file__).parent.resolve()
hudWidthOf1080 = 960
hudWidthDouble = hudWidthOf1080 * 2
hudWidthTriple = hudWidthOf1080 * 3
lifeBarWidth = 26
lifeBarBlackPixelsMapperOf1080 = np.array([
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
    hudWidthOf1080, hudWidthOf1080 + lifeBarWidth,
    hudWidthDouble, hudWidthDouble + lifeBarWidth,
    hudWidthTriple, hudWidthTriple + 1, hudWidthTriple + 2, hudWidthTriple + 3, hudWidthTriple +
    4, hudWidthTriple + 5, hudWidthTriple + 6, hudWidthTriple + 7, hudWidthTriple +
    8, hudWidthTriple + 9, hudWidthTriple + 10, hudWidthTriple + 11, hudWidthTriple + 12, hudWidthTriple + 13, hudWidthTriple +
    14, hudWidthTriple + 15, hudWidthTriple + 16, hudWidthTriple +
    17, hudWidthTriple + 18, hudWidthTriple + 19, hudWidthTriple + 20, hudWidthTriple + 21, hudWidthTriple +
    22, hudWidthTriple + 23, hudWidthTriple +
    24, hudWidthTriple + 25, hudWidthTriple + 26
])

lifeBarBlackPixelsMapperOf720 = np.array([
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
    480, 506,
    960, 986,
    1440, 1441, 1442, 1443, 1444, 1445, 1446, 1447, 1448, 1449, 1450, 1451, 1452, 1453, 1454, 1455, 1456, 1457, 1458, 1459, 1460, 1461, 1462, 1463, 1464, 1465, 1466
])

resolutions = {
    720: {
        'lifeBarblackPixelsMapper': lifeBarBlackPixelsMapperOf720,
        'flattened': np.zeros(lifeBarBlackPixelsMapperOf720.size),
        'numberOfPixelsInHud': 168960,
        'hudHeight': 352,
        'hudWidth': 480,
        'slotWidth': 32,
    },
    1080: {
        'lifeBarblackPixelsMapper': lifeBarBlackPixelsMapperOf1080,
        'flattened': np.zeros(lifeBarBlackPixelsMapperOf1080.size),
        'numberOfPixelsInHud': 675840,
        'hudHeight': 704,
        'hudWidth': 960,
        'slotWidth': 64,
    },
}

creaturesNamesHashes = {}
for creature in creatures:
    creaturesNamesHashes[creature] = utils.image.loadAsGrey(
        f'{currentPath}/images/monsters/{creature}.png')

creatureType = np.dtype([
    ('name', np.str_, 64),
    ('type', np.str_, 64),
    ('isBeingAttacked', np.bool_),
    ('slot', np.uint8, (2,)),
    ('coordinate', np.uint16, (3,)),
    ('windowCoordinate', np.uint32, (2,))
])


def cleanCreatureName(creatureName):
    creatureName = np.where(creatureName == 29, 0, creatureName)
    creatureName = np.where(creatureName == 57, 0, creatureName)
    creatureName = np.where(creatureName == 91, 0, creatureName)
    creatureName = np.where(creatureName == 113, 0, creatureName)
    creatureName = np.where(creatureName == 152, 0, creatureName)
    creatureName = np.where(creatureName == 170, 0, creatureName)
    creatureName = np.where(creatureName == 192, 0, creatureName)
    return creatureName


def getClosestCreature(hudCreatures, coordinate):
    hasNoCreatures = len(hudCreatures) == 0
    if hasNoCreatures:
        return None
    floorLevel = coordinate[2]
    walkableFloorsSqms = radar.config.walkableFloorsSqms[floorLevel].copy()
    hudWalkableFloorsSqms = getHudWalkableFloorsSqms(
        walkableFloorsSqms, coordinate)
    adjacencyMatrix = utils.matrix.getAdjacencyMatrix(hudWalkableFloorsSqms)
    sqmsGraph = csr_matrix(adjacencyMatrix)
    playerHudIndex = 82
    sqmsGraphWeights = dijkstra(
        sqmsGraph, directed=True, indices=playerHudIndex, unweighted=False)
    creaturesSlots = hudCreatures['slot'][:, [1, 0]]
    hudWalkableFloorsSqmsCreatures = np.zeros((11, 15))
    hudWalkableFloorsSqmsCreatures[creaturesSlots[:,
                                                  0], creaturesSlots[:, 1]] = 1
    creaturesIndexes = np.nonzero(
        hudWalkableFloorsSqmsCreatures.flatten() == 1)[0]
    creaturesGraphWeights = np.take(sqmsGraphWeights, creaturesIndexes)
    nonTargetCreaturesIndexes = np.where(creaturesGraphWeights == np.inf)[0]
    creaturesIndexes = np.delete(creaturesIndexes, nonTargetCreaturesIndexes)
    creaturesGraphWeights = np.delete(
        creaturesGraphWeights, nonTargetCreaturesIndexes)
    hasOnlyNonTargetCreatures = len(creaturesGraphWeights) == 0
    if hasOnlyNonTargetCreatures:
        return None
    creaturesDistances = np.where(
        creaturesGraphWeights == np.amin(creaturesGraphWeights))[0]
    closestCreatureHudIndex = creaturesIndexes[np.random.choice(
        creaturesDistances)]
    creatureSlot = [closestCreatureHudIndex %
                    15, closestCreatureHudIndex // 15]
    closestCreatureIndex = np.where(
        (hudCreatures['slot'] == creatureSlot).all(axis=1))[0][0]
    closestCreature = hudCreatures[closestCreatureIndex]
    return closestCreature


# TODO: improve clean code
def getCreaturesBars(hudImg, resolution):
    global resolutions
    flattenedHudImg = hudImg.flatten()
    blackPixelsIndexes = np.nonzero(flattenedHudImg == 0)[0]
    maxBlackPixelIndex = resolutions[resolution]['numberOfPixelsInHud'] - (
        resolutions[resolution]['hudWidth'] * 4)
    allowedBlackPixelsIndexes = np.nonzero(
        blackPixelsIndexes < maxBlackPixelIndex)[0]
    blackPixelsIndexes = np.take(blackPixelsIndexes, allowedBlackPixelsIndexes)
    noBlackPixels = blackPixelsIndexes.size == 0
    if noBlackPixels:
        return np.array([])
    blackPixelsIndexesDiff = np.diff(blackPixelsIndexes)
    blackPixelsIndexesDiff = np.where(blackPixelsIndexesDiff == 1, 1, 0)
    cumulativeOfBlackPixelsIndexesDiff = np.cumsum(blackPixelsIndexesDiff)
    corr = np.diff(np.hstack(
        ((0,), cumulativeOfBlackPixelsIndexesDiff[blackPixelsIndexesDiff == 0])))
    a2 = blackPixelsIndexesDiff.copy()
    a2[blackPixelsIndexesDiff == 0] -= corr
    f = a2.cumsum()
    h = np.where(f == 26)[0]
    h = h - 25
    blackPixelsIndexes = np.take(blackPixelsIndexes, h)
    blackPixelsIndexes2d = np.broadcast_to(
        blackPixelsIndexes, (resolutions[resolution]['lifeBarblackPixelsMapper'].size, blackPixelsIndexes.size))
    blackPixelsIndexes2d = np.transpose(blackPixelsIndexes2d)
    z = np.add(blackPixelsIndexes2d,
               resolutions[resolution]['lifeBarblackPixelsMapper'])
    pixelsColorsIndexes = np.take(hudImg, z)
    g = (pixelsColorsIndexes == resolutions[resolution]['flattened']).all(1)
    possibleCreatures = np.nonzero(g)[0]
    hasNoCreaturesBars = possibleCreatures.size == 0
    if hasNoCreaturesBars:
        return np.array([])
    creaturesBars = np.take(blackPixelsIndexes, possibleCreatures)
    creaturesBarsX = creaturesBars % resolutions[resolution]['hudWidth']
    creaturesBarsY = creaturesBars // resolutions[resolution]['hudWidth']
    creaturesBarsXY = np.column_stack((creaturesBarsX, creaturesBarsY))
    return creaturesBarsXY


def getCreatures(battleListCreatures, direction, hudCoordinate, hudImg, coordinate, resolution):
    """
    TODO:
    - Find a way to avoid 3 calculation times when comparing names since some words have a wrong location
    - Whenever the last species is left, avoid loops and resolve species immediately for remaining creatures bars
    """
    creaturesBars = getCreaturesBars(hudImg, resolution)
    creatures = np.array([], dtype=creatureType)
    hasNoCreaturesBars = len(creaturesBars) == 0
    if hasNoCreaturesBars:
        return creatures
    hasNoBattleListCreatures = len(battleListCreatures) == 0
    if hasNoBattleListCreatures:
        return creatures
    hudWidth = len(hudImg[1])
    x = (len(hudImg[1]) / 2) - 1
    y = (len(hudImg[0]) / 2) - 1
    slotWidth = len(hudImg[1]) // 15
    centersBars = np.broadcast_to([x, y], (len(creaturesBars), 2))
    absolute = np.absolute(creaturesBars - centersBars)
    power = np.power(absolute, 2)
    sum = np.sum(power, axis=1)
    sqrt = np.sqrt(sum)
    creaturesBarsSortedInxes = np.argsort(sqrt)
    for creatureBarSortedIndex in creaturesBarsSortedInxes:
        creatureBar = creaturesBars[creatureBarSortedIndex]
        nonCreaturesForCurrentBar = {}
        battleListCreaturesCount = len(battleListCreatures)
        for battleListIndex in range(battleListCreaturesCount):
            battleListCreature = battleListCreatures[battleListIndex]
            creatureName = battleListCreature['name']
            isUnknownCreature = creatureName == 'Unknown'
            if isUnknownCreature:
                creature = makeCreature(
                    creatureName, 'player', creatureBar, direction, hudCoordinate, hudImg, coordinate, slotWidth)
                creaturesToAppend = np.array([creature], dtype=creatureType)
                creatures = np.append(creatures, creaturesToAppend)
                battleListCreatures = np.delete(
                    battleListCreatures, battleListIndex)
                continue
            creatureTypeAlreadyTried = creatureName in nonCreaturesForCurrentBar
            if creatureTypeAlreadyTried:
                continue
            _, creatureNameWidth = creaturesNamesHashes[creatureName].shape
            (creatureBarX, creatureBarY) = creatureBar
            creatureBarY0 = creatureBarY - 13
            creatureBarY1 = creatureBarY0 + 11
            creatureNameImgHalfWidth = math.floor(creatureNameWidth / 2)
            leftDiff = max(creatureNameImgHalfWidth - 13, 0)
            gapLeft = 0 if creatureBarX > leftDiff else leftDiff - creatureBarX
            gapInnerLeft = 0 if creatureNameWidth > 27 else math.ceil(
                (27 - creatureNameWidth) / 2)
            rightDiff = max(creatureNameWidth -
                            creatureNameImgHalfWidth - 14, 0)
            gapRight = 0 if hudWidth > (
                creatureBarX + 27 + rightDiff) else creatureBarX + 27 + rightDiff - hudWidth
            gapInnerRight = 0 if creatureNameWidth > 27 else math.floor(
                (27 - creatureNameWidth) / 2)
            startingX = max(0, creatureBarX - creatureNameImgHalfWidth +
                            13 + gapLeft + gapInnerLeft - gapRight - gapInnerRight)
            endingX = min(960, creatureBarX + creatureNameImgHalfWidth +
                          13 + gapLeft + gapInnerLeft - gapRight - gapInnerRight)
            creatureNameImg = creaturesNamesHashes[creatureName].copy()
            creatureWithDirtNameImg = hudImg[creatureBarY0:creatureBarY1,
                                             startingX:endingX]
            if creatureNameImg.shape[1] != creatureWithDirtNameImg.shape[1]:
                creatureWithDirtNameImg = hudImg[creatureBarY0:creatureBarY1,
                                                 startingX:endingX + 1]
            # TODO: avoid cleaning matrix, search directly by specific colours
            creatureWithDirtNameImg = cleanCreatureName(
                creatureWithDirtNameImg)
            creatureDidMatch = utils.matrix.hasMatrixInsideOther(
                creatureWithDirtNameImg, creatureNameImg)
            if creatureDidMatch:
                creature = makeCreature(
                    creatureName, 'monster', creatureBar, direction, hudCoordinate, hudImg, coordinate, slotWidth)
                creaturesToAppend = np.array([creature], dtype=creatureType)
                creatures = np.append(creatures, creaturesToAppend)
                battleListCreatures = np.delete(
                    battleListCreatures, battleListIndex)
                break
            creatureNameImg2 = creaturesNamesHashes[creatureName].copy()
            creatureWithDirtNameImg2 = hudImg[creatureBarY0:creatureBarY1,
                                              startingX+1:endingX+1]
            if creatureNameImg2.shape[1] != creatureWithDirtNameImg2.shape[1]:
                creatureNameImg2 = creatureNameImg2[:,
                                                    0:creatureNameImg2.shape[1] - 1]
            creatureWithDirtNameImg2 = cleanCreatureName(
                creatureWithDirtNameImg2)
            creatureDidMatch = utils.matrix.hasMatrixInsideOther(
                creatureWithDirtNameImg2, creatureNameImg2)
            if creatureDidMatch:
                creature = makeCreature(
                    creatureName, 'monster', creatureBar, direction, hudCoordinate, hudImg, coordinate, slotWidth)
                creaturesToAppend = np.array([creature], dtype=creatureType)
                creatures = np.append(creatures, creaturesToAppend)
                battleListCreatures = np.delete(
                    battleListCreatures, battleListIndex)
                break
            creatureWithDirtNameImg3 = hudImg[creatureBarY0:creatureBarY1,
                                              startingX:endingX - 1]
            creatureWithDirtNameImg3 = cleanCreatureName(
                creatureWithDirtNameImg3)
            creatureNameImg3 = creaturesNamesHashes[creatureName].copy()
            creatureNameImg3 = creatureNameImg3[:, 1:creatureNameImg3.shape[1]]
            if creatureWithDirtNameImg3.shape[1] != creatureNameImg3.shape[1]:
                creatureNameImg3 = creatureNameImg3[:,
                                                    0:creatureNameImg3.shape[1] - 1]
            creatureDidMatch = utils.matrix.hasMatrixInsideOther(
                creatureWithDirtNameImg3, creatureNameImg3)
            if creatureDidMatch:
                creature = makeCreature(
                    creatureName, 'monster', creatureBar, direction, hudCoordinate, hudImg, coordinate, slotWidth)
                creaturesToAppend = np.array([creature], dtype=creatureType)
                creatures = np.append(creatures, creaturesToAppend)
                battleListCreatures = np.delete(
                    battleListCreatures, battleListIndex)
                break
            nonCreaturesForCurrentBar[creatureName] = True
    return creatures


def getCreatureByType(hudCreatures, type):
    return hudCreatures[hudCreatures['type'] == type]


def getDifferentCreaturesBySlots(previousHudCreatures, currentHudCreatures, slots):
    previousHudCreaturesBySlots = np.array(
        [], dtype=creatureType)
    currentHudCreaturesBySlots = np.array(
        [], dtype=creatureType)
    differentCreatures = np.array([], dtype=creatureType)
    for previousHudCreature in previousHudCreatures:
        if np.isin(previousHudCreature['slot'], slots).all():
            previousHudCreaturesBySlots = np.append(
                previousHudCreaturesBySlots, [previousHudCreature])
    for currentHudCreature in currentHudCreatures:
        if np.isin(currentHudCreature['slot'], slots).all():
            currentHudCreaturesBySlots = np.append(
                currentHudCreaturesBySlots, [currentHudCreature])
    for previousHudCreature in previousHudCreaturesBySlots:
        creatureDoesNotExists = True
        for currentHudCreature in currentHudCreatures:
            previousHudCreatureHash = utils.core.hashitHex(
                previousHudCreature)
            currentHudCreatureHash = utils.core.hashitHex(
                currentHudCreature)
            if previousHudCreatureHash == currentHudCreatureHash:
                creatureDoesNotExists = False
                break
        if creatureDoesNotExists:
            differentCreatures = np.append(
                differentCreatures, [previousHudCreature])
    return differentCreatures


def getHudWalkableFloorsSqms(walkableFloorsSqms, coordinate):
    (xOfPixelCoordinate, yOfPixelCoordinate) = utils.core.getPixelFromCoordinate(
        coordinate)
    hudWalkableFloorsSqms = walkableFloorsSqms[yOfPixelCoordinate -
                                               5:yOfPixelCoordinate+6, xOfPixelCoordinate-7:xOfPixelCoordinate+8].copy()
    return hudWalkableFloorsSqms


def getNearestCreaturesCount(creatures):
    hudWalkableFloorsSqmsCreatures = np.zeros((11, 15), dtype=np.uint)
    xySlots = creatures['slot'][:, [1, 0]]
    hudWalkableFloorsSqmsCreatures[xySlots[:, 0], xySlots[:, 1]] = 1
    indicesOfNearestCreatures = hudWalkableFloorsSqmsCreatures[
        [4, 4, 4, 5, 5, 6, 6, 6],
        [6, 7, 8, 6, 8, 6, 7, 8]
    ]
    nearestCreaturesCount = np.sum(indicesOfNearestCreatures)
    return nearestCreaturesCount


def getTargetCreature(hudCreatures):
    hasNoHudCreatures = len(hudCreatures) == 0
    if hasNoHudCreatures:
        return
    indexes2d = np.argwhere(hudCreatures['isBeingAttacked'] == True)
    if len(indexes2d) == 0:
        return
    indexes = indexes2d[0]
    hasNoTarget = len(indexes) == 0
    if hasNoTarget:
        return
    targetCreatureIndex = indexes[0]
    targetCreature = hudCreatures[targetCreatureIndex]
    return targetCreature


def hasTargetToCreatureBySlot(hudCreatures, slot, coordinate):
    hasNoHudCreatures = len(hudCreatures) == 0
    if hasNoHudCreatures:
        return False
    floorLevel = hudCreatures[0]['coordinate'][2]
    walkableFloorsSqms = radar.config.walkableFloorsSqms[floorLevel].copy()
    hudCreaturesSlots = hudCreatures['slot']
    hudWalkableFloorsSqms = getHudWalkableFloorsSqms(
        walkableFloorsSqms, coordinate)
    creaturesSlots = hudCreaturesSlots[:, [1, 0]]
    hudWalkableFloorsSqms[creaturesSlots[:, 0], creaturesSlots[:, 1]] = 0
    xOfSlot, yOfSlot = slot
    hudWalkableFloorsSqms[yOfSlot, xOfSlot] = 1
    adjacencyMatrix = utils.matrix.getAdjacencyMatrix(hudWalkableFloorsSqms)
    graph = csr_matrix(adjacencyMatrix)
    playerHudIndex = 82
    graphWeights = dijkstra(graph, directed=True,
                            indices=playerHudIndex, unweighted=False)
    graphWeights = graphWeights.reshape(11, 15)
    creatureGraphValue = graphWeights[yOfSlot, xOfSlot]
    hasTarget = creatureGraphValue != np.inf
    return hasTarget


def hasTargetToCreature(hudCreatures, hudCreature, coordinate):
    hasTarget = hasTargetToCreatureBySlot(
        hudCreatures, hudCreature['slot'], coordinate)
    return hasTarget


# TODO: Avoid creature target check when non target creature is different from battleList being attacked creature
# TODO: improve clean code
# TODO: windowCoordinate should be improved for hud edges
def makeCreature(creatureName, creatureType, creatureBar, direction, hudCoordinate, hudImg, coordinate, slotWidth):
    isBigHud = slotWidth == 64
    (hudCoordinateX, hudCoordinateY, _, _) = hudCoordinate
    (xOfCreatureBar, yOfCreatureBar) = creatureBar
    extraY = 0 if yOfCreatureBar <= 27 else 31
    wikiCreature = creatures.get(creatureName)
    hudMisalignment = wikiCreature.get('hudMisalignment', {'x': 0, 'y': 0})
    hudMisalignmentX = hudMisalignment['x'] if isBigHud else hudMisalignment['x'] / 2
    hudMisalignmentY = hudMisalignment['y'] if isBigHud else hudMisalignment['y'] / 2
    distanceBetweenSlotPixelLifeBar = 19 if isBigHud else 3
    xCoordinate = xOfCreatureBar - distanceBetweenSlotPixelLifeBar
    xSlot = round((xCoordinate + hudMisalignmentX) / slotWidth)
    xSlot = min(xSlot, 14)
    xSlot = max(xSlot, 0)
    yCoordinate = yOfCreatureBar + 5 + extraY
    yCoordinate = 0 if yOfCreatureBar <= 14 else yOfCreatureBar + 5
    ySlot = round((yCoordinate + hudMisalignmentY) / slotWidth)
    ySlot = min(ySlot, 10)
    ySlot = max(ySlot, 0)
    borderX = max(xOfCreatureBar - distanceBetweenSlotPixelLifeBar, 0)
    borderedCreatureImg = hudImg[yOfCreatureBar + 5:yOfCreatureBar +
                                 5 + slotWidth, borderX:borderX + slotWidth]
    borderGap = 4 if slotWidth == 64 else 2
    yOfBorder = slotWidth - borderGap
    borderedCreatureImg[borderGap:yOfBorder, borderGap:yOfBorder] = 0
    pixelsCount = np.sum(np.where(np.logical_or(
        borderedCreatureImg == 76, borderedCreatureImg == 166), 1, 0))
    # TODO: count by 720p resolution should be less than 1080p resolution
    isBeingAttacked = pixelsCount > 50
    slot = (xSlot, ySlot)
    coordinateX = coordinate[0] - 7 + xSlot
    coordinateY = coordinate[1] - 5 + ySlot
    coordinate = [coordinateX, coordinateY, coordinate[2]]
    currentCreatureCoordinateIsntWalkable = not radar.core.isCoordinateWalkable(
        coordinate)
    if currentCreatureCoordinateIsntWalkable:
        if direction == 'left' or direction == 'right':
            leftCoordinate = [coordinate[0] - 1,
                              coordinate[1], coordinate[2]]
            leftCoordinateIsWalkable = radar.core.isCoordinateWalkable(
                leftCoordinate)
            if leftCoordinateIsWalkable:
                coordinate = leftCoordinate
                xSlot = slot[0] - 1
                xSlot = min(xSlot, 14)
                xSlot = max(xSlot, 0)
                slot = (xSlot, slot[1])
            else:
                rightCoordinate = [coordinate[0] + 1,
                                   coordinate[1], coordinate[2]]
                rightCoordinateIsWalkable = radar.core.isCoordinateWalkable(
                    rightCoordinate)
                if rightCoordinateIsWalkable:
                    coordinate = rightCoordinate
                    xSlot = slot[0] + 1
                    xSlot = min(xSlot, 14)
                    xSlot = max(xSlot, 0)
                    slot = (xSlot, slot[1])
        if direction == 'top' or direction == 'bottom':
            topCoordinate = [coordinate[0],
                             coordinate[1] - 1, coordinate[2]]
            topCoordinateIsWalkable = radar.core.isCoordinateWalkable(
                topCoordinate)
            if topCoordinateIsWalkable:
                coordinate = topCoordinate
                ySlot = slot[1] - 1
                ySlot = min(ySlot, 10)
                ySlot = max(ySlot, 0)
                slot = (slot[0], ySlot)
            else:
                bottomCoordinate = [coordinate[0],
                                    coordinate[1] + 1, coordinate[2]]
                bottomCoordinateIsWalkable = radar.core.isCoordinateWalkable(
                    bottomCoordinate)
                if bottomCoordinateIsWalkable:
                    coordinate = bottomCoordinate
                    ySlot = slot[1] + 1
                    ySlot = min(ySlot, 10)
                    ySlot = max(ySlot, 0)
                    slot = (slot[0], ySlot)
    hudHeight, hudWidth = hudImg.shape
    halfOfSlot = (slotWidth / 2)
    maxHudHeightForAttacking = hudHeight - halfOfSlot
    maxHudWidthForAttacking = hudWidth - halfOfSlot
    xCoordinate = max(xCoordinate + halfOfSlot, halfOfSlot)
    xCoordinate = min(xCoordinate, maxHudWidthForAttacking)
    yCoordinate = max(yCoordinate + halfOfSlot, halfOfSlot)
    yCoordinate = min(yCoordinate, maxHudHeightForAttacking)
    windowCoordinate = (hudCoordinateX + xCoordinate,
                        hudCoordinateY + yCoordinate)
    creature = (creatureName, creatureType, isBeingAttacked, slot,
                coordinate, windowCoordinate)
    return creature
