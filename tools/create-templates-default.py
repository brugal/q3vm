#!/usr/bin/env python

####
# Copyright (C) 2012, 2020 Angelo Cano
#
# This file is part of Qvmdis.
#
# Qvmdis is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Qvmdis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Qvmdis.  If not, see <https://www.gnu.org/licenses/>.
####

import inspect, os.path, sys
from pycparser import parse_file
from printcstruct import print_struct, print_struct_offset

commentLString = """
; default templates file

; template [size]
; {
;    [offset] <size or type> name
;    ...
; }
;

; All the BASEQ3 structures defined in cgame/, game/, ui/, and q3_ui/ are
; included here.  This includes the structures defined in header files and
; structures used in individual .c files.
;
; cvarTable_t in ui/ui_main.c is renamed to cvarTable_t_ui since it is also
; defined in game/g_main.c.
;
"""
aliasesLString = """
;;; aliases
; game/q_shared.h
%alias int size_t
%alias int qboolean
%alias int cvarHandle_t
%alias int qhandle_t
%alias int sfxHandle_t
%alias int fileHandle_t
%alias int clipHandle_t

%alias float vec_t
%alias vec_t[2] vec2_t
%alias vec_t[3] vec3_t
%alias vec_t[4] vec4_t
%alias vec_t[5] vec5_t

%alias int fixed4_t
%alias int fixed8_t
%alias int fixed16_t

%alias int signed
%alias int trType_t

%alias int flagStatus_t  ; enum
%alias int connstate_t  ; enum

; game/bg_public.h
%alias int gametype_t  ; enum
%alias int gender_t  ; enum
%alias int itemType_t  ; enum
%alias int team_t  ; enum
%alias int weapon_t  ; enum

; cgame/tr_types.h
%alias int glDriverType_t  ; enum
%alias int glHardwareType_t  ; enum
%alias int refEntityType_t  ; enum
%alias int textureCompression_t  ; enum

; cgame/cg_local.h
%alias int footstep_t  ; enum
%alias int leBounceSoundType_t  ; enum
%alias int leMarkType_t  ; enum
%alias int leType_t  ; enum

; game/g_local.h
%alias gentity_s gentity_t
%alias gclient_s gclient_t
%alias int playerTeamStateState_t  ; enum
%alias int clientConnected_t  ; enum
%alias int spectatorState_t  ; enum
%alias int moverState_t  ; enum

; game/g_spawn.c
%alias int fieldtype_t  ; enum
"""

