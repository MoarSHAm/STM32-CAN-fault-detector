#ifndef CAN_TX_H
#define CAN_TX_H

#include "mcp2515.h"
#include <stdint.h>

void CAN_TX_Init(MCP2515_Handle_t *h);
int  CAN_TX_SendTempVolt(uint16_t temp_raw, uint16_t volt_raw);
int  CAN_TX_SendCurrent(uint16_t curr_raw);

#endif /* CAN_TX_H */
