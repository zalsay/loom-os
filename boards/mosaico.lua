-- Loom OS boards/mosaico.lua
-- ESP-Mosaico V1.0 board policy and hardware metadata.


local M = {}
M.id = "mosaico"
M.name = "ESP-Mosaico"
M.chip = "ESP32-S31"
M.hardware_revision = "CoreBoard V1.0"


M.display = {
    width = 480,
    height = 480,
    lcd_device = "display_lcd",
    touch_device = "lcd_touch",
    lcd_driver = "CO5300",
    touch_controller = "CST9220",
}


M.i2c = {
    sda = 0,
    scl = 1,
    addresses = {
        bmm150_1 = 0x11,
        bmm150_2 = 0x12,
        es8311 = 0x19,
        module_eeprom_left = 0x50,
        module_eeprom_right = 0x51,
        bq27220 = 0x55,
        cst9220 = 0x5A,
        bmi270 = 0x69,
    },
}


M.hard_reserved_gpio = {
    [0]="shared I2C SDA", [1]="shared I2C SCL", [2]="sensor interrupt",
    [3]="status LED", [6]="touch interrupt", [7]="AI button", [8]="vibration motor",
    [9]="LCD DATA3", [35]="LCD DATA2", [36]="LCD DATA0", [42]="LCD reset",
    [43]="LCD TE", [44]="LCD clock", [50]="LCD chip select", [51]="LCD DATA1",
    [45]="speaker amplifier enable", [56]="audio codec power",
    [57]="power switch request", [60]="system 3.3V rail control",
    [20]="SPI NAND clock", [21]="SPI NAND data", [22]="SPI NAND Q",
    [23]="SPI NAND chip select", [24]="SPI NAND hold", [25]="SPI NAND write protect",
    [14]="left module EEPROM address select", [39]="right module EEPROM address select",
}


M.audio_shared_gpio = {
    [37]="I2S BCK / expansion",
    [40]="I2S DOUT / expansion",
    [49]="I2S WS / expansion",
    [52]="I2S DIN / expansion",
    [54]="I2S MCLK / expansion",
}


M.expansion_gpio = {5, 10, 11, 38, 46, 47, 58, 59}


M.onboard = {
    imu = {model="BMI270", address=0x69},
    magnetometer_1 = {model="BMM150", address=0x11},
    magnetometer_2 = {model="BMM150", address=0x12},
    fuel_gauge = {model="BQ27220", address=0x55},
    audio_codec = {model="ES8311", address=0x19},
    speaker_amp = {model="NS4150B"},
    touch = {model="CST9220", address=0x5A},
}


local function lower(v)
    return type(v) == "string" and v:lower() or ""
end


function M.matches(info)
    return type(info) == "table"
        and lower(info.name):find("mosaico", 1, true) ~= nil
end


function M.system_options(hooks)
    hooks = hooks or {}
    return {
        board = M.name,
        chip = M.chip,
        battery = hooks.battery,
        memory = hooks.memory,
        wifi = hooks.wifi,
        now_ms = hooks.now_ms,
    }
end


function M.reserve_gpio(gpio_api, options)
    options = options or {}
    if type(gpio_api) ~= "table" or type(gpio_api.reserve_system) ~= "function" then
        return nil, "gpio_api.reserve_system is required"
    end


    local reserved = {}
    local function reserve_set(set, prefix)
        for pin, reason in pairs(set) do
            local ok, err = gpio_api.reserve_system(pin, prefix .. ": " .. reason)
            if ok then
                reserved[#reserved + 1] = pin
            elseif not (type(err) == "table" and err.code == "E_BUSY") then
                return nil, err
            end
        end
        return true
    end


    local ok, err = reserve_set(M.hard_reserved_gpio, "mosaico")
    if not ok then return nil, err end


    if options.allow_audio_shared_gpio ~= true then
        ok, err = reserve_set(M.audio_shared_gpio, "mosaico audio")
        if not ok then return nil, err end
    end


    table.sort(reserved)
    return reserved
end


-- Sensor providers are injected only after a real ESP-Claw Lua driver path is verified.
function M.register_sensors(sensor_registry, providers)
    providers = providers or {}
    if type(sensor_registry) ~= "table" or type(sensor_registry.register) ~= "function" then
        return nil, "sensor registry is required"
    end


    local registered = {}
    local function add(id, provider, metadata)
        if type(provider) ~= "table" or type(provider.read) ~= "function" then
            return true
        end
        local ok, err = sensor_registry.register(id, provider, metadata)
        if not ok then return nil, err end
        registered[#registered + 1] = id
        return true
    end


    local ok, err = add("imu", providers.imu, {
        model="BMI270", bus="i2c", address=0x69, kind="accelerometer_gyroscope"
    })
    if not ok then return nil, err end


    ok, err = add("magnetometer.left", providers.magnetometer_left, {
        model="BMM150", bus="i2c", address=0x11, kind="magnetometer"
    })
    if not ok then return nil, err end


    ok, err = add("magnetometer.right", providers.magnetometer_right, {
        model="BMM150", bus="i2c", address=0x12, kind="magnetometer"
    })
    if not ok then return nil, err end


    table.sort(registered)
    return registered
end


return M