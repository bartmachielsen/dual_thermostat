# Smart Climate Integration

The **Smart Climate** integration extends Home Assistant's built-in climate functionality to control one or two climate devices as a single unit. It intelligently determines whether to run in heating or cooling mode based on a preset (such as "comfort") and an outdoor sensor reading. Additionally, the integration supports an optional secondary device for boosting and synchronizes the HVAC mode across devices using a configurable template.

## Features

*   **Smart Mode Selection:**
    *   When the "comfort" preset is set, the integration checks the outdoor temperature.
    *   If the outdoor temperature is high (≥ `outdoor_hot_threshold`), it switches to cooling mode and applies the cooling preset temperature.
    *   If the outdoor temperature is low (≤ `outdoor_cold_threshold`), it switches to heating mode using the heating preset temperature.
    *   Otherwise, it applies a default mode based on the indoor temperature reading and the configured thresholds.
*   **Dual Device Control (Optional):**
    *   The integration designates one device as the main climate device and can optionally use a secondary device for additional boosting.
    *   Two thresholds determine activation:
        *   `temp_threshold_primary` – for the main device
        *   `temp_threshold_secondary` – for the secondary device
    *   If no secondary device is configured, only the primary device is controlled.
*   **Mode Synchronization:**
    *   A `mode_sync_template` can be provided to ensure that both climate devices (if applicable) run in the same HVAC mode.

## Installation

1.  Place the `smart_climate` folder in your `custom_components` directory.
2.  Restart Home Assistant.

The folder structure should look like:

custom\_components/
└── smart\_climate/
    ├── \_\_init\_\_.py
    ├── climate.py
    └── manifest.json
  

## Configuration

Below is an example YAML configuration. Note that code blocks in this README use double backticks.

```
climate:
  - platform: smart_climate
    main_climate: climate.living_room_main
    # Optional: secondary device for additional boosting
    secondary_climate: climate.living_room_secondary
    sensor: sensor.indoor_temperature
    outdoor_sensor: sensor.outdoor_temperature
    temp_threshold_primary: 1.0
    temp_threshold_secondary: 3.0
    outdoor_hot_threshold: 24.0
    outdoor_cold_threshold: 21.0
    min_runtime_seconds: 300
    mode_sync_template: "{{ 'cool' if states('sensor.outdoor_temperature')|float >= 24.0 else 'heat' }}"
  
```

## How It Works

*   **Smart Mode Selection:**
    *   If the indoor temperature is below the target temperature minus `temp_threshold_primary`, the main device activates heating mode.
    *   If the indoor temperature is above the target temperature plus `temp_threshold_primary`, the integration evaluates the outdoor sensor. If the outdoor temperature is ≥ `outdoor_hot_threshold`, cooling mode is activated.
    *   Within the acceptable range—and if the minimum runtime requirement is met—the system turns off the devices.
*   **Boosting Logic:**
    *   The indoor sensor reading is compared to the target temperature.
    *   If the difference exceeds `temp_threshold_secondary`, the secondary device (if configured) is activated to provide additional heating or cooling.
*   **Mode Synchronization:**
    *   The `mode_sync_template` is evaluated periodically.
    *   If the result differs from the current HVAC mode, both devices are forced into the desired mode.

## Additional Enhancements

Some ideas to further enhance this integration include:

*   **Config Flow / UI Integration:** Implement a configuration flow to allow setup and adjustments directly via the Home Assistant UI.
*   **Dynamic Role Swapping:** Add logic to dynamically swap which device is the main or secondary based on sensor health, energy efficiency, or performance.
*   **Advanced Error Handling and Notifications:** Improve error detection and send notifications if sensors are unavailable or if there are issues with device communication.
*   **Logging and Metrics:** Collect and display usage statistics (such as boosting frequency, mode switches, etc.) to help optimize performance.
*   **Fan and Swing Control:** Extend support to control additional HVAC settings like fan speed or swing modes, if supported by the devices.
*   **Adaptive Thresholds:** Allow thresholds to adjust based on historical data, time of day, or occupancy information.

## Contributing

Contributions are welcome! Feel free to open issues or pull requests on the repository.

## License

This integration is provided under the MIT License.