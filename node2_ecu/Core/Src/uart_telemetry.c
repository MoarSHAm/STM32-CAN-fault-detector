#include "uart_telemetry.h"
#include "stm32f4xx_hal.h"
#include <stdio.h>

extern UART_HandleTypeDef huart2;

/*
 * Wire format (architecture doc §7):
 *   T,<timestamp_ms>,<can_id_hex>,<val1_raw>,<val2_raw>,<fault_hex>\r\n
 *
 * val1/val2 meaning depends on CAN ID:
 *   0x100 → val1=temp_raw,  val2=volt_raw
 *   0x101 → val1=curr_raw,  val2=0
 *   0x200 → val1=0,         val2=0  (fault frame, flags in fault field)
 */
void UART_Telemetry_Send(TelemetryData_t *telemetry)
{
    char    txbuf[128];
    uint16_t v1 = 0, v2 = 0;

    switch (telemetry->last_rx_id)
    {
        case 0x100:
            v1 = telemetry->temp_raw;
            v2 = telemetry->volt_raw;
            break;
        case 0x101:
            v1 = telemetry->curr_raw;
            v2 = 0;
            break;
        default:
            v1 = 0;
            v2 = 0;
            break;
    }

    int len = snprintf(txbuf, sizeof(txbuf),
                       "T,%lu,0x%03X,%u,%u,0x%02X\r\n",
                       HAL_GetTick(),
                       telemetry->last_rx_id,
                       v1,
                       v2,
                       telemetry->fault_flags);

    if (len > 0)
        HAL_UART_Transmit(&huart2, (uint8_t *)txbuf, (uint16_t)len, 100);
}
