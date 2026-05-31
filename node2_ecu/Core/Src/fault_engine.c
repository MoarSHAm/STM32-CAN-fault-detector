#include "fault_engine.h"
#include "thresholds.h"
#include "can_frame_def.h"

/*
 * Thresholds are compared against raw ADC counts.
 * Derivation documented in thresholds.h.
 * To switch to engineering-unit comparison, apply
 * the conversion formulas from thresholds.h first.
 */
void FaultEngine_Update(TelemetryData_t *telemetry)
{
    telemetry->fault_flags = 0;

    if (telemetry->temp_raw > TEMP_MAX_RAW)
        telemetry->fault_flags |= FAULT_TEMP_HIGH;

    if (telemetry->volt_raw < VOLT_MIN_RAW)
        telemetry->fault_flags |= FAULT_VOLT_LOW;

    if (telemetry->volt_raw > VOLT_MAX_RAW)
        telemetry->fault_flags |= FAULT_VOLT_HIGH;

    if (telemetry->curr_raw > CURR_MAX_RAW)
        telemetry->fault_flags |= FAULT_CURR_HIGH;
}