arrayConstantsLString = """
;;; array constants
; game/q_shared.h

%arrayConstant MAX_TOKENLENGTH 1024
%arrayConstant MAX_CVAR_VALUE_STRING 256
%arrayConstant MAX_CONFIGSTRINGS 1024
%arrayConstant MAX_GAMESTATE_CHARS 16000
%arrayConstant MAX_PS_EVENTS 2
%arrayConstant MAX_STATS 16
%arrayConstant MAX_PERSISTANT 16
%arrayConstant MAX_POWERUPS 16
%arrayConstant MAX_WEAPONS 16
%arrayConstant GLYPHS_PER_FONT 256
%arrayConstant MAX_QPATH 64

%arrayConstant MAX_TEAMNAME 32

%arrayConstant MAX_STRING_CHARS 1024
%arrayConstant MAX_STRING_TOKENS 1024
%arrayConstant MAX_CLIENTS 64
%arrayConstant MAX_NAME_LENGTH 32
%arrayConstant MAX_MODELS 256
%arrayConstant MAX_SOUNDS 256
%arrayConstant MAX_MAP_AREA_BYTES 32
%arrayConstant BIG_INFO_STRING 8192

%arrayConstant MAX_SAY_TEXT 150
%arrayConstant MAX_INFO_STRING 1024

; game/bg_public.h
%arrayConstant MAX_TOTALANIMATIONS 37
%arrayConstant MAX_ITEM_MODELS 4
%arrayConstant TEAM_NUM_TEAMS 4
%arrayConstant MAXTOUCH 32
%arrayConstant MAX_ANIMATIONS 31
%arrayConstant MAX_BOTS 1024

; cgame/cg_local.h
%arrayConstant MAX_VERTS_ON_POLY 10
%arrayConstant MAX_CUSTOM_SOUNDS 32
%arrayConstant MAX_SKULLTRAIL 10
%arrayConstant MAX_PREDICTED_EVENTS 16
%arrayConstant MAX_REWARDSTACK 10
%arrayConstant MAX_SOUNDBUFFER 20
%arrayConstant NUM_CROSSHAIRS 10
%arrayConstant FOOTSTEP_TOTAL 7
%arrayConstant TEAMCHAT_HEIGHT 8
%arrayConstant TEAMCHAT_WIDTH 80
%arrayConstant TEAMCHAT_WIDTH3_1 241  ;  TEAMCHAT_WIDTH * 3 + 1

; cgame/cg_public.h
%arrayConstant MAX_ENTITIES_IN_SNAPSHOT 256

; cgame/tr_types.h
%arrayConstant MAX_RENDER_STRINGS 8
%arrayConstant MAX_RENDER_STRING_LENGTH 32

; cgame/cg_draw.c
%arrayConstant LAG_SAMPLES 128

; cgame/cg_servercmds.c
%arrayConstant MAX_VOICECHATS 64
%arrayConstant MAX_VOICESOUNDS 64
%arrayConstant MAX_CHATSIZE 64

; game/g_local.h
%arrayConstant MAX_NETNAME 36
%arrayConstant MAX_SPAWN_VARS 64
%arrayConstant MAX_SPAWN_VARS_CHARS 4096
%arrayConstant BODY_QUEUE_SIZE 8
%arrayConstant MAX_FILEPATH 144

; game/ai_main.h
%arrayConstant MAX_ACTIVATEAREAS 32
%arrayConstant MAX_ITEMS 256
%arrayConstant MAX_PROXMINES 64
%arrayConstant MAX_ACTIVATESTACK 8

; game/be_ai_chat.h
%arrayConstant MAX_MESSAGE_SIZE 256
%arrayConstant MAX_MATCHVARIABLES 8

; game/be_aas.h
%arrayConstant MAX_STRINGFIELD 80

; q3_ui/ui_local.h
%arrayConstant MAX_MENUITEMS 64
%arrayConstant MAX_EDIT_LINE 256
%arrayConstant MAX_MENUDEPTH 8

; q3_ui/ui_demos2.c
%arrayConstant MAX_DEMOS 128
%arrayConstant NAMEBUFSIZE_DEMOS 2048  ; MAX_DEMOS * 16

; q3_ui/ui_loadconfig.c
%arrayConstant MAX_CONFIGS 128
%arrayConstant NAMEBUFSIZE_CONFIGS 2048  ; MAX_CONFIGS * 16

; q3_ui/ui_mods.c
%arrayConstant MAX_MODS 64
%arrayConstant NAMEBUFSIZE_MODS 3072  ; MAX_MODS * 48
%arrayConstant GAMEBUFSIZE 1024  ; MAX_MODS * 16

; q3_ui/ui_playermodel.c
%arrayConstant MAX_MODELSPERPAGE 16  ; PLAYERGRID_ROWS * PLAYERGRID_COLS
%arrayConstant MAX_PLAYERMODELS 256

; q3_ui/ui_servers2.c
%arrayConstant MAX_ADDRESSLENGTH 64
%arrayConstant MAX_HOSTNAMELENGTH_3 25  ;  MAX_HOSTNAMELENGTH + 3
%arrayConstant MAX_MAPNAMELENGTH 16
%arrayConstant MAX_LISTBOXWIDTH_SERVERS 68

; q3_ui/ui_sppostgame.c
%arrayConstant MAX_SCOREBOARD_CLIENTS 8

; q3_ui/ui_startserver.c
%arrayConstant MAX_MAPSPERPAGE 4
%arrayConstant MAX_SERVERMAPS 64
%arrayConstant MAX_NAMELENGTH_START_SERVER 16
%arrayConstant PLAYER_SLOTS 12
"""

# not used
# ; q3_ui/ui_specifyleague.c
# %arrayConstant MAX_LISTBOX_WIDTH_SPECIFY 40
# %arrayConstant MAX_LEAGUENAME 80
#

Q3sdk = os.path.join(os.sep, "home", "acano", "tmp", "sdk1", "mod-sdk-1.32")
CurrentDir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

def error_exit (msg):
    sys.stderr.write("ERROR: %s\n" % msg)
    sys.exit(1)

def usage ():
    sys.stderr.write("%s [--offset] [quake3 sdk location]\n" % os.path.basename(sys.argv[0]))
    sys.exit(1)

# cFileName:str
# structNames = [ structName1:str, structName2:str, ... ]
# structNewNames = structName:str -> structNewName:str
# aconsts = [ [ structName1:str, memberName1:str, [ arrayValue1:str, ... ] ], ... ]
# cFileNameAlt:str  load this file instead of cFileName

