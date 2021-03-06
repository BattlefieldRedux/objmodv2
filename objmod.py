# --------------------------------------------------------------------------
# Project Reality x by rpoxo
# x
#
# ~ objmodv2.py
#
# Description:
#
# x
#
# Credits:
#   x
# -------------------------------------------------------------------------

# importing python system modules
import sys
import time

# importing modules from standart bf2 package
import bf2
import host

# importing project reality packages
import game.realitytimer as rtimer


# importing custom modules
import debugger
import constants as C

G_QUERY_MANAGER = None
G_TRACKED_OBJECT = None
G_UPDATE_TIMER = None
G_UPDATE_LAST = 0.0
# debugger
D = debugger.Debugger()

class QueryManager:

    def __init__(self):
        D.debugMessage('QueryManager::initializing')
        
        self.queries = []
        
        D.debugMessage('QueryManager::initialized!')
    

    def setupDefaultQueries(self):
        del self.queries
        self.queries = []

        for vehicle in C.DEFAULT_QUERIES:
            D.debugMessage('QueryManager::parsing %s' % (vehicle))
            for vehicle_part in C.DEFAULT_QUERIES[vehicle]:
                invoke_string = ('ObjectTemplate.active %s' % (str(vehicle_part)))
                host.rcon_invoke(invoke_string)
                D.debugMessage(invoke_string)
                for param in C.DEFAULT_QUERIES[vehicle][vehicle_part]:
                    host.rcon_invoke(param)
                    D.debugMessage(param)

# ------------------------------------------------------------------------
# Init
# ------------------------------------------------------------------------


def init():
    global G_QUERY_MANAGER

    G_QUERY_MANAGER = QueryManager()
    G_QUERY_MANAGER.setupDefaultQueries()

    host.registerGameStatusHandler(onGameStatusChanged)

# ------------------------------------------------------------------------
# DeInit
# ------------------------------------------------------------------------


def deinit():
    host.unregisterGameStatusHandler(onGameStatusChanged)


# ------------------------------------------------------------------------
# onGameStatusChanged
# ------------------------------------------------------------------------
def onGameStatusChanged(status):

    if status == bf2.GameStatus.Playing:
        # registering chatMessage handler
        host.registerHandler('ChatMessage', onChatMessage, 1)

        # test stuff
        #select_timer = rtimer.Timer(setTestVehicle, 3, 1, 'us_jet_a10a')

        # test stuff2
        host.registerHandler('EnterVehicle', onEnterVehicle)
        host.registerHandler('ExitVehicle', onExitVehicle)
        
        if G_QUERY_MANAGER is not None:
            G_QUERY_MANAGER.setupDefaultQueries()

        resetUpdateTimer()

        D.debugMessage('===== FINISHED OBJMOD INIT =====')


# 30+-5fps = ~0.33...ms is server frame, no need for updates more frequently than 0.05
def resetUpdateTimer():
    global G_UPDATE_TIMER


    if G_UPDATE_TIMER is not None:
        G_UPDATE_TIMER.destroy()
        G_UPDATE_TIMER = None

        G_UPDATE_TIMER = rtimer.Timer(onUpdate, 1, 1)
        G_UPDATE_TIMER.setRecurring(0.05)
    else:
        G_UPDATE_TIMER = rtimer.Timer(onUpdate, 1, 1)
        G_UPDATE_TIMER.setRecurring(0.05)
    
    D.debugMessage('resetUpdateTimer(): reloaded updated timer')

# offloading debug
# tnx pie&mats for idea, althorugh my implementation is worse
def onUpdate(data=''):
    global G_UPDATE_LAST

    time_wall_now = host.timer_getWallTime()
    time_delta = time_wall_now - G_UPDATE_LAST
    time_epoch = time.time()
    G_UPDATE_LAST = host.timer_getWallTime()
    #D.debugMessage('Time: %s+%s@%s' % (time_wall_now, time_delta, time_epoch))
    if G_TRACKED_OBJECT is not None and G_TRACKED_OBJECT.isValid():
        position = G_TRACKED_OBJECT.getPosition()
        rotation = G_TRACKED_OBJECT.getRotation()
        message = {
            'position': position,
            'rotation': rotation,
            'time_wall': time_wall_now,
            'time_delta': time_delta,
            'time_epoch': time_epoch
        }
        #D.debugMessage('Position: %s\nRotation: %s\n' % (position, rotation))
        D.updateMessageUDP(message)


def onEnterVehicle(player, vehicle, freeSoldier=False):
    global G_TRACKED_OBJECT

    G_TRACKED_OBJECT = vehicle
    D.debugMessage('Player entered %s' % (G_TRACKED_OBJECT.templateName))
    resetUpdateTimer()


def onExitVehicle(player, vehicle):
    global G_TRACKED_OBJECT

    G_TRACKED_OBJECT = None
    D.debugMessage('Player left %s' % (vehicle.templateName))
    resetUpdateTimer()


def setTestVehicle(template, data=''):
    global G_TRACKED_OBJECT

    objects = bf2.objectManager.getObjectsOfTemplate(template)
    D.debugMessage(
        'setTestVehicle(): found %s objects of template %s' %
        (len(objects), template))
    G_TRACKED_OBJECT = objects[0]
    D.debugMessage('Selected first object of template %s at %s' % (
        G_TRACKED_OBJECT.templateName, str(G_TRACKED_OBJECT.getPosition())))


# ------------------------------------------------------------------------
# onChatMessage
# Callback that managing chat messages.
##########################################################################
# !NEVER call any messages directly from onChatMessage handler
# It causing inifite loop
##########################################################################
# ------------------------------------------------------------------------
def onChatMessage(playerId, text, channel, flags):

    # fix for local non-dedicated servers
    if playerId == -1:
        playerId = 255

    # getting player object by player index
    player = bf2.playerManager.getPlayerByIndex(playerId)

    # standart check for invalid players
    if player is None or player.isValid() is False:
        return

    # common way to filter chat message
    # clearing text as any channel except Global are prefixed
    text = text.replace('HUD_TEXT_CHAT_COMMANDER', '')
    text = text.replace('HUD_TEXT_CHAT_TEAM', '')
    text = text.replace('HUD_TEXT_CHAT_SQUAD', '')
    text = text.replace('HUD_CHAT_DEADPREFIX', '')
    text = text.replace('* ', '')
    text = text.strip()

    # splitting filtered message text to arguments
    args = text.split(' ')

    if args[0] == C.COMMANDKEY:
        del args[0]
        if len(args) == 0:
            D.debugMessage('NO ARGS IN CHAT MSG', ['echo'])
            return
        commandHandler(player, args)
    else:
        pass


# ------------------------------------------------------------------------
# commandHandler
# wrapper around function calls
# ------------------------------------------------------------------------
def commandHandler(player, args):
    """
        commandHandler
            handling functions calls for ingame debug
    """

    if args[0] == 'reload':
        reload(C)  # reloading constant file
        return G_QUERY_MANAGER.setupDefaultQueries()

    if args[0] == 'reset':
        return resetUpdateTimer()

    # createQuery(args)
    D.debugMessage('commandHandler::args = %s' % (str(args)))


# EOF
