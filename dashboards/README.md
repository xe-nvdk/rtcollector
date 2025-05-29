# RTCollector Dashboards

This directory contains Grafana dashboards designed to work with RTCollector, RedisTimeSeries, and Grafana. These dashboards are provided to help you get started with visualizing the metrics collected by RTCollector.

## Purpose

- Accelerate adoption of RTCollector with ready-to-use visualizations
- Provide examples of how to query RedisTimeSeries data in Grafana
- Showcase the capabilities of RTCollector's metrics collection

## Available Dashboards

| Dashboard | Description | Link |
|-----------|-------------|------|
| Linux System Overview | Comprehensive system metrics for Linux hosts including CPU, memory, disk, network, and process statistics | [linux-system-overview](./linux-system-overview/) |

## How to Contribute

We welcome contributions to improve existing dashboards or add new ones:

1. **Improve existing dashboards**:
   - Fork the repository
   - Make your changes to the dashboard JSON
   - Submit a pull request with a clear description of your improvements

2. **Add new dashboards**:
   - Create a new folder under `dashboards/` with a descriptive name
   - Include the dashboard JSON file
   - Add a README.md explaining what the dashboard shows
   - Update this main README to include your dashboard in the table
   - Submit a pull request

## Dashboard Guidelines

When contributing dashboards, please follow these guidelines:

- Use variables for host selection, mount points, interfaces, etc.
- Include appropriate refresh intervals (typically 5-30s)
- Group related panels together
- Use consistent units and color schemes
- Include documentation in the dashboard (text panels explaining sections)
- Test with different data sources and configurations

## Requirements

- Grafana 9.x or newer
- Redis Data Source for Grafana
- RedisTimeSeries database with metrics from RTCollector