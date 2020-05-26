
// gcc -Wall -c -m32 game.c -o game.o

#include "code/game/g_local.h"
#include "code/game/botlib.h"
#include "code/game/be_aas.h"
#include "code/game/be_ai_goal.h"
#include "code/game/ai_main.h"

#include "common.c"

gentity_t g_entities[MAX_GENTITIES];

void G_Error (const char *fmt, ...) {}
void G_Printf (const char *fmt, ...) {}

// ai_dmq3.c  g_main.c
bot_goal_t ctf_blueflag;
bot_goal_t ctf_redflag;

float floattime;
int gametype;
int maxclients;
int notleader[MAX_CLIENTS];

gentity_t *podium1;
gentity_t *podium2;
gentity_t *podium3;

level_locals_t level;

vmCvar_t bot_challenge;
vmCvar_t bot_fastchat;
vmCvar_t bot_grapple;
vmCvar_t bot_nochat;
vmCvar_t bot_rocketjump;
vmCvar_t bot_testrchat;

vmCvar_t g_banIPs;
vmCvar_t g_dedicated;
vmCvar_t g_doWarmup;
vmCvar_t g_filterBan;
vmCvar_t g_gametype;
vmCvar_t g_gravity;
vmCvar_t g_maxclients;
vmCvar_t g_motd;
vmCvar_t g_restarted;

void AddScore (gentity_t *ent, vec3_t origin, int score) {}

int BotAI_GetClientState (int clientNum, playerState_t *state) { return 0; }
void BotAI_BotInitialChat (bot_state_t *bs, char *type, ...) {}
int BotAILoadMap (int restart) { return 0; }
int BotAISetup (int restart) { return 0; }
int BotAISetupClient (int client, struct bot_settings_s *settings, qboolean restart) { return 0; }
int BotAIShutdown (int restart) { return 0; }
int BotAIStartFrame (int time) { return 0; }

int BotChat_ExitGame (bot_state_t *bs) { return 0; }
void BotChatTest (bot_state_t *bs) {}
void BotClearActivateGoalStack (bot_state_t *bs) {}
int BotCTFCarryingFlag (bot_state_t *bs) { return 0; }
void BotDeathmatchAI (bot_state_t *bs, float thinktime) {}

void BotEntityInfo (int entnum, aas_entityinfo_t *info) {}

void BotFreeWaypoints (bot_waypoint_t *wp) {}

int BotGetAlternateRouteGoal (bot_state_t *bs, int base) { return 0; }
int BotGetTeamMateTaskPreference(bot_state_t *bs, int teammate) { return 0; }

void BotInterbreedEndMatch (void) {}

int BotOppositeTeam (bot_state_t *bs) { return 0; }

int BotPointAreaNum (vec3_t origin) { return 0; }

void BotRememberLastOrderedTask (bot_state_t *bs) {}

int BotSameTeam (bot_state_t *bs, int entnum) { return 0; }

int BotSetLastOrderedTask (bot_state_t *bs) { return 0; }
void BotSetTeamMateTaskPreference (bot_state_t *bs, int teammate, int preference) {}
void BotSetTeamStatus (bot_state_t *bs) {}

void BotSetupDeathmatchAI (void) {}
int BotSynonymContext(bot_state_t *bs) { return 0; }

int BotTeam (bot_state_t *bs) { return 0; }
int BotTeamFlagCarrier (bot_state_t *bs) { return 0; }

void BotVoiceChat_Defend (bot_state_t *bs, int client, int mode) {}
void BotVoiceChatOnly (bot_state_t *bs, int toclient, char *voicechat) {}

void CalculateRanks (void) {}

void CheckTeamStatus (void) {}

void ClearRegisteredItems (void) {}

void ClientBegin (int clientNum) {}
void ClientCommand (int clientNum) {}
char *ClientConnect (int clientNum, qboolean firstTime, qboolean isBot) { return ""; }
void ClientDisconnect (int clientNum) {}
void ClientEndFrame (gentity_t *ent) {}
int ClientFromName (char *name) { return 0; }
char *ClientName (int client, char *name, int size) { return ""; }
void ClientThink (int clientNum) {}
void ClientUserinfoChanged (int clientNum) {}

char *ConcatArgs (int start) { return ""; }
qboolean ConsoleCommand (void) { return qfalse; }

void DeathmatchScoreboardMessage (gentity_t *ent) {}

