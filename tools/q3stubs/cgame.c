
// gcc -Wall -c -m32 cgame.c -o cgame.o

#include "code/cgame/cg_local.h"

#include "common.c"

centity_t cg_entities[MAX_GENTITIES];
itemInfo_t cg_items[MAX_ITEMS];
weaponInfo_t cg_weapons[MAX_WEAPONS];

// cg_draw.c

int drawTeamOverlayModificationCount = -1;

int sortedTeamPlayers[TEAM_MAXOVERLAY];
int numSortedTeamPlayers;

cg_t cg;
cgs_t cgs;

vmCvar_t cg_addMarks;

vmCvar_t cg_buildScript;

vmCvar_t cg_cameraOrbit;
vmCvar_t cg_centertime;

vmCvar_t cg_crosshairHealth;
vmCvar_t cg_crosshairSize;
vmCvar_t cg_crosshairX;
vmCvar_t cg_crosshairY;

vmCvar_t cg_draw2D;
vmCvar_t cg_draw3dIcons;
vmCvar_t cg_drawAmmoWarning;
vmCvar_t cg_drawAttacker;
vmCvar_t cg_drawCrosshair;
vmCvar_t cg_drawCrosshairNames;

vmCvar_t cg_drawFPS;
vmCvar_t cg_drawIcons;
vmCvar_t cg_drawRewards;
vmCvar_t cg_drawSnapshot;
vmCvar_t cg_drawStatus;
vmCvar_t cg_drawTeamOverlay;
vmCvar_t cg_drawTimer;

vmCvar_t cg_lagometer;

vmCvar_t cg_nopredict;

vmCvar_t cg_showmiss;
vmCvar_t cg_stereoSeparation;
vmCvar_t cg_synchronousClients;

vmCvar_t cg_teamChatHeight;
vmCvar_t cg_teamChatsOnly;
vmCvar_t cg_teamChatTime;

vmCvar_t cg_viewsize;


// cg_syscalls.c
void trap_AddCommand (const char *cmdName) {}
int trap_Argc (void) { return 0; }
void trap_Args (char *buffer, int bufferLength) {}
void trap_Argv (int n, char *buffer, int bufferLength) {}

void trap_CM_LoadMap (const char *mapname) {}
int trap_CM_MarkFragments (int numPoints, const vec3_t *points, const vec3_t projection, int maxPoints, vec3_t pointBuffer, int maxFragments, markFragment_t *fragmentBuffer) { return 0; }
int trap_CM_NumInlineModels (void) { return 0; }
int trap_CM_PointContents (const vec3_t p, clipHandle_t model) { return 0; }

void trap_Cvar_Register (vmCvar_t *vmCvar, const char *varName, const char *defaultValue, int flags) {}
void trap_Cvar_Set (const char *var_name, const char *value) {}
void trap_Cvar_Update (vmCvar_t *vmCvar) {}
void trap_Cvar_VariableStringBuffer( const char *var_name, char *buffer, int bufsize ) {}

void trap_Error (const char *fmt) {}

void trap_FS_FCloseFile (fileHandle_t f) {}
int trap_FS_FOpenFile (const char *qpath, fileHandle_t *f, fsMode_t mode) { return 0; }
void trap_FS_Read (void *buffer, int len, fileHandle_t f) {}

int trap_GetCurrentCmdNumber (void) { return 0; }
void trap_GetGameState (gameState_t *gamestate) {}
void trap_GetGlconfig (glconfig_t *glconfig) {}
qboolean trap_GetUserCmd (int cmdNumber, usercmd_t *ucmd) { return qfalse; }
qboolean trap_GetServerCommand (int serverCommandNumber) { return qfalse; }

int trap_MemoryRemaining (void) { return 0; }
int trap_Milliseconds (void) { return 0; }

void trap_Print (const char *fmt) {}

void trap_R_AddPolyToScene (qhandle_t hShader, int numVerts, const polyVert_t *verts) {}
void trap_R_AddRefEntityToScene (const refEntity_t *re) {}
void trap_R_ClearScene (void) {}

void trap_R_DrawStretchPic (float x, float y, float w, float h, float s1, float t1, float s2, float t2, qhandle_t hShader) {}

