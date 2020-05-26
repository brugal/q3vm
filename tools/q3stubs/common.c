
// bg_misc.c
gitem_t bg_itemlist[] =
{
        {
                NULL,
                NULL,
                { NULL,
                NULL,
                0, 0} ,
/* icon */              NULL,
/* pickup */    NULL,
                0,
                0,
                0,
/* precache */ "",
/* sounds */ ""
        },      // leave index 0 alone
};

int bg_numItems = 1;

void BG_AddPredictableEventToPlayerstate( int newEvent, int eventParm, playerState_t *ps ) {}

void BG_EvaluateTrajectory( const trajectory_t *tr, int atTime, vec3_t result ) {}

gitem_t *BG_FindItemForPowerup (powerup_t pw) { return NULL; }

double atan2 (double y, double x) { return 0.0; }
double cos (double x) { return 0.0; }
double floor (double x) { return 0.0; }
double sin (double x)  { return 0.0; }
double sqrt (double x) { return 0.0; }

qboolean PM_SlideMove (qboolean gravity) { return qfalse; }
void PM_StepSlideMove (qboolean gravity) {}

// COM_

char *COM_Parse (char **data_p) { return NULL; }
char *COM_ParseExt (char **data_p, qboolean allowLineBreak) { return NULL; }

void COM_StripExtension (const char *in, char *out) {}

float Com_Clamp (float min, float max, float value) { return 0.0f; }

void Com_Error (int code, const char *fmt, ...) {}

void Com_Printf (const char *fmt, ...) {}

void Com_sprintf (char *dest, int size, const char *fmt, ...) {}

// q_math.c

vec4_t colorBlack = { 0, 0, 0, 1 };
vec4_t colorRed = { 1, 0, 0, 1 };
vec4_t colorWhite = { 1, 1, 1, 1 };

vec4_t g_color_table[8];
vec3_t vec3_origin = { 0, 0, 0 };

void AddPointToBounds (const vec3_t v, vec3_t mins, vec3_t maxs) {}
float AngleMod (float a) { return 0.0f; }
void AnglesToAxis (const vec3_t angles, vec3_t axis[3]) {}
void AngleVectors (const vec3_t angles, vec3_t forward, vec3_t right, vec3_t up) {}
void AxisClear (vec3_t axis[3]) {}

void Info_NextPair (const char **s, char *key, char *value) {}
void Info_SetValueForKey( char *s, const char *key, const char *value ) {}
void Info_SetValueForKey_Big( char *s, const char *key, const char *value ) {}
char *Info_ValueForKey (const char *s, const char *key) { return ""; }

void PerpendicularVector (vec3_t dst, const vec3_t src) {}

char *Q_CleanStr (char *string) { return ""; }
int Q_PrintStrlen (const char *string) { return 0; }
int Q_stricmp (const char *s1, const char *s2) { return 0; }
int Q_stricmpn (const char *s1, const char *s2, int n) { return 0; }
int Q_strncmp (const char *s1, const char *s2, int n) { return 0; }
void Q_strncpyz( char *dest, const char *src, int destsize ) {}
void Q_strcat( char *dest, int size, const char *src ) {}
char *Q_strupr (char *s1) { return ""; }
char *Q_strrchr (const char *string, int c) { return ""; }

float RadiusFromBounds (const vec3_t mins, const vec3_t maxs) { return 0.0f; }
void RotateAroundDirection (vec3_t axis[3], float yaw) {}
void RotatePointAroundVector( vec3_t dst, const vec3_t dir, const vec3_t point, float degrees ) {}

char *va (char *format, ...) { return ""; }

void vectoangles (const vec3_t value1, vec3_t angles) {}

vec_t VectorNormalize (vec3_t v) { return 0.0f; }
vec_t VectorNormalize2 (const vec3_t v, vec3_t out) { return 0.0f; }