char *EasyClientName (int client, char *buf, int size) { return ""; }

void ExitLevel (void) {}

void G_AddEvent (gentity_t *ent, int event, int eventParm) {}
void *G_Alloc (int size) { return NULL; }

void G_CheckBotSpawn (void) {}
void G_CheckTeamItems (void) {}

gentity_t *G_Find (gentity_t *from, int fieldofs, const char *match) { return NULL; }
void G_FreeEntity (gentity_t *ed) {}

void G_Damage (gentity_t *targ, gentity_t *inflictor, gentity_t *attacker, vec3_t dir, vec3_t point, int damage, int dflags, int mod) {}

void G_InitBots (qboolean restart) {}
void G_InitMemory (void) {}
void G_InitWorldSession (void) {}

void G_LogPrintf (const char *fmt, ...) {}

int G_ModelIndex (char *name) { return 0; }

gentity_t *G_PickTarget (char *targetname) { return NULL; }
void G_ProcessIPBans (void) {}

void G_RunClient (gentity_t *ent) {}
void G_RunItem (gentity_t *ent) {}
void G_RunMissile (gentity_t *ent) {}
void G_RunMover (gentity_t *ent) {}
void G_RunThink (gentity_t *ent) {}

void G_SetMovedir (vec3_t angles, vec3_t movedir) {}

int G_SoundIndex (char *name) { return 0; }

gentity_t *G_Spawn (void) { return NULL; }

void G_SpawnEntitiesFromString (void) {}

qboolean G_SpawnFloat (const char *key, const char *defaultString, float *out) { return qfalse; }
qboolean G_SpawnInt (const char *key, const char *defaultString, int *out) { return qfalse; }
void G_SpawnItem (gentity_t *ent, gitem_t *item) {}
qboolean G_SpawnString (const char *key, const char *defaultString, char **out) { return qfalse; }
qboolean G_SpawnVector (const char *key, const char *defaultString, float *out) { return qfalse; }

gentity_t *G_TempEntity (vec3_t origin, int event) { return NULL; }

void G_UseTargets (gentity_t *ent, gentity_t *activator) {}

void G_WriteSessionData (void) {}

void InitBodyQue (void) {}

team_t PickTeam (int ignoreClientNum) { return 0; }

void respawn (gentity_t *ent) {}

void RespawnItem (gentity_t *ent) {}

void SaveRegisteredItems (void) {}

gentity_t *SelectSpawnPoint (vec3_t avoidPoint, vec3_t origin, vec3_t angles) { return NULL; }

void SetTeam (gentity_t *ent, char *s) {}

void SpawnModelsOnVictoryPads (void) {}

void SP_info_player_start (gentity_t *ent) {}
void SP_info_player_deathmatch (gentity_t *ent) {}
void SP_info_player_intermission (gentity_t *ent) {}
void SP_info_firstplace(gentity_t *ent) {}
void SP_info_secondplace(gentity_t *ent) {}
void SP_info_thirdplace(gentity_t *ent) {}
void SP_info_podium(gentity_t *ent) {}

void SP_func_plat (gentity_t *ent) {}
void SP_func_static (gentity_t *ent) {}
void SP_func_rotating (gentity_t *ent) {}
void SP_func_bobbing (gentity_t *ent) {}
void SP_func_pendulum( gentity_t *ent ) {}
void SP_func_button (gentity_t *ent) {}
void SP_func_door (gentity_t *ent) {}
void SP_func_train (gentity_t *ent) {}
void SP_func_timer (gentity_t *self) {}

void SP_trigger_always (gentity_t *ent) {}
void SP_trigger_multiple (gentity_t *ent) {}
void SP_trigger_push (gentity_t *ent) {}
void SP_trigger_teleport (gentity_t *ent) {}
void SP_trigger_hurt (gentity_t *ent) {}

void SP_target_remove_powerups( gentity_t *ent ) {}
void SP_target_give (gentity_t *ent) {}
void SP_target_delay (gentity_t *ent) {}
void SP_target_speaker (gentity_t *ent) {}
void SP_target_print (gentity_t *ent) {}
void SP_target_laser (gentity_t *self) {}
void SP_target_character (gentity_t *ent) {}
void SP_target_score( gentity_t *ent ) {}
void SP_target_teleporter( gentity_t *ent ) {}
void SP_target_relay (gentity_t *ent) {}
void SP_target_kill (gentity_t *ent) {}
void SP_target_position (gentity_t *ent) {}
void SP_target_location (gentity_t *ent) {}
void SP_target_push (gentity_t *ent) {}

