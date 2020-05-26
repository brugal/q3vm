
// gcc -Wall -c -m32 q3_ui.c -o q3_ui.o

#include "code/q3_ui/ui_local.h"

#include "common.c"

vec4_t color_black = { 0.00f, 0.00f, 0.00f, 1.00f };
vec4_t color_orange = { 1.00f, 0.43f, 0.00f, 1.00f };
vec4_t color_red = { 1.00f, 0.00f, 0.00f, 1.00f };
vec4_t color_white = { 1.00f, 1.00f, 1.00f, 1.00f };
vec4_t color_yellow = { 1.00f, 1.00f, 0.00f, 1.00f };

vec4_t listbar_color = { 1.00f, 0.43f, 0.00f, 0.30f };

vec4_t menu_text_color = { 1.0f, 1.0f, 1.0f, 1.0f };

vec4_t text_color_disabled = { 0.50f, 0.50f, 0.50f, 1.00f };
vec4_t text_color_highlight = { 1.00f, 1.00f, 0.00f, 1.00f };
vec4_t text_color_normal = { 1.00f, 0.43f, 0.00f, 1.00f };

sfxHandle_t menu_buzz_sound;
sfxHandle_t menu_move_sound;
sfxHandle_t menu_null_sound;
sfxHandle_t menu_out_sound;

vmCvar_t ui_browserGameType;
vmCvar_t ui_browserMaster;
vmCvar_t ui_browserShowEmpty;
vmCvar_t ui_browserShowFull;
vmCvar_t ui_browserSortKey;
vmCvar_t ui_cdkeychecked;

const char *punkbuster_items[] = { "" };

char *ui_medalPicNames[] = { "" };
char *ui_medalSounds[] = { "" };

uiStatic_t uis;

void Bitmap_Draw (menubitmap_s *b) {}
void Bitmap_Init (menubitmap_s *b) {}

void Menu_AddItem (menuframework_s *menu, void *item) {}
void *Menu_ItemAtCursor (menuframework_s *m) { return NULL; }
sfxHandle_t Menu_DefaultKey (menuframework_s *s, int key) { return 0; }
void Menu_Draw (menuframework_s *menu) {}
void Menu_SetCursor (menuframework_s *s, int cursor) {}
void Menu_SetCursorToItem (menuframework_s *m, void *ptr) {}

void MField_Draw (mfield_t *edit, int x, int y, int style, vec4_t color) {}

sfxHandle_t ScrollList_Key (menulist_s *l, int key) { return 0; }

void UI_AddBotsMenu (void) {}
void UI_AdjustFrom640 (float *x, float *y, float *w, float *h) {}
void UI_ArenaServersMenu (void) {}
char *UI_Argv (int arg) { return ""; }

qboolean UI_CanShowTierVideo (int tier) { return qfalse; }
void UI_CDKeyMenu (void) {}
void UI_CinematicsMenu (void) {}
float UI_ClampCvar (float min, float max, float value) { return 0.0f; }
void UI_ConfirmMenu (const char *question, void (*draw)(void), void (*action)(qboolean result)) {}
void UI_ConfirmMenu_Style (const char *question, int style, void (*draw)(void), void (*action)(qboolean result)) {}
qboolean UI_ConsoleCommand (int realTime) { return qfalse; }
void UI_ControlsMenu (void) {}
void UI_CreditMenu (void) {}
qboolean UI_CursorInRect (int x, int y, int width, int height) { return qfalse; }
char *UI_Cvar_VariableString (const char *var_name) { return ""; }

void UI_DemosMenu (void) {}
void UI_DisplayOptionsMenu (void) {}

void UI_DrawBannerString (int x, int y, const char *str, int style, vec4_t color) {}
void UI_DrawChar (int x, int y, int ch, int style, vec4_t color) {}
void UI_DrawConnectScreen (qboolean overlay) {}
void UI_DrawHandlePic (float x, float y, float w, float h, qhandle_t hShader) {}
void UI_DrawNamedPic (float x, float y, float width, float height, const char *picname) {}
void UI_DrawPlayer (float x, float y, float w, float h, playerInfo_t *pi, int time) {}
void UI_DrawProportionalString (int x, int y, const char *str, int style, vec4_t color) {}
void UI_DrawProportionalString_AutoWrapped( int x, int ystart, int xmax, int ystep, const char* str, int style, vec4_t color ) {}
void UI_DrawString (int x, int y, const char *str, int style, vec4_t color) {}

void UI_FillRect (float x, float y, float width, float height, const float *color) {}
void UI_ForceMenuOff (void) {}

const char *UI_GetArenaInfoByMap (const char *map) { return ""; }
const char *UI_GetArenaInfoByNumber (int num) { return ""; }
int UI_GetAwardLevel (int award) { return 0; }
void UI_GetBestScore (int level, int *score, int *skill) {}
char *UI_GetBotInfoByName (const char *name) { return ""; }
char *UI_GetBotInfoByNumber (int num) { return ""; }
int UI_GetCurrentGame (void) { return 0; }
int UI_GetNumArenas (void) { return 0; }
int UI_GetNumBots (void) { return 0; }
int UI_GetNumSPArenas (void) { return 0; }
int UI_GetNumSPTiers (void) { return 0; }
const char *UI_GetSpecialArenaInfo (const char *tag) { return ""; }

