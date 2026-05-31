#include "mcp2515.h"

/* ── SPI command bytes ───────────────────────────── */
#define MCP_RESET_CMD   0xC0
#define MCP_READ_CMD    0x03
#define MCP_WRITE_CMD   0x02
#define MCP_BITMOD_CMD  0x05
#define MCP_RTS_TXB0    0x81

/* ── Register addresses ──────────────────────────── */
#define CANSTAT         0x0E
#define CANCTRL         0x0F
#define CNF3            0x28
#define CNF2            0x29
#define CNF1            0x2A
#define CANINTE         0x2B
#define CANINTF         0x2C
#define EFLG            0x2D
#define TXB0CTRL        0x30
#define TXB0SIDH        0x31
#define TXB0SIDL        0x32
#define TXB0DLC         0x35
#define TXB0D0          0x36
#define RXB0CTRL        0x60
#define RXB0SIDH        0x61
#define RXB0SIDL        0x62
#define RXB0DLC         0x65
#define RXB0D0          0x66

/* ── Bit masks ───────────────────────────────────── */
#define RX0IF           0x01
#define RX1IF           0x02
#define TXREQ           0x08
#define REQOP_MASK      0xE0
#define OPMOD_MASK      0xE0

/* ── CS helpers ──────────────────────────────────── */
static inline void cs_low(MCP2515_Handle_t *h)
{
    HAL_GPIO_WritePin(h->cs_port, h->cs_pin, GPIO_PIN_RESET);
}

static inline void cs_high(MCP2515_Handle_t *h)
{
    HAL_GPIO_WritePin(h->cs_port, h->cs_pin, GPIO_PIN_SET);
}

/* ── Primitives ──────────────────────────────────── */
static uint8_t read_reg(MCP2515_Handle_t *h, uint8_t reg)
{
    uint8_t tx[3] = { MCP_READ_CMD, reg, 0x00 };
    uint8_t rx[3] = { 0 };
    cs_low(h);
    HAL_SPI_TransmitReceive(h->hspi, tx, rx, 3, h->timeout_ms);
    cs_high(h);
    return rx[2];
}

static void write_reg(MCP2515_Handle_t *h, uint8_t reg, uint8_t value)
{
    uint8_t tx[3] = { MCP_WRITE_CMD, reg, value };
    cs_low(h);
    HAL_SPI_Transmit(h->hspi, tx, 3, h->timeout_ms);
    cs_high(h);
}

static void bit_modify(MCP2515_Handle_t *h, uint8_t reg, uint8_t mask, uint8_t data)
{
    uint8_t tx[4] = { MCP_BITMOD_CMD, reg, mask, data };
    cs_low(h);
    HAL_SPI_Transmit(h->hspi, tx, 4, h->timeout_ms);
    cs_high(h);
}

/* ── Reset ───────────────────────────────────────── */
void MCP2515_Reset(MCP2515_Handle_t *h)
{
    uint8_t cmd = MCP_RESET_CMD;
    cs_low(h);
    HAL_SPI_Transmit(h->hspi, &cmd, 1, h->timeout_ms);
    cs_high(h);
    HAL_Delay(10);
}

/* ── Mode ────────────────────────────────────────── */
int MCP2515_SetMode(MCP2515_Handle_t *h, MCP2515_Mode_t mode)
{
    bit_modify(h, CANCTRL, REQOP_MASK, mode);
    for (uint32_t i = 0; i < 100; i++) {
        if ((read_reg(h, CANSTAT) & OPMOD_MASK) == mode)
            return MCP2515_OK;
        HAL_Delay(1);
    }
    return MCP2515_ERR_TIMEOUT;
}

/* ── Bit timing ──────────────────────────────────── *
 * Values from MCP2515 datasheet Table 5-3.          *
 * Verify against your module's oscillator before    *
 * flashing — a wrong CNF value causes silent bus    *
 * errors that are very hard to debug on hardware.   *
 * ─────────────────────────────────────────────────── */
