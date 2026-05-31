#pragma once
#include <stdint.h>

/* ── CAN Message IDs ─────────────────────────────── */
#define CAN_ID_TEMP_VOLT    0x100U
#define CAN_ID_CURRENT      0x101U
#define CAN_ID_FAULT        0x200U

/* ── Payload structs (big-endian on wire) ─────────── */
typedef struct {
    uint16_t temp_raw;
    uint16_t voltage_raw;
    uint8_t  reserved[4];
} __attribute__((packed)) Frame_TempVolt_t;

typedef struct {
    uint16_t current_raw;
    uint8_t  reserved[6];
} __attribute__((packed)) Frame_Current_t;

typedef struct {
    uint8_t  fault_flags;
    uint8_t  fault_count;
    uint8_t  reserved[6];
} __attribute__((packed)) Frame_Fault_t;

/* ── Fault bitmasks ───────────────────────────────── */
#define FAULT_TEMP_HIGH   (1U << 0)
#define FAULT_VOLT_LOW    (1U << 1)
#define FAULT_VOLT_HIGH   (1U << 2)
#define FAULT_CURR_HIGH   (1U << 3)