def struct_info (cFileName, structNames, aconsts, useOffset=False, structNewNames={}, cFileNameAlt=None):
    global Q3sdk

    # testing
    #if cFileName.startswith("cgame"):
    #    return
    #if cFileName.startswith("game"):
    #    return

    if cFileNameAlt:
        cfile = os.path.join(Q3sdk, "code", cFileNameAlt)
    else:
        cfile = os.path.join(Q3sdk, "code", cFileName)

    if not os.path.exists(cfile):
        error_exit("%s doesn't exist" % cfile)

    ast = parse_file(filename=cfile, use_cpp=True, cpp_path='gcc', cpp_args=['-nostdinc', '-m32', '-I', '/usr/share/python-pycparser/fake_libc_include', '-S', '-E'])

    print("; %s\n" % cFileName)

    arrayConstants = {}
    for a in aconsts:
        arrayConstants[a[0] + "." + a[1]] = a[2]

    debugLevel = 0

    if useOffset:
        linkObjects = []

        if cFileName.startswith("cgame"):
            linkObjects = [os.path.join(CurrentDir, "q3stubs", "cgame.o")]
        elif cFileName.startswith("game"):
            linkObjects = [os.path.join(CurrentDir, "q3stubs", "game.o")]
        #elif cFileName.startswith("ui"):
        #    linkObjects = [os.path.join(CurrentDir, "q3stubs", "ui.o")]
        elif cFileName.startswith("q3_ui"):
            linkObjects = [os.path.join(CurrentDir, "q3stubs", "q3_ui.o")]
        #else:
        #    error_exit("can't identify type for stub")

        if len(linkObjects) > 0:
            for ob in linkObjects:
                if not os.path.exists(ob):
                    error_exit("need to generate '%s' stub file" % ob)

        found = print_struct_offset(ast, cFileName=cfile, printAll=False, structNames=structNames, structNewNames=structNewNames, linkObjects=linkObjects, debugLevel=debugLevel)
    else:
        found, arrayConstantsUsed = print_struct(ast, printAll=False, structNames=structNames, structNewNames=structNewNames, arrayConstants=arrayConstants, debugLevel=debugLevel)
        for a in arrayConstants:
            if a not in arrayConstantsUsed:
                error_exit("%s not used in %s" % (a, cFileName))

    for s in structNames:
        if s not in found:
            error_exit("couldn't find %s in %s" % (s, cFileName))

