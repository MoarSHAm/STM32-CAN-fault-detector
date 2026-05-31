#ifndef TELEMETRY_H
#define TELEMETRY_H

#include <stdint.h>

typedef struct {
    uint16_t temp_raw;
    uint16_t volt_raw;
    uint16_t curr_raw;
    uint8_t  fault_flags;
    uint16_t last_rx_id;
} TelemetryData_t;

#endif /* TELEMETRY_H */
