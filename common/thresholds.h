#pragma once

/* ── Engineering-unit thresholds ─────────────────── */
#define THRESH_TEMP_MAX_C     60.0f
#define THRESH_VOLT_MIN_V      3.0f
#define THRESH_VOLT_MAX_V      4.2f
#define THRESH_CURR_MAX_A      5.0f

/* ── ADC conversion constants ────────────────────── */
#define ADC_FULLSCALE        4095.0f
#define ADC_VREF_V             3.3f

/* ── LM35: 10 mV/°C, 3.3 V ref ──────────────────── */
#define LM35_MV_PER_C         10.0f

/* ── ACS712-5A: 2.5 V zero, 185 mV/A ────────────── */
#define ACS712_ZERO_V          2.5f
#define ACS712_MV_PER_A      185.0f

/* ── Voltage divider ratio (R1+R2)/R2 ───────────── */
#define VDIV_RATIO             2.0f

/* ── Raw ADC threshold equivalents ──────────────── *
 * Derived from conversion formulas — do not edit    *
 * these without updating the formulas below.        *
 *                                                   *
 * temp_C  = (raw/4095) * 3.3 * 100                 *
 *   → TEMP_MAX_RAW = 60 / (3.3*100/4095) = 744     *
 *                                                   *
 * volt_V  = (raw/4095) * 3.3 * VDIV_RATIO          *
 *   → VOLT_MIN_RAW = 3.0 / (3.3*2/4095) = 1860     *
 *   → VOLT_MAX_RAW = 4.2 / (3.3*2/4095) = 2604     *
 *                                                   *
 * curr_A  = ((raw/4095)*3.3 - 2.5) / 0.185         *
 *   → CURR_MAX_RAW = (5*0.185+2.5)/(3.3/4095)=3779 *
 * ────────────────────────────────────────────────── */
#define TEMP_MAX_RAW    744U
#define VOLT_MIN_RAW   1860U
#define VOLT_MAX_RAW   2604U
#define CURR_MAX_RAW   3779U