void trap_R_LoadWorldMap (const char *mapname) {}
void trap_R_ModelBounds (clipHandle_t model, vec3_t mins, vec3_t maxs) {}

qhandle_t trap_R_RegisterModel (const char *name) { return 0; }
qhandle_t trap_R_RegisterSkin (const char *name) { return 0; }
qhandle_t trap_R_RegisterShader (const char *name) { return 0; }
qhandle_t trap_R_RegisterShaderNoMip (const char *name) { return 0; }

void trap_R_RemapShader (const char *oldShader, const char *newShader, const char *timeOffset) {}
void trap_R_RenderScene (const refdef_t *fd) {}
void trap_R_SetColor (const float *rgba) {}

void trap_S_ClearLoopingSounds( qboolean killall ) {}
sfxHandle_t trap_S_RegisterSound (const char *sample, qboolean compressed) { return 0; }
void trap_S_StartBackgroundTrack (const char *intro, const char *loop) {}
void trap_S_StartLocalSound (sfxHandle_t sfx, int channelNum) {}

void trap_SendClientCommand (const char *s) {}
void trap_SendConsoleCommand (const char *text) {}


void CG_AdjustFrom640 (float *x, float *y, float *w, float *h) {}

const char *CG_Argv (int arg) { return ""; }

void CG_BuildSpectatorString (void) {}

void CG_CenterPrint (const char *str, int y, int charWidth) {}

void CG_ClearParticles (void) {}

void CG_ColorForHealth (vec4_t hcolor) {}
const char *CG_ConfigString (int index) { return ""; }
qboolean CG_ConsoleCommand (void) { return 0; }
int CG_CrosshairPlayer (void) { return 0; }

void CG_DrawActiveFrame (int serverTime, stereoFrame_t stereoView, qboolean demoPlayback) {}
void CG_DrawBigString (int x, int y,  const char *s, float alpha) {}

void CG_DrawInformation (void) {}

qboolean CG_DrawOldScoreboard (void) { return qfalse; }
void CG_DrawOldTourneyScoreboard (void) {}

void CG_DrawPic (float x, float y, float width, float height, qhandle_t hShader) {}

void CG_DrawSmallString (int x, int y, const char *s, float alpha) {}

void CG_DrawStringExt (int x, int y, const char *string, const float *setColor, qboolean forceColor, qboolean shadow, int charWidth, int charHeight, int maxChars) {}
int CG_DrawStrlen (const char *str) { return 0; }

void CG_DrawWeaponSelect (void) {}

void CG_Error (const char *msg, ...) {}

float *CG_FadeColor (int startMsec, int totalMsec) { return NULL; }
void CG_FillRect (float x, float y, float width, float height, const float *color) {}

void CG_GetColorForHealth (int health, int armor, vec4_t hcolor) {}

void CG_InitConsoleCommands (void) {}
void CG_InitLocalEntities (void) {}
void CG_InitMarkPolys (void) {}
int CG_LastAttacker (void) { return 0; }

void CG_LoadDeferredPlayers (void) {}
void CG_LoadingClient (int clientNum) {}
void CG_LoadingItem (int itemNum) {}
void CG_LoadingString (const char *s) {}

void CG_NewClientInfo (int clientNum) {}
void CG_NextWeapon_f (void) {}

void CG_ParseServerinfo (void) {}
void CG_PrevWeapon_f (void) {}

void CG_Printf (const char *msg, ...) {}

void CG_RegisterItemVisuals (int itemNum) {}

void CG_SetConfigValues (void) {}
void CG_ShaderStateChanged (void) {}
void CG_StartMusic (void) {}

void CG_TestGun_f (void) {}
void CG_TestModel_f (void) {}
void CG_TestModelNextFrame_f (void) {}
void CG_TestModelPrevFrame_f (void) {}
void CG_TestModelNextSkin_f (void) {}
void CG_TestModelPrevSkin_f (void) {}

void CG_TileClear (void) {}
void CG_Trace (trace_t *result, const vec3_t start, const vec3_t mins, const vec3_t maxs, const vec3_t end, int skipNumber, int mask) {}

void CG_Weapon_f (void) {}

void CG_ZoomDown_f (void) {}
void CG_ZoomUp_f (void) {}
