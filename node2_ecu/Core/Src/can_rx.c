#include "can_rx.h"
#include "can_frame_def.h"

bool CAN_RX_ProcessFrame(uint16_t id,
                          uint8_t *data,
                          uint8_t  len,
                          TelemetryData_t *telemetry)
{
    (void)len; /* length already validated by MCP2515 driver */

    telemetry->last_rx_id = id;

    switch (id)
    {
        case CAN_ID_TEMP_VOLT:
            telemetry->temp_raw = ((uint16_t)data[0] << 8) | data[1];
            telemetry->volt_raw = ((uint16_t)data[2] << 8) | data[3];
            return true;

        case CAN_ID_CURRENT:
            telemetry->curr_raw = ((uint16_t)data[0] << 8) | data[1];
            return true;

        default:
            return false;
    }
}
