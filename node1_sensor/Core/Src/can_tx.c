#include "can_tx.h"
#include "can_frame_def.h"

static MCP2515_Handle_t *s_handle;

void CAN_TX_Init(MCP2515_Handle_t *h)
{
    s_handle = h;
}

int CAN_TX_SendTempVolt(uint16_t temp_raw, uint16_t volt_raw)
{
    uint8_t frame[8] = {
        (uint8_t)(temp_raw >> 8),
        (uint8_t)(temp_raw & 0xFF),
        (uint8_t)(volt_raw >> 8),
        (uint8_t)(volt_raw & 0xFF),
        0x00, 0x00, 0x00, 0x00
    };
    return MCP2515_SendFrame(s_handle, CAN_ID_TEMP_VOLT, frame, 8);
}

int CAN_TX_SendCurrent(uint16_t curr_raw)
{
    uint8_t frame[8] = {
        (uint8_t)(curr_raw >> 8),
        (uint8_t)(curr_raw & 0xFF),
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    };
    return MCP2515_SendFrame(s_handle, CAN_ID_CURRENT, frame, 8);
}