def main ():
    global Q3sdk
    args = [sys.argv[0]]

    useOffset = False
    for a in sys.argv[1:]:
        if a == "--offset":
            useOffset = True
        else:
            args.append(a)

    if len(args) > 1:
        Q3sdk = args[1]

    if not os.path.exists(Q3sdk):
        error_exit("SDK location doesn't exist")
    if not os.path.isdir(Q3sdk):
        error_exit("SDK location isn't a directory")

    print(commentLString)
    print(aliasesLString)
    print(arrayConstantsLString)
    print(";;; templates")

    sys.stderr.flush()
    sys.stdout.flush()

    #FIXME "#ifdef MISSIONPACK" versions

    cfile = os.path.join("game", "q_shared.h")
    # vec3struct_t defined with LCC
    structs = [ "pc_token_t", "qint64", "cvar_t", "vmCvar_t",
                "cplane_t", "trace_t", "markFragment_t", "orientation_t",
                "gameState_t", "playerState_t", "usercmd_t", "trajectory_t",
                "entityState_t", "glyphInfo_t", "fontInfo_t", "qtime_t"
    ]
    aconsts = [
        # game/q_shared.h
        [ "pc_token_t", "string", ["MAX_TOKENLENGTH"] ],
        [ "vmCvar_t", "string", ["MAX_CVAR_VALUE_STRING"] ],
        [ "gameState_t", "stringOffsets", ["MAX_CONFIGSTRINGS"] ],
        [ "gameState_t", "stringData", ["MAX_GAMESTATE_CHARS"] ],
        [ "playerState_t", "events", ["MAX_PS_EVENTS"] ],
        [ "playerState_t", "eventParms", ["MAX_PS_EVENTS"] ],
        [ "playerState_t", "stats", ["MAX_STATS"] ],
        [ "playerState_t", "persistant", ["MAX_PERSISTANT"] ],
        [ "playerState_t", "powerups", ["MAX_POWERUPS"] ],
        [ "playerState_t", "ammo", ["MAX_WEAPONS"] ],
        [ "fontInfo_t", "glyphs", ["GLYPHS_PER_FONT"] ],
        [ "fontInfo_t", "name", ["MAX_QPATH"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("game", "bg_local.h")
    structs = [ "pml_t", "pmove_t", "animation_t", "gitem_t" ]
    aconsts = [
        # game/bg_local.h
        [ "pmove_t", "touchents", ["MAXTOUCH"] ],
        [ "gitem_t", "world_model", ["MAX_ITEM_MODELS"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset, cFileNameAlt=os.path.join("game", "bg_pmove.c"))

    cfile = os.path.join("cgame", "tr_types.h")
    structs = [ "polyVert_t", "poly_t", "refEntity_t", "refdef_t", "glconfig_t" ]
    aconsts = [
        # cgame/tr_types.h
        [ "refdef_t", "areamask", ["MAX_MAP_AREA_BYTES"] ],
        [ "refdef_t", "text", ["MAX_RENDER_STRINGS", "MAX_RENDER_STRING_LENGTH"] ],
        [ "glconfig_t", "renderer_string", ["MAX_STRING_CHARS"] ],
        [ "glconfig_t", "vendor_string", ["MAX_STRING_CHARS"] ],
        [ "glconfig_t", "version_string", ["MAX_STRING_CHARS"] ],
        [ "glconfig_t", "extensions_string", ["BIG_INFO_STRING"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset, cFileNameAlt=os.path.join("cgame", "cg_local.h"))

    # cgame/cg_public.h
    cfile = os.path.join("cgame", "cg_public.h")  # can just include cgame/cg_local.h
    structs = [ "snapshot_t" ]
    aconsts = [
        # cgame/cg_public.h
        [ "snapshot_t", "areamask", ["MAX_MAP_AREA_BYTES"] ],
        [ "snapshot_t", "entities", ["MAX_ENTITIES_IN_SNAPSHOT"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset, cFileNameAlt=os.path.join("cgame", "cg_local.h"))

    cfile = os.path.join("cgame", "cg_local.h")
    structs = [
        "lerpFrame_t", "playerEntity_t", "centity_t", "markPoly_t",
        "localEntity_t", "score_t", "clientInfo_t", "weaponInfo_t",
        "itemInfo_t", "powerupInfo_t", "skulltrail_t", "cg_t",
        "cgMedia_t", "cgs_t"
    ]
    aconsts = [
        # cgame/cg_local.h
        [ "markPoly_t", "verts", ["MAX_VERTS_ON_POLY"] ],
        [ "clientInfo_t", "name", ["MAX_QPATH"] ],
        [ "clientInfo_t", "modelName", ["MAX_QPATH"] ],
        [ "clientInfo_t", "skinName", ["MAX_QPATH"] ],
        [ "clientInfo_t", "headModelName", ["MAX_QPATH"] ],
        [ "clientInfo_t", "headSkinName", ["MAX_QPATH"] ],
        [ "clientInfo_t", "redTeam", ["MAX_TEAMNAME"] ],
        [ "clientInfo_t", "blueTeam", ["MAX_TEAMNAME"] ],
        [ "clientInfo_t", "animations", ["MAX_TOTALANIMATIONS"] ],
        [ "clientInfo_t", "sounds", ["MAX_CUSTOM_SOUNDS"] ],
        [ "itemInfo_t", "models", ["MAX_ITEM_MODELS"] ],
        [ "skulltrail_t", "positions", ["MAX_SKULLTRAIL"] ],
        [ "cg_t", "predictableEvents", ["MAX_PREDICTED_EVENTS"] ],
        [ "cg_t", "infoScreenText", ["MAX_STRING_CHARS"] ],
        [ "cg_t", "scores", ["MAX_CLIENTS"] ],
        [ "cg_t", "killerName", ["MAX_NAME_LENGTH"] ],
        [ "cg_t", "spectatorList", ["MAX_STRING_CHARS"] ],
        [ "cg_t", "skulltrails", ["MAX_CLIENTS"] ],
        [ "cg_t", "rewardCount", ["MAX_REWARDSTACK"] ],
        [ "cg_t", "rewardShader", ["MAX_REWARDSTACK"] ],
        [ "cg_t", "rewardSound", ["MAX_REWARDSTACK"] ],
        [ "cg_t", "soundBuffer", ["MAX_SOUNDBUFFER"] ],
        [ "cg_t", "testModelName", ["MAX_QPATH"] ],
        [ "cgMedia_t", "crosshairShader", ["NUM_CROSSHAIRS"] ],
        [ "cgMedia_t", "footsteps", ["FOOTSTEP_TOTAL", "4"] ],
        [ "cgs_t", "mapname", ["MAX_QPATH"] ],
        [ "cgs_t", "redTeam", ["MAX_QPATH"] ],
        [ "cgs_t", "blueTeam", ["MAX_QPATH"] ],
        [ "cgs_t", "voteString", ["MAX_STRING_TOKENS"] ],
        [ "cgs_t", "teamVoteString", ["2", "MAX_STRING_TOKENS"] ],
        [ "cgs_t", "gameModels", ["MAX_MODELS"] ],
        [ "cgs_t", "gameSounds", ["MAX_SOUNDS"] ],
        [ "cgs_t", "inlineDrawModel", ["MAX_MODELS"] ],
        [ "cgs_t", "inlineModelMidpoints", ["MAX_MODELS"] ],
        [ "cgs_t", "clientinfo", ["MAX_CLIENTS"] ],
        [ "cgs_t", "teamChatMsgs", ["TEAMCHAT_HEIGHT", "TEAMCHAT_WIDTH3_1"] ],
        [ "cgs_t", "teamChatMsgTimes", ["TEAMCHAT_HEIGHT"] ],
        [ "cgs_t", "acceptVoice", ["MAX_NAME_LENGTH"] ]
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("cgame", "cg_consolecmds.c")
    structs = [ "consoleCommand_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("cgame", "cg_draw.c")
    structs = [ "lagometer_t" ]
    aconsts = [
        # cgame/cg_draw.c
        [ "lagometer_t", "frameSamples", ["LAG_SAMPLES"] ],
        [ "lagometer_t", "snapshotFlags", ["LAG_SAMPLES"] ],
        [ "lagometer_t", "snapshotSamples", ["LAG_SAMPLES"] ],

    ]
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("cgame", "cg_marks.c")  # same as cgame/cg_particles.c
    structs = [ "cparticle_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("cgame", "cg_servercmds.c")
    structs = [ "orderTask_t", "voiceChat_t", "voiceChatList_t", "headModelVoiceChat_t", "bufferedVoiceChat_t" ]
    aconsts = [
        # cgame/cg_servercmds.c
        [ "voiceChat_t", "sounds", ["MAX_VOICESOUNDS"] ],
        [ "voiceChat_t", "chats", ["MAX_VOICESOUNDS", "MAX_CHATSIZE"] ],
        [ "voiceChatList_t", "voiceChats", ["MAX_VOICECHATS"] ],
        [ "bufferedVoiceChat_t", "cmd", ["MAX_SAY_TEXT"] ],
        [ "bufferedVoiceChat_t", "message", ["MAX_SAY_TEXT"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("game", "g_public.h")
    structs = [ "entityShared_t", "sharedEntity_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset, cFileNameAlt=os.path.join("game", "g_local.h"))

    cfile = os.path.join("game", "g_local.h")
    structs = [ "gentity_s", "playerTeamState_t", "clientSession_t", "clientPersistant_t", "gclient_s", "level_locals_t", "bot_settings_t" ]
    aconsts = [
        # game/g_local.h
        [ "clientPersistant_t", "netname", ["MAX_NETNAME"] ],
        [ "level_locals_t", "teamScores", ["TEAM_NUM_TEAMS"] ],
        [ "level_locals_t", "sortedClients", ["MAX_CLIENTS"] ],
        [ "level_locals_t", "voteString", ["MAX_STRING_CHARS"] ],
        [ "level_locals_t", "voteDisplayString", ["MAX_STRING_CHARS"] ],
        [ "level_locals_t", "teamVoteString", ["2", "MAX_STRING_CHARS"] ],
        [ "level_locals_t", "spawnVars", ["MAX_SPAWN_VARS", "2"] ],
        [ "level_locals_t", "spawnVarChars", ["MAX_SPAWN_VARS_CHARS"] ],
        [ "level_locals_t", "bodyQue", ["BODY_QUEUE_SIZE"] ],
        [ "bot_settings_t", "characterfile", ["MAX_FILEPATH"] ],
        [ "bot_settings_t", "team", ["MAX_FILEPATH"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("game", "be_ai_goal.h")
    structs = [ "bot_goal_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset, cFileNameAlt=os.path.join("game", "ai_main.c"))

    cfile = os.path.join("game", "ai_main.h")
    structs = [ "bot_waypoint_t", "bot_activategoal_t", "bot_state_t" ]
    aconsts = [
        # game/ai_main.h
        [ "bot_activategoal_t", "areas", ["MAX_ACTIVATEAREAS"] ],
        [ "bot_state_t", "inventory", ["MAX_ITEMS"] ],
        [ "bot_state_t", "proxmines", ["MAX_PROXMINES"] ],
        [ "bot_state_t", "activategoalheap", ["MAX_ACTIVATESTACK"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset, cFileNameAlt=os.path.join("game", "ai_main.c"))

    cfile = os.path.join("game", "be_aas.h")
    structs = [ "aas_trace_t", "aas_entityinfo_t", "aas_areainfo_t", "aas_clientmove_t", "aas_altroutegoal_t", "aas_predictroute_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset, cFileNameAlt=os.path.join("game", "ai_main.c"))

    cfile = os.path.join("game", "be_ai_chat.h")
    structs = [ "bot_consolemessage_t", "bot_matchvariable_t", "bot_match_t" ]
    aconsts = [
        # game/be_ai_chat.h
        [ "bot_consolemessage_t", "message", ["MAX_MESSAGE_SIZE"] ],
        [ "bot_match_t", "string", ["MAX_MESSAGE_SIZE"] ],
        [ "bot_match_t", "variables", ["MAX_MATCHVARIABLES"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset, cFileNameAlt=os.path.join("game", "ai_main.c"))

    cfile = os.path.join("game", "be_ai_move.h")
    structs = [ "bot_initmove_t", "bot_moveresult_t", "bot_avoidspot_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset, cFileNameAlt=os.path.join("game", "ai_main.c"))

    cfile = os.path.join("game", "be_ai_weap.h")
    structs = [ "projectileinfo_t", "weaponinfo_t" ]
    aconsts = [
        # game/be_ai_weap.h
        [ "projectileinfo_t", "name", ["MAX_STRINGFIELD"] ],
        [ "projectileinfo_t", "model", ["MAX_STRINGFIELD"] ],
        [ "weaponinfo_t", "name", ["MAX_STRINGFIELD"] ],
        [ "weaponinfo_t", "model", ["MAX_STRINGFIELD"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset, cFileNameAlt=os.path.join("game", "ai_main.c"))

    cfile = os.path.join("game", "botlib.h")
    structs = [ "bot_input_t", "bsp_surface_t", "bsp_trace_t", "bot_entitystate_t", "botlib_import_t", "aas_export_t", "ea_export_t", "ai_export_t", "botlib_export_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset, cFileNameAlt=os.path.join("game", "ai_main.c"))

    cfile = os.path.join("game", "ai_team.c")
    structs = [ "bot_ctftaskpreference_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("game", "ai_vcmd.c")
    structs = [ "voiceCommand_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("game", "g_bot.c")
    structs = [ "botSpawnQueue_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("game", "g_main.c")
    structs = [ "cvarTable_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("game", "g_mover.c")
    structs = [ "pushed_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("game", "g_spawn.c")
    structs = [ "field_t", "spawn_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("game", "g_svcmds.c")
    structs = [ "ipFilter_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("game", "g_team.c")
    structs = [ "teamgame_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("game", "g_utils.c")
    structs = [ "shaderRemap_t" ]
    aconsts = [
        # game/g_utils.c
        [ "shaderRemap_t", "oldShader", ["MAX_QPATH"] ],
        [ "shaderRemap_t", "newShader", ["MAX_QPATH"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    #FIXME MISSIONPACK ui/*

    cfile = os.path.join("ui", "ui_public.h")
    structs = [ "uiClientState_t" ]
    aconsts = [
        # ui/ui_public.h
        [ "uiClientState_t", "servername", ["MAX_STRING_CHARS"] ],
        [ "uiClientState_t", "updateInfoString", ["MAX_STRING_CHARS"] ],
        [ "uiClientState_t", "messageString", ["MAX_STRING_CHARS"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset, cFileNameAlt=os.path.join("ui", "ui_local.h"))

    cfile = os.path.join("q3_ui", "ui_local.h")
    structs = [ "menuframework_s", "menucommon_s", "mfield_t", "menufield_s", "menuslider_s", "menulist_s", "menuaction_s", "menuradiobutton_s", "menubitmap_s", "menutext_s", "playerInfo_t", "uiStatic_t" ]
    aconsts = [
        # q3_ui/ui_local.h
        [ "menuframework_s", "items", ["MAX_MENUITEMS"] ],
        [ "mfield_t", "buffer", ["MAX_EDIT_LINE"] ],
        [ "playerInfo_t", "animations", ["MAX_ANIMATIONS"] ],
        [ "uiStatic_t", "stack", ["MAX_MENUDEPTH"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_addbots.c")
    structs = [ "addBotsMenuInfo_t" ]
    aconsts = [
        # q3_ui/ui_addbots.c
        [ "addBotsMenuInfo_t", "sortedBotNums", ["MAX_BOTS"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_cdkey.c")
    structs = [ "cdkeyMenuInfo_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_cinematics.c")
    structs = [ "cinematicsMenuInfo_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_confirm.c")
    structs = [ "confirmMenu_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_controls2.c")
    structs = [ "bind_t", "configcvar_t", "controls_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_credits.c")
    structs = [ "creditsmenu_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_demo2.c")
    structs = [ "demos_t" ]
    aconsts = [
        # q3_ui/ui_demos2.c
        [ "demos_t", "names", ["NAMEBUFSIZE_DEMOS"] ],
        [ "demos_t", "demolist", ["MAX_DEMOS"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_display.c")
    structs = [ "displayOptionsInfo_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_ingame.c")
    structs = [ "ingamemenu_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_loadconfig.c")
    structs = [ "configs_t" ]
    aconsts = [
        # q3_ui/ui_loadconfig.c
        [ "configs_t", "names", ["NAMEBUFSIZE_CONFIGS"] ],
        [ "configs_t", "configlist", ["MAX_CONFIGS"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    # not used
    #cfile = os.path.join("q3_ui", "ui_login.c")
    #structs = [ "login_t" ]
    #aconsts = []
    #struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_main.c")
    # cvarTable_t different from game/g_main.c version
    structs = [ "cvarTable_t" ]
    aconsts = []
    structNewNames = { "cvarTable_t" : "cvarTable_t_ui" }
    struct_info(cfile, structs, aconsts, useOffset, structNewNames=structNewNames)

    cfile = os.path.join("q3_ui", "ui_menu.c")
    structs = [ "mainmenu_t", "errorMessage_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_mods.c")
    structs = [ "mods_t" ]
    aconsts = [
        # q3_ui/ui_mods.c
        [ "mods_t", "description", ["NAMEBUFSIZE_MODS"] ],
        [ "mods_t", "fs_game", ["GAMEBUFSIZE"] ],
        [ "mods_t", "descriptionList", ["MAX_MODS"] ],
        [ "mods_t", "fs_gameList", ["MAX_MODS"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_network.c")
    structs = [ "networkOptionsInfo_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_options.c")
    structs = [ "optionsmenu_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_playermodel.c")
    structs = [ "playermodel_t" ]
    aconsts = [
        # q3_ui/ui_playermodel.c
        [ "playermodel_t", "pics", ["MAX_MODELSPERPAGE"] ],
        [ "playermodel_t", "picbuttons", ["MAX_MODELSPERPAGE"] ],
        [ "playermodel_t", "modelnames", ["MAX_PLAYERMODELS", "128"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_playersettings.c")
    structs = [ "playersettings_t" ]
    aconsts = [
        # q3_ui/ui_playersettings.c
        [ "playersettings_t", "playerModel", ["MAX_QPATH"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_preferences.c")
    structs = [ "preferences_t" ]
    aconsts = [
        # q3_ui/ui_preferences.c
        [ "preferences_t", "crosshairShader", ["NUM_CROSSHAIRS"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    # not used
    #cfile = os.path.join("q3_ui", "ui_rankings.c")
    #structs = [ "rankings_t" ]
    #aconsts = []
    #struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_removebots.c")
    structs = [ "removeBotsMenuInfo_t" ]
    aconsts = [
        # q3_ui/ui_removebots.c
        [ "removeBotsMenuInfo_t", "botClientNums", ["MAX_BOTS" ] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_saveconfig.c")
    structs = [ "saveConfig_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_serverinfo.c")
    structs = [ "serverinfo_t" ]
    aconsts = [
        # q3_ui/ui_serverinfo.c
        [ "serverinfo_t", "info", ["MAX_INFO_STRING"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_servers2.c")
    structs = [ "pinglist_t", "servernode_t", "table_t" ]
    aconsts = [
        # q3_ui/ui_servers2.c
        [ "pinglist_t", "adrstr", ["MAX_ADDRESSLENGTH"] ],
        [ "servernode_t", "adrstr", ["MAX_ADDRESSLENGTH"] ],
        [ "servernode_t", "hostname", ["MAX_HOSTNAMELENGTH_3"] ],
        [ "servernode_t", "mapname", ["MAX_MAPNAMELENGTH"] ],
        [ "table_t", "buff", ["MAX_LISTBOXWIDTH_SERVERS"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_setup.c")
    structs = [ "setupMenuInfo_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    # not used
    #cfile = os.path.join("q3_ui", "ui_signup.c")
    #structs = [ "signup_t" ]
    #aconsts = []
    #struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_sound.c")
    structs = [ "soundOptionsInfo_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    # not used
    #cfile = os.path.join("q3_ui", "ui_specifyleague.c")
    # name conflict: table_t also in ui_servers2.c
    #structs = [ "specifyleague_t", "table_t" ]
    #aconsts = [
    #    # q3_ui/ui_specifyleague.c
    #    [ "table_t", "buff", ["MAX_LISTBOX_WIDTH_SPECIFY"] ],
    #    [ "table_t", "leaguename", ["MAX_LEAGUENAME"] ],
    #]
    #structNewNames = { "table_t" : "table_t_specifyleague" }
    #struct_info(cfile, structs, aconsts, useOffset, structNewNames=structNewNames)

    cfile = os.path.join("q3_ui", "ui_specifyserver.c")
    structs = [ "specifyserver_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_splevel.c")
    structs = [ "levelMenuInfo_t" ]
    aconsts = [
        # q3_ui/ui_splevel.c
        [ "levelMenuInfo_t", "levelPicNames", ["4", "MAX_QPATH"] ],
        [ "levelMenuInfo_t", "playerModel", ["MAX_QPATH"] ],
        [ "levelMenuInfo_t", "playerPicName", ["MAX_QPATH"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_sppostgame.c")
    structs = [ "postgameMenuInfo_t" ]
    aconsts = [
        # q3_ui/ui_sppostgame.c
        [ "postgameMenuInfo_t", "clientNums", ["MAX_SCOREBOARD_CLIENTS"] ],
        [ "postgameMenuInfo_t", "ranks", ["MAX_SCOREBOARD_CLIENTS"] ],
        [ "postgameMenuInfo_t", "scores", ["MAX_SCOREBOARD_CLIENTS"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_spreset.c")
    structs = [ "resetMenu_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_spskill.c")
    structs = [ "skillMenuInfo_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_startserver.c")
    structs = [ "startserver_t", "serveroptions_t", "botSelectInfo_t" ]
    aconsts = [
        # q3_ui/ui_startserver.c
        [ "startserver_t", "mappics", ["MAX_MAPSPERPAGE"] ],
        [ "startserver_t", "mapbuttons", ["MAX_MAPSPERPAGE"] ],
        [ "startserver_t", "maplist", ["MAX_SERVERMAPS", "MAX_NAMELENGTH_START_SERVER"] ],
        [ "startserver_t", "mapGamebits", ["MAX_SERVERMAPS"] ],
        [ "serveroptions_t", "playerType", ["PLAYER_SLOTS"] ],
        [ "serveroptions_t", "playerName", ["PLAYER_SLOTS"] ],
        [ "serveroptions_t", "playerTeam", ["PLAYER_SLOTS"] ],
        [ "serveroptions_t", "playerNameBuffers", ["PLAYER_SLOTS", "16"] ],
        [ "botSelectInfo_t", "pics", ["MAX_MODELSPERPAGE"] ],
        [ "botSelectInfo_t", "picbuttons", ["MAX_MODELSPERPAGE"] ],
        [ "botSelectInfo_t", "picnames", ["MAX_MODELSPERPAGE"] ],
        [ "botSelectInfo_t", "sortedBotNums", ["MAX_BOTS"] ],
        [ "botSelectInfo_t", "boticons", ["MAX_MODELSPERPAGE", "MAX_QPATH"] ],
        [ "botSelectInfo_t", "botnames", ["MAX_MODELSPERPAGE", "16"] ],
    ]
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_team.c")
    structs = [ "teammain_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_teamorders.c")
    structs = [ "teamOrdersMenuInfo_t" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

    cfile = os.path.join("q3_ui", "ui_video.c")
    structs = [ "driverinfo_t", "graphicsoptions_t", "InitialVideoOptions_s" ]
    aconsts = []
    struct_info(cfile, structs, aconsts, useOffset)

if __name__ == "__main__":
    main()