void SP_light (gentity_t *self) {}
void SP_info_null (gentity_t *self) {}
void SP_info_notnull (gentity_t *self) {}
void SP_info_camp (gentity_t *self) {}
void SP_path_corner (gentity_t *self) {}

void SP_misc_teleporter_dest (gentity_t *self) {}
void SP_misc_model(gentity_t *ent) {}
void SP_misc_portal_camera(gentity_t *ent) {}
void SP_misc_portal_surface(gentity_t *ent) {}

void SP_shooter_rocket( gentity_t *ent ) {}
void SP_shooter_plasma( gentity_t *ent ) {}
void SP_shooter_grenade( gentity_t *ent ) {}

void SP_team_CTF_redplayer( gentity_t *ent ) {}
void SP_team_CTF_blueplayer( gentity_t *ent ) {}

void SP_team_CTF_redspawn( gentity_t *ent ) {}
void SP_team_CTF_bluespawn( gentity_t *ent ) {}

//#ifdef MISSIONPACK
//void SP_team_blueobelisk( gentity_t *ent ) {}
//void SP_team_redobelisk( gentity_t *ent ) {}
//void SP_team_neutralobelisk( gentity_t *ent ) {}
//#endif

void SP_item_botroam( gentity_t *ent ) {}

qboolean SpotWouldTelefrag (gentity_t *spot) { return qfalse; }
void StopFollowing (gentity_t *ent) {}

void Svcmd_AbortPodium_f (void) {}
void Svcmd_AddBot_f (void) {}
void Svcmd_BotList_f (void) {}
void Svcmd_GameMem_f (void) {}

team_t TeamCount (int ignoreClientNum, int team) { return 0; }
void Team_DroppedFlagThink (gentity_t *ent) {}
int TeamPlayIsOn (void) { return 0; }

void TeleportPlayer (gentity_t *player, vec3_t origin, vec3_t angles) {}

void UpdateTournamentInfo (void) {}

char *vtos (const vec3_t v) { return ""; }

// g_syscalls.c

int trap_AAS_AreaInfo (int areanum, void *info) { return 0; }
int trap_AAS_AreaTravelTimeToGoalArea(int areanum, vec3_t origin, int goalareanum, int travelflags) { return 0; }
void trap_AAS_EntityInfo (int entnum, void *info) {}
int trap_AAS_Initialized (void) { return 0; }
float trap_AAS_Time (void) { return 0.0f; }

void trap_AdjustAreaPortalState( gentity_t *ent, qboolean open ) {}

int trap_Argc (void) { return 0; }
void trap_Argv (int n, char *buffer, int bufferLength) {}

int trap_BotAllocateClient (void) { return 0; }
int trap_BotAllocChatState (void) { return 0; }
int trap_BotAllocGoalState (int state) { return 0; }
int trap_BotAllocMoveState (void) { return 0; }
int trap_BotAllocWeaponState (void) { return 0; }

void trap_BotEnterChat (int chatstate, int client, int sendto) {}

void trap_BotFreeCharacter (int character) {}
void trap_BotFreeChatState (int handle) {}
void trap_BotFreeGoalState (int handle) {}
void trap_BotFreeMoveState (int handle) {}
void trap_BotFreeWeaponState (int weaponstate) {}

void trap_BotGetChatMessage (int chatstate, char *buf, int size) {}
int trap_BotGetServerCommand (int clientNum, char *message, int size) { return 0; }
int trap_BotGetSnapshotEntity (int clientNum, int sequence) { return 0; }
int trap_BotGetTopGoal (int goalstate, void *goal) { return 0; }

void trap_BotGoalName (int number, char *name, int size) {}
void trap_BotInitialChat(int chatstate, char *type, int mcontext, char *var0, char *var1, char *var2, char *var3, char *var4, char *var5, char *var6, char *var7 ) {}
void trap_BotInterbreedGoalFuzzyLogic(int parent1, int parent2, int child) {}

int trap_BotLibLoadMap (const char *mapname) { return 0; }
int trap_BotLibSetup (void) { return 0; }
int trap_BotLibShutdown (void) { return 0; }
int trap_BotLibStartFrame (float time) { return 0; }
int trap_BotLibUpdateEntity (int ent, void *bue) { return 0; }
int trap_BotLibVarSet (char *var_name, char *value) { return 0; }

