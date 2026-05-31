#ifndef CAN_RX_H
#define CAN_RX_H

#include <stdint.h>
#include <stdbool.h>
#include "telemetry.h"

bool CAN_RX_ProcessFrame(uint16_t id,
                          uint8_t *data,
                          uint8_t  len,
                          TelemetryData_t *telemetry);

#endif /* CAN_RX_H */
