#include "adc_sensor.h"
#include "stm32f4xx_hal.h"

extern ADC_HandleTypeDef hadc1;

/*
 * ADC1 must be configured in CubeMX with:
 *   - Scan conversion mode: enabled
 *   - Channel rank 1: PA0 (temperature)
 *   - Channel rank 2: PA1 (voltage)
 *   - Channel rank 3: PA4 (current)
 * One HAL_ADC_Start triggers all three in sequence.
 */
void ADC_ReadSensors(uint16_t *temp_raw,
                     uint16_t *volt_raw,
                     uint16_t *curr_raw)
{
    HAL_ADC_Start(&hadc1);

    HAL_ADC_PollForConversion(&hadc1, 10);
    *temp_raw = HAL_ADC_GetValue(&hadc1);

    HAL_ADC_PollForConversion(&hadc1, 10);
    *volt_raw = HAL_ADC_GetValue(&hadc1);

    HAL_ADC_PollForConversion(&hadc1, 10);
    *curr_raw = HAL_ADC_GetValue(&hadc1);

    HAL_ADC_Stop(&hadc1);
}
