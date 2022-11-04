import numpy as np
from time import time
from gameplay.factories.makeDepositItemsTask import makeDepositItemsTask
from gameplay.factories.makeOpenBackpackTask import makeOpenBackpackTask
from gameplay.groupTasks.groupTaskExecutor import GroupTaskExecutor
from gameplay.typings import taskType


class GroupOfDepositItemsTasks(GroupTaskExecutor):
    def __init__(self, context, waypoint):
        self.createdAt = time()
        self.startedAt = None
        self.delayBeforeStart = 1
        self.delayAfterComplete = 1
        self.name = 'groupOfDepositItems'
        self.status = 'notStarted'
        self.tasks = self.generateTasks(context, waypoint)
        self.value = waypoint

    def generateTasks(self, context, waypoint):
        tasks = np.array([], dtype=taskType)
        tasksToAppend = np.array([
            # - abrir a main backpack se estiver fechada
            makeOpenBackpackTask(context['backpacks']['main']),
            # - abrir a loot backpack se estiver fechada
            makeOpenBackpackTask(context['backpacks']['loot']),
            # - verificar se tem loot, se sim, ir até um free depot
            # - verificar se tem loot, se sim, depositar itens
            makeDepositItemsTask(),
        ], dtype=taskType)
        tasks = np.append(tasks, [tasksToAppend])
        return tasks

    def shouldIgnore(self, _):
        return False

    def shouldRestart(self, _):
        return False

    def onIgnored(self, context):
        return context

    def onDidComplete(self, context):
        return context
