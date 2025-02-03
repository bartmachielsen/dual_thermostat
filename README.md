# Dual Thermostat Integration

The **Dual Thermostat** integration extends Home Assistant's built-in climate functionality to control two climate devices (e.g., two air conditioners) as a single unit. It intelligently determines whether to run in heating or cooling mode based on a preset (like "comfort") and an outdoor sensor reading. Additionally, the integration supports boosting via a secondary device and synchronizes the HVAC mode across devices using a configurable template.

## Features

- **Smart Comfort Mode:**  
  When the "comfort" preset is set, the integration checks the outdoor temperature.  
  - If the outdoor temperature is very hot (≥ `outdoor_hot_threshold`), the integration switches to cooling mode and applies the cooling preset temperature.
  - If it is very cold (≤ `outdoor_cold_threshold`), it switches to heating mode using the heating preset.
  - In between, a default mode (e.g., heating) is applied (this behavior can be adjusted).

- **Dual Device Control:**  
  The integration designates one device as the effective main device (to set the target temperature) and the other as a secondary booster. The booster is activated based on a temperature threshold and operation mode:
  - **always:** The secondary device is always activated when the temperature difference exceeds the threshold.
  - **on_demand:** It is activated only if the difference is significantly larger.
  - **constant_on_demand:** Once activated, the secondary device stays on until the target temperature is reached.

- **Mode Synchronization:**  
  A `mode_sync_template` can be provided to ensure both climate devices run in the same HVAC mode.

## Installation

1. Place the `dual_thermostat` folder in your `custom_components` directory.
2. Restart Home Assistant.

The folder structure should look like:


## Configuration

Below is an example YAML configuration. Note that code blocks in this README use double backticks.

```python
climate:
  - platform: dual_thermostat
    main_climate: climate.living_room_main
    secondary_climate: climate.living_room_secondary
    sensor: sensor.indoor_temperature
    outdoor_sensor: sensor.outdoor_temperature
    operation_mode: on_demand
    temp_threshold: 1.5
    heating_preset_temperatures:
      comfort: 21
      eco: 17
    cooling_preset_temperatures:
      comfort: 25
      eco: 28
    outdoor_hot_threshold: 25.0
    outdoor_cold_threshold: 10.0
    mode_sync_template: "{{ 'cool' if states('sensor.ac1_mode') != states('sensor.ac2_mode') else states('sensor.ac1_mode') }}"
```

## How It Works

- **Smart Mode Selection:**  
  The integration uses the outdoor sensor to determine whether "comfort" should result in heating or cooling:
  - If `sensor.outdoor_temperature` is ≥ `outdoor_hot_threshold`, it selects cooling mode.
  - If ≤ `outdoor_cold_threshold`, it selects heating mode.
  - Otherwise, it defaults to a predetermined mode (by default, heating).

- **Boosting Logic:**  
  The indoor sensor reading is compared to the target temperature. If the difference exceeds `temp_threshold`, the secondary device is activated based on the chosen operation mode.

- **Mode Synchronization:**  
  The `mode_sync_template` is evaluated periodically. If the result differs from the current HVAC mode, both devices are forced into the desired mode.

## Additional Enhancements

Some ideas to further enhance this integration include:

- **Config Flow / UI Integration:**  
  Implement a configuration flow to allow setup and adjustments directly via the Home Assistant UI.

- **Dynamic Role Swapping:**  
  Add logic to dynamically swap which device is the main or secondary based on sensor health, energy efficiency, or performance.

- **Advanced Error Handling and Notifications:**  
  Improve error detection and send notifications if sensors are unavailable or if there are issues with device communication.

- **Logging and Metrics:**  
  Collect and display usage statistics (such as boosting frequency, mode switches, etc.) to help optimize performance.

- **Fan and Swing Control:**  
  Extend support to control additional HVAC settings like fan speed or swing modes, if supported by the devices.

- **Adaptive Thresholds:**  
  Allow thresholds to adjust based on historical data, time of day, or occupancy information.

## Contributing

Contributions are welcome! Feel free to open issues or pull requests on the repository.

## License

This integration is provided under the MIT License.
