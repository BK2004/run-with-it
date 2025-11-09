
#include <stdio.h>
#include <string.h>
#include <stdint.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"

#include "driver/i2c.h"
#include "driver/adc.h"

#include "esp_log.h"
#include "esp_err.h"

#include "nvs_flash.h"
#include "esp_netif.h"
#include "esp_event.h"
#include "esp_wifi.h"
#include "esp_http_client.h"
#include "lwip/err.h"
#include "lwip/sys.h"

#include "driver/gpio.h"

// --------- User configuration ----------
#define WIFI_SSID    "Lucas iPhone 15 Pro"
#define WIFI_PASS    "Hackutd1"
#define CSV_POST_URL "http://172.20.10.7:8000/data" // change to your laptop IP:port
#define INPUT_PIN 33
// ---------------------------------------

/* I2C / MPU6050 pins and regs */
#define I2C_MASTER_SCL_IO           22
#define I2C_MASTER_SDA_IO           21
#define I2C_MASTER_NUM              I2C_NUM_0
#define I2C_MASTER_FREQ_HZ          400000
#define I2C_MASTER_TX_BUF_DISABLE   0
#define I2C_MASTER_RX_BUF_DISABLE   0
#define I2C_MASTER_TIMEOUT_MS       1000

#define MPU6050_ADDR                0x68
#define MPU6050_REG_PWR_MGMT_1      0x6B
#define MPU6050_REG_ACCEL_XOUT_H    0x3B

/* ADC pin: IO34 -> ADC1_CHANNEL_6 */
#define ADC_CHANNEL                 ADC1_CHANNEL_6

/* Logging tags */
static const char *TAG = "SENSOR_APP";
static const char *WIFI_TAG = "WIFI_STA";
static const char *HTTP_TAG = "HTTP_POST";

static EventGroupHandle_t s_wifi_event_group;
#define CONNECTED_BIT BIT0

/* Forward declaration for http_post_csv used in app_main */
static void http_post_csv(float x, float y, float z, float temp, int boolean_flag);

/* ---------------- Wi-Fi STA ---------------- */
static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                               int32_t event_id, void* event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();

    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        wifi_event_sta_disconnected_t *event = (wifi_event_sta_disconnected_t *)event_data;
        ESP_LOGW(WIFI_TAG, "Disconnected from AP, reason=%d. Retrying...", event->reason);
        esp_wifi_connect();
        xEventGroupClearBits(s_wifi_event_group, CONNECTED_BIT);

    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(WIFI_TAG, "Got IP: " IPSTR, IP2STR(&event->ip_info.ip));
        xEventGroupSetBits(s_wifi_event_group, CONNECTED_BIT);
    }
}


static void wifi_init_sta(void)
{
    ESP_ERROR_CHECK(nvs_flash_init());
    ESP_ERROR_CHECK(esp_netif_init());
    s_wifi_event_group = xEventGroupCreate();
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID,
                                               &wifi_event_handler, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP,
                                               &wifi_event_handler, NULL));

    wifi_config_t wifi_config = {
        .sta = {
            .ssid = WIFI_SSID,
            .password = WIFI_PASS,
            .threshold.authmode = WIFI_AUTH_WPA2_PSK,
        },
    };

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(WIFI_TAG, "wifi_init_sta finished. Waiting for IP...");
    xEventGroupWaitBits(s_wifi_event_group, CONNECTED_BIT, pdFALSE, pdTRUE, portMAX_DELAY);
    ESP_LOGI(WIFI_TAG, "Connected to AP");
}

/* ---------------- I2C + MPU6050 ---------------- */
static esp_err_t i2c_master_init(void)
{
    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = I2C_MASTER_FREQ_HZ,
    };
    ESP_ERROR_CHECK(i2c_param_config(I2C_MASTER_NUM, &conf));
    ESP_ERROR_CHECK(i2c_driver_install(I2C_MASTER_NUM, conf.mode,
                                       I2C_MASTER_RX_BUF_DISABLE,
                                       I2C_MASTER_TX_BUF_DISABLE, 0));
    return ESP_OK;
}

static esp_err_t mpu6050_write_byte(uint8_t reg, uint8_t data)
{
    uint8_t buf[2] = {reg, data};
    return i2c_master_write_to_device(I2C_MASTER_NUM, MPU6050_ADDR,
                                      buf, sizeof(buf),
                                      I2C_MASTER_TIMEOUT_MS / portTICK_PERIOD_MS);
}

static esp_err_t mpu6050_read_bytes(uint8_t reg, uint8_t *data, size_t len)
{
    return i2c_master_write_read_device(I2C_MASTER_NUM, MPU6050_ADDR,
                                        &reg, 1, data, len,
                                        I2C_MASTER_TIMEOUT_MS / portTICK_PERIOD_MS);
}

