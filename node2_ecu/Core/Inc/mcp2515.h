#ifndef MCP2515_H
#define MCP2515_H

#include "stm32f4xx_hal.h"
#include <stdint.h>
#include <stdbool.h>

#define MCP2515_MAX_DATA_LEN    8U

#ifndef MCP2515_OSC_HZ
#define MCP2515_OSC_HZ          8000000UL
#endif

typedef enum {
    MCP2515_OK           =  0,
    MCP2515_ERR          = -1,
    MCP2515_ERR_PARAM    = -2,
    MCP2515_ERR_TIMEOUT  = -3,
    MCP2515_ERR_BUSY     = -4,
    MCP2515_ERR_NO_MSG   = -5
} MCP2515_Status_t;

typedef enum {
    MCP2515_MODE_NORMAL      = 0x00,
    MCP2515_MODE_SLEEP       = 0x20,
    MCP2515_MODE_LOOPBACK    = 0x40,
    MCP2515_MODE_LISTEN_ONLY = 0x60,
    MCP2515_MODE_CONFIG      = 0x80
} MCP2515_Mode_t;

typedef struct {
    SPI_HandleTypeDef *hspi;
    GPIO_TypeDef      *cs_port;
    uint16_t           cs_pin;
    GPIO_TypeDef      *int_port;
    uint16_t           int_pin;
    uint32_t           timeout_ms;
} MCP2515_Handle_t;

int  MCP2515_Init(MCP2515_Handle_t *h, uint32_t can_baud_kbps);
int  MCP2515_SetMode(MCP2515_Handle_t *h, MCP2515_Mode_t mode);
void MCP2515_Reset(MCP2515_Handle_t *h);
bool MCP2515_TxReady(MCP2515_Handle_t *h);
bool MCP2515_RxAvailable(MCP2515_Handle_t *h);
int  MCP2515_SendFrame(MCP2515_Handle_t *h, uint16_t id, const uint8_t *data, uint8_t len);
int  MCP2515_ReadFrame(MCP2515_Handle_t *h, uint16_t *id, uint8_t *data, uint8_t *len);
uint8_t MCP2515_ReadErrorFlags(MCP2515_Handle_t *h);

#endif /* MCP2515_H */
