#ifndef ADC_SENSOR_H
#define ADC_SENSOR_H

#include <stdint.h>

void ADC_ReadSensors(uint16_t *temp_raw,
                     uint16_t *volt_raw,
                     uint16_t *curr_raw);

#endif /* ADC_SENSOR_H */
