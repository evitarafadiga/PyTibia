import numpy as np
from time import time
from gameplay.factories.makeWalkTask import makeWalkTask
from gameplay.groupTasks.groupTaskExecutor import GroupTaskExecutor
from gameplay.typings import taskType
from gameplay.waypoint import generateFloorWalkpoints


class GroupOfWalkTasks(GroupTaskExecutor):
    def __init__(self, context, waypointCoordinate):
        self.createdAt = time()
        self.startedAt = None
        self.delayBeforeStart = 0
        self.delayAfterComplete = 0
        self.name = 'groupOfWalk'
        self.status = 'notStarted'
        self.tasks = self.generateTasks(context, waypointCoordinate)
        self.value = waypointCoordinate

    def generateTasks(self, context, waypointCoordinate):
        walkpoints = generateFloorWalkpoints(
            context['coordinate'], waypointCoordinate)
        tasks = np.array([], dtype=taskType)
        for walkpoint in walkpoints:
            walkpointTask = makeWalkTask(walkpoint)
            taskToAppend = np.array([walkpointTask], dtype=taskType)
            tasks = np.append(tasks, [taskToAppend])
        return tasks

    def shouldIgnore(self, _):
        return False

    def did(self, _):
        for taskWithName in self.tasks:
            _, task = taskWithName
            if task.status != 'completed':
                return False
        return True

    def shouldRestart(self, _):
        return False

    def onIgnored(self, context):
        return context

    def onDidComplete(self, context):
        return context