static esp_err_t mpu6050_init(void)
{
    // Wake up MPU6050 (clear sleep bit)
    esp_err_t err = mpu6050_write_byte(MPU6050_REG_PWR_MGMT_1, 0x00);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Failed to wake MPU6050: %s", esp_err_to_name(err));
        return err;
    }

    vTaskDelay(pdMS_TO_TICKS(100));
    return ESP_OK;
}

static void mpu6050_read_accel(float *ax_g, float *ay_g, float *az_g)
{
    uint8_t data[6];
    esp_err_t err = mpu6050_read_bytes(MPU6050_REG_ACCEL_XOUT_H, data, sizeof(data));
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "MPU6050 read error: %s", esp_err_to_name(err));
        *ax_g = *ay_g = *az_g = 0.0f;
        return;
    }

    int16_t ax_raw = (int16_t)((data[0] << 8) | data[1]);
    int16_t ay_raw = (int16_t)((data[2] << 8) | data[3]);
    int16_t az_raw = (int16_t)((data[4] << 8) | data[5]);

    *ax_g = ax_raw / 16384.0f;
    *ay_g = ay_raw / 16384.0f;
    *az_g = az_raw / 16384.0f;
}

/* ---------------- HTTP CSV POST ---------------- */
static void http_post_csv(float x, float y, float z, float temp, int boolean_flag)
{
    char csv[128];
    int len = snprintf(csv, sizeof(csv), "%.3f,%.3f,%.3f,%.3f,0,%d\n",
                       x, y, z, temp, boolean_flag);
    if (len <= 0 || len >= (int)sizeof(csv)) {
        ESP_LOGE(HTTP_TAG, "CSV build error");
        return;
    }

    esp_http_client_config_t config = {
        .url = CSV_POST_URL,
        .method = HTTP_METHOD_POST,
        .timeout_ms = 3000,
    };

    esp_http_client_handle_t client = esp_http_client_init(&config);
    if (!client) {
        ESP_LOGE(HTTP_TAG, "Failed to init HTTP client");
        return;
    }

    esp_http_client_set_header(client, "Content-Type", "text/csv");
    esp_http_client_set_post_field(client, csv, len);

    esp_err_t err = esp_http_client_perform(client);
    if (err == ESP_OK) {
        int status = esp_http_client_get_status_code(client);
        ESP_LOGI(HTTP_TAG, "POST OK, status=%d body=\"%s\"", status, csv);
    } else {
        ESP_LOGE(HTTP_TAG, "POST failed: %s", esp_err_to_name(err));
    }

    esp_http_client_cleanup(client);

}

/* ---------------- app_main ---------------- */
void app_main(void)
{
    ESP_LOGI(TAG, "Starting sensor POST app");

    // 1) Wi-Fi connect (blocks until IP)
    wifi_init_sta();

    // 2) I2C + MPU6050
    ESP_ERROR_CHECK(i2c_master_init());
    ESP_LOGI(TAG, "I2C initialized");

     // After wifi_init_sta() and before the loop:
gpio_reset_pin(INPUT_PIN);
gpio_set_direction(INPUT_PIN, GPIO_MODE_INPUT);
gpio_pullup_en(INPUT_PIN);        // enable internal pull-up
gpio_pulldown_dis(INPUT_PIN);     // make sure pulldown is off


    esp_err_t mpu_ok = mpu6050_init();
    if (mpu_ok == ESP_OK) {
        ESP_LOGI(TAG, "MPU6050 initialized");
    } else {
        ESP_LOGW(TAG, "MPU6050 init failed (%s). Continuing with ADC+HTTP only.",
                 esp_err_to_name(mpu_ok));
    }

    // 3) ADC config (GPIO34 = ADC1_CHANNEL_6)
    adc1_config_width(ADC_WIDTH_BIT_12);
    adc1_config_channel_atten(ADC_CHANNEL, ADC_ATTEN_DB_11);
    ESP_LOGI(TAG, "ADC configured on GPIO34 (ADC1_CHANNEL_6)");

    // 4) Main loop: read & POST
    while (1) {
        float ax = 0.0f, ay = 0.0f, az = 0.0f;
        if (mpu_ok == ESP_OK) {
            mpu6050_read_accel(&ax, &ay, &az);
        }

        int raw = adc1_get_raw(ADC_CHANNEL);
        float voltage = (raw / 4095.0f) * 3.3f;

        float temp = voltage*476.67f + 17.57f; // placeholder. replace with actual conversion if you want °C
        int boolean_flag = gpio_get_level(INPUT_PIN);


        // POST CSV line
        http_post_csv(ax, ay, az, temp, boolean_flag);

        // Local logging
        ESP_LOGI(TAG, "Posted CSV -> X=%.3f Y=%.3f Z=%.3f Temp=%.3f raw=%d V=%.3f Bool=%d",
                 ax, ay, az, temp, raw, voltage, boolean_flag);

        vTaskDelay(pdMS_TO_TICKS(100)); // 1 Hz
    }
}