int trap_BotLoadCharacter (char *charfile, float skill) { return 0; }
int trap_BotLoadChatFile (int chatstate, char *chatfile, char *chatname) { return 0; }
int trap_BotLoadItemWeights (int goalstate, char *filename) { return 0; }
int trap_BotLoadWeaponWeights (int weaponstate, char *filename) { return 0; }

void trap_BotMutateGoalFuzzyLogic(int goalstate, float range) {}

void trap_BotQueueConsoleMessage(int chatstate, int type, char *message) {}

void trap_BotResetAvoidGoals (int goalstate) {}
void trap_BotResetAvoidReach (int movestate) {}
void trap_BotResetGoalState (int goalstate) {}
void trap_BotResetMoveState (int movestate) {}
void trap_BotResetWeaponState (int weaponstate) {}

void trap_BotSetChatGender (int chatstate, int gender) {}

void trap_BotSaveGoalFuzzyLogic(int goalstate, char *filename) {}

void trap_BotUpdateEntityItems (void) {}
void trap_BotUserCommand (int clientNum, usercmd_t *ucmd) {}

float trap_Characteristic_BFloat(int character, int index, float min, float max) { return 0.0f; }
void trap_Characteristic_String(int character, int index, char *buf, int size) {}

void trap_Cvar_Register (vmCvar_t *cvar, const char *var_name, const char *value, int flags) {}
void trap_Cvar_Set (const char *var_name, const char *value) {}
void trap_Cvar_Update (vmCvar_t *cvar) {}
int trap_Cvar_VariableIntegerValue (const char *var_name) { return 0; }
void trap_Cvar_VariableStringBuffer( const char *var_name, char *buffer, int bufsize ) {}

int trap_DebugPolygonCreate(int color, int numPoints, vec3_t *points) { return 0; }

void trap_DropClient (int clientNum, const char *reason) {}

void trap_EA_Action (int client, int action) {}
void trap_EA_GetInput (int client, float thinktime, void *input) {}
void trap_EA_ResetInput (int client) {}
void trap_EA_SelectWeapon (int client, int weapon) {}
void trap_EA_View (int client, vec3_t viewangles) {}

int trap_EntitiesInBox( const vec3_t mins, const vec3_t maxs, int *list, int maxcount ) { return 0; }
void trap_Error (const char *fmt) {}

void trap_FS_FCloseFile (fileHandle_t f) {}
int trap_FS_FOpenFile (const char *qpath, fileHandle_t *f, fsMode_t mode) { return 0; }
int trap_FS_GetFileList(  const char *path, const char *extension, char *listbuf, int bufsize ) { return 0; }
void trap_FS_Read (void *buffer, int len, fileHandle_t f) {}
void trap_FS_Write (const void *buffer, int len, fileHandle_t f) {}

int trap_GeneticParentsAndChildSelection(int numranks, float *ranks, int *parent1, int *parent2, int *child) { return 0; }

void trap_GetConfigstring (int num, char *buffer, int bufferSize) {}
qboolean trap_GetEntityToken (char *buffer, int bufferSize) { return qfalse; }
void trap_GetServerinfo (char *buffer, int bufferSize) {}
void trap_GetUserinfo (int num, char *buffer, int bufferSize) {}

qboolean trap_InPVS (const vec3_t p1, const vec3_t p2) { return qfalse; }

void trap_LinkEntity (gentity_t *ent) {}
void trap_LocateGameData( gentity_t *gEnts, int numGEntities, int sizeofGEntity_t, playerState_t *clients, int sizeofGClient ) {}

int trap_Milliseconds (void) { return 0; }

void trap_Printf (const char *fmt) {}

void trap_SendConsoleCommand (int exec_when, const char *text) {}
void trap_SendServerCommand (int clientNum, const char *text) {}

void trap_SetBrushModel( gentity_t *ent, const char *name ) {}
void trap_SetConfigstring (int num, const char *string) {}
void trap_SetUserinfo (int num, const char *buffer) {}

void trap_SnapVector (float *v) {}

void trap_Trace( trace_t *results, const vec3_t start, const vec3_t mins, const vec3_t maxs, const vec3_t end, int passEntityNum, int contentmask ) {}

void trap_UnlinkEntity (gentity_t *ent) {}