static int configure_bitrate(MCP2515_Handle_t *h, uint32_t baud)
{
    if (baud != 500)
        return MCP2515_ERR_PARAM;

#if   MCP2515_OSC_HZ == 8000000UL
    /* 8 MHz, 500 kbps — datasheet Table 5-3 */
    write_reg(h, CNF1, 0x00);
    write_reg(h, CNF2, 0x90);
    write_reg(h, CNF3, 0x02);
#elif MCP2515_OSC_HZ == 16000000UL
    /* 16 MHz, 500 kbps — datasheet Table 5-3 */
    write_reg(h, CNF1, 0x00);
    write_reg(h, CNF2, 0xAC);
    write_reg(h, CNF3, 0x03);
#else
#error "Unsupported oscillator frequency — add CNF values from MCP2515 datasheet Table 5-3"
#endif
    return MCP2515_OK;
}

/* ── Init ────────────────────────────────────────── */
int MCP2515_Init(MCP2515_Handle_t *h, uint32_t can_baud_kbps)
{
    MCP2515_Reset(h);

    if (MCP2515_SetMode(h, MCP2515_MODE_CONFIG) != MCP2515_OK)
        return MCP2515_ERR;

    if (configure_bitrate(h, can_baud_kbps) != MCP2515_OK)
        return MCP2515_ERR;

    /* RXB0: filters off (RXM=11), no rollover to RXB1 (BUKT=0) */
    write_reg(h, RXB0CTRL, 0x60);

    /* Clear any stale interrupt flags */
    write_reg(h, CANINTF, 0x00);

    /* Enable RX interrupts on INT pin */
    write_reg(h, CANINTE, RX0IF | RX1IF);

    return MCP2515_SetMode(h, MCP2515_MODE_NORMAL);
}

/* ── TX ──────────────────────────────────────────── */
bool MCP2515_TxReady(MCP2515_Handle_t *h)
{
    return !(read_reg(h, TXB0CTRL) & TXREQ);
}

int MCP2515_SendFrame(MCP2515_Handle_t *h, uint16_t id,
                      const uint8_t *data, uint8_t len)
{
    if (len > 8)               return MCP2515_ERR_PARAM;
    if (!MCP2515_TxReady(h))   return MCP2515_ERR_BUSY;

    write_reg(h, TXB0SIDH, (uint8_t)(id >> 3));
    write_reg(h, TXB0SIDL, (uint8_t)(id << 5)); /* EXIDE=0: standard frame */
    write_reg(h, TXB0DLC,  len);

    for (uint8_t i = 0; i < len; i++)
        write_reg(h, TXB0D0 + i, data[i]);

    uint8_t cmd = MCP_RTS_TXB0;
    cs_low(h);
    HAL_SPI_Transmit(h->hspi, &cmd, 1, h->timeout_ms);
    cs_high(h);

    return MCP2515_OK;
}

/* ── RX ──────────────────────────────────────────── */
bool MCP2515_RxAvailable(MCP2515_Handle_t *h)
{
    return (read_reg(h, CANINTF) & (RX0IF | RX1IF)) != 0;
}

int MCP2515_ReadFrame(MCP2515_Handle_t *h, uint16_t *id,
                      uint8_t *data, uint8_t *len)
{
    uint8_t flags = read_reg(h, CANINTF);

    if (!(flags & RX0IF))
        return MCP2515_ERR_NO_MSG;

    uint8_t sidh = read_reg(h, RXB0SIDH);
    uint8_t sidl = read_reg(h, RXB0SIDL);
    *id  = ((uint16_t)sidh << 3) | (sidl >> 5);
    *len = read_reg(h, RXB0DLC) & 0x0F;

    for (uint8_t i = 0; i < *len; i++)
        data[i] = read_reg(h, RXB0D0 + i);

    /* Clear RX0 interrupt flag */
    bit_modify(h, CANINTF, RX0IF, 0x00);

    return MCP2515_OK;
}

/* ── Error flags ─────────────────────────────────── */
uint8_t MCP2515_ReadErrorFlags(MCP2515_Handle_t *h)
{
    return read_reg(h, EFLG);
}
