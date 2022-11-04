import numpy as np
from time import time
from utils.array import getNextArrayIndex


class SetNextWaypointTask:
    def __init__(self, value):
        self.createdAt = time()
        self.startedAt = None
        self.finishedAt = None
        self.delayBeforeStart = 0
        self.delayAfterComplete = 0
        self.name = 'setNextWaypoint'
        self.status = 'notStarted'
        self.value = value

    def shouldIgnore(self, _):
        return False

    def do(self, context):
        nextWaypointIndex = getNextArrayIndex(
            context['waypoints']['points'], context['waypoints']['currentIndex'])
        context['waypoints']['currentIndex'] = nextWaypointIndex
        context['waypoints']['state'] = None
        return context

    def did(self, _):
        return True

    def shouldRestart(self, _):
        return False

    def onIgnored(self, context):
        return context

    def onDidComplete(self, context):
        return context