void UI_GraphicsOptionsMenu (void) {}

void UI_Init (void) {}
qboolean UI_IsFullscreen (void) { return qfalse; }

void UI_KeyEvent (int key, int down) {}

void UI_LogAwardData (int award, int data) {}

void UI_Message (const char **lines) {}
void UI_ModsMenu (void) {}
void UI_MouseEvent (int dx, int dy) {}

void UI_NetworkOptionsMenu (void) {}
void UI_NewGame (void) {}

void UI_PlayerInfo_SetInfo (playerInfo_t *pi, int legsAnim, int torsoAnim, vec3_t viewAngles, vec3_t moveAngles, weapon_t weaponNum, qboolean chat) {}
void UI_PlayerInfo_SetModel (playerInfo_t *pi, const char *model) {}

void UI_PlayerModelMenu (void) {}
void UI_PlayerSettingsMenu (void) {}

void UI_PopMenu (void) {}
void UI_PreferencesMenu (void) {}
int UI_ProportionalStringWidth (const char *str) { return 0; }
void UI_PushMenu (menuframework_s *menu) {}

void UI_Refresh (int realtime) {}
void UI_RemoveBotsMenu (void) {}

void UI_ServerInfoMenu (void) {}
void UI_SetActiveMenu (uiMenuCommand_t menu) {}
void UI_SetBestScore (int level, int score) {}
void UI_SetupMenu (void) {}
qboolean UI_ShowTierVideo (int tier) { return qfalse; }
void UI_Shutdown (void) {}
void UI_SoundOptionsMenu (void) {}
void UI_SpecifyServerMenu (void) {}
void UI_SPArena_Start (const char *arenaInfo) {}
void UI_SPLevelMenu (void) {}
void UI_SPSkillMenu (const char *arenaInfo) {}
void UI_StartServerMenu (qboolean multiplayer) {}

void UI_TeamMainMenu (void) {}
void UI_TeamOrdersMenu (void) {}

int UI_TierCompleted (int levelWon) { return 0; }

// ui_syscalls.c

void trap_Cmd_ExecuteText (int exec_when, const char *text) {}

void trap_Cvar_Register (vmCvar_t *cvar, const char *var_name, const char *value, int flags) {}
void trap_Cvar_Reset (const char *name) {}
void trap_Cvar_Set (const char *var_name, const char *value) {}
void trap_Cvar_SetValue (const char *var_name, float value) {}
void trap_Cvar_Update (vmCvar_t *cvar) {}
void trap_Cvar_VariableStringBuffer (const char *var_name, char *buffer, int bufsize) {}
float trap_Cvar_VariableValue (const char *var_name) { return 0.0f; }

int trap_FS_GetFileList (const char *path, const char *extension, char *listbuf, int bufsize) { return 0; }

void trap_GetCDKey (char *buf, int buflen) {}
void trap_GetClientState (uiClientState_t *state) {}
int trap_GetConfigString (int index, char *buff, int buffsize) { return 0; }

void trap_Key_GetBindingBuf (int keynum, char *buf, int buflen) {}
qboolean trap_Key_GetOverstrikeMode (void) { return qfalse; }
void trap_Key_KeynumToStringBuf (int keynum, char *buf, int buflen) {}
void trap_Key_SetBinding (int keynum, const char *binding) {}
void trap_Key_SetCatcher (int catcher) {}

void trap_LAN_ClearPing (int n) {}
void trap_LAN_GetPing (int n, char *buf, int buflen, int *pingtime) {}
void trap_LAN_GetPingInfo (int n, char *buf, int buflen) {}
int trap_LAN_GetPingQueueCount (void) { return 0; }
void trap_LAN_GetServerAddressString (int source, int n, char *buf, int buflen) {}
int trap_LAN_GetServerCount (int source) { return 0; }

int trap_MemoryRemaining (void) { return 0; }

void trap_Print (const char *string) {}

void trap_R_AddRefEntityToScene (const refEntity_t *re) {}
void trap_R_ClearScene (void) {}
qhandle_t trap_R_RegisterModel (const char *name) { return 0; }
qhandle_t trap_R_RegisterShaderNoMip (const char *name) { return 0; }
void trap_R_RenderScene (const refdef_t *fd) {}
void trap_R_SetColor (const float *rgba) {}

sfxHandle_t trap_S_RegisterSound (const char *sample, qboolean compressed) { return 0; }
void trap_S_StartLocalSound (sfxHandle_t sfx, int channelNum) {}

void trap_SetCDKey (char *buf) {}
void trap_SetPbClStatus (int status) {}

qboolean trap_VerifyCDKey (const char *key, const char *chksum) { return qfalse; }

