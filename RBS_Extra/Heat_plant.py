import asyncio
import logging
import random
from dataclasses import dataclass

from asyncua import Server, ua

ENDPOINT = "opc.tcp://0.0.0.0:4840/scada-heatplant/"
NAMESPACE_URI = "urn:local:scada:heatplant"
UPDATE_INTERVAL_SECONDS = 1.0

STATUS_TEXT = {
    0: "Off",
    1: "Auto on",
    2: "Man off",
    3: "Man on",
    4: "Alarm",
}

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("heatplant_test_server")


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


@dataclass
class DeviceStatus:
    tag: str
    status_node: object
    start_cmd_node: object
    stop_cmd_node: object
    auto_mode_node: object
    enable_in_auto_node: object
    running_fb_node: object
    available_node: object
    fault_node: object
    status: int = 0


@dataclass
class ValveDevice:
    tag: str
    status_node: object
    auto_mode_node: object
    open_cmd_node: object
    close_cmd_node: object
    position_cmd_node: object
    position_fb_node: object
    open_fb_node: object
    closed_fb_node: object
    fault_node: object
    position: float = 0.0
    status: int = 0


@dataclass
class AnalogValue:
    tag: str
    value_node: object
    low_node: object
    high_node: object
    low_alarm_node: object
    high_alarm_node: object
    min_value: float
    max_value: float
    value: float
    noise_step: float


async def add_status_device(parent, idx: int, tag: str, description: str, initial_status: int = 0):
    obj = await parent.add_object(idx, tag)
    await obj.add_variable(idx, "Description", ua.Variant(description, ua.VariantType.String))

    status = await obj.add_variable(idx, "Status", ua.Variant(initial_status, ua.VariantType.Int32))
    start_cmd = await obj.add_variable(idx, "StartCmd", ua.Variant(False, ua.VariantType.Boolean))
    stop_cmd = await obj.add_variable(idx, "StopCmd", ua.Variant(False, ua.VariantType.Boolean))
    auto_mode = await obj.add_variable(idx, "AutoMode", ua.Variant(True, ua.VariantType.Boolean))
    enable_in_auto = await obj.add_variable(idx, "EnableInAuto", ua.Variant(True, ua.VariantType.Boolean))
    running_fb = await obj.add_variable(idx, "RunningFb", ua.Variant(initial_status in (1, 3), ua.VariantType.Boolean))
    available = await obj.add_variable(idx, "Available", ua.Variant(True, ua.VariantType.Boolean))
    fault = await obj.add_variable(idx, "Fault", ua.Variant(False, ua.VariantType.Boolean))

    await status.set_writable()
    await start_cmd.set_writable()
    await stop_cmd.set_writable()
    await auto_mode.set_writable()
    await enable_in_auto.set_writable()
    await running_fb.set_writable()
    await available.set_writable()
    await fault.set_writable()

    return DeviceStatus(
        tag=tag,
        status_node=status,
        start_cmd_node=start_cmd,
        stop_cmd_node=stop_cmd,
        auto_mode_node=auto_mode,
        enable_in_auto_node=enable_in_auto,
        running_fb_node=running_fb,
        available_node=available,
        fault_node=fault,
        status=initial_status,
    )


async def add_valve_device(parent, idx: int, tag: str, description: str, initial_position: float = 0.0, initial_status: int = 0):
    obj = await parent.add_object(idx, tag)
    await obj.add_variable(idx, "Description", ua.Variant(description, ua.VariantType.String))

    status = await obj.add_variable(idx, "Status", ua.Variant(initial_status, ua.VariantType.Int32))
    auto_mode = await obj.add_variable(idx, "AutoMode", ua.Variant(True, ua.VariantType.Boolean))
    open_cmd = await obj.add_variable(idx, "OpenCmd", ua.Variant(False, ua.VariantType.Boolean))
    close_cmd = await obj.add_variable(idx, "CloseCmd", ua.Variant(False, ua.VariantType.Boolean))
    position_cmd = await obj.add_variable(idx, "PositionCmd", ua.Variant(float(initial_position), ua.VariantType.Float))
    position_fb = await obj.add_variable(idx, "PositionFb", ua.Variant(float(initial_position), ua.VariantType.Float))
    open_fb = await obj.add_variable(idx, "OpenFb", ua.Variant(False, ua.VariantType.Boolean))
    closed_fb = await obj.add_variable(idx, "ClosedFb", ua.Variant(initial_position <= 0.5, ua.VariantType.Boolean))
    fault = await obj.add_variable(idx, "Fault", ua.Variant(False, ua.VariantType.Boolean))

    await status.set_writable()
    await auto_mode.set_writable()
    await open_cmd.set_writable()
    await close_cmd.set_writable()
    await position_cmd.set_writable()
    await position_fb.set_writable()
    await open_fb.set_writable()
    await closed_fb.set_writable()
    await fault.set_writable()

    return ValveDevice(
        tag=tag,
        status_node=status,
        auto_mode_node=auto_mode,
        open_cmd_node=open_cmd,
        close_cmd_node=close_cmd,
        position_cmd_node=position_cmd,
        position_fb_node=position_fb,
        open_fb_node=open_fb,
        closed_fb_node=closed_fb,
        fault_node=fault,
        position=float(initial_position),
        status=initial_status,
    )


async def add_analog_value(parent, idx: int, tag: str, description: str, start_value: float,
                           eng_low: float, eng_high: float, low_limit: float, high_limit: float, noise_step: float):
    obj = await parent.add_object(idx, tag)
    await obj.add_variable(idx, "Description", ua.Variant(description, ua.VariantType.String))

    value_node = await obj.add_variable(idx, "Value", ua.Variant(float(start_value), ua.VariantType.Float))
    low_node = await obj.add_variable(idx, "LowLimit", ua.Variant(float(low_limit), ua.VariantType.Float))
    high_node = await obj.add_variable(idx, "HighLimit", ua.Variant(float(high_limit), ua.VariantType.Float))
    low_alarm = await obj.add_variable(idx, "LowAlarm", ua.Variant(False, ua.VariantType.Boolean))
    high_alarm = await obj.add_variable(idx, "HighAlarm", ua.Variant(False, ua.VariantType.Boolean))
    eng_low_node = await obj.add_variable(idx, "EngLow", ua.Variant(float(eng_low), ua.VariantType.Float))
    eng_high_node = await obj.add_variable(idx, "EngHigh", ua.Variant(float(eng_high), ua.VariantType.Float))

    await low_node.set_writable()
    await high_node.set_writable()
    await low_alarm.set_writable()
    await high_alarm.set_writable()

    return AnalogValue(
        tag=tag,
        value_node=value_node,
        low_node=low_node,
        high_node=high_node,
        low_alarm_node=low_alarm,
        high_alarm_node=high_alarm,
        min_value=float(eng_low),
        max_value=float(eng_high),
        value=float(start_value),
        noise_step=float(noise_step),
    )


async def apply_latched_alarms(point: AnalogValue):
    low_limit = float(await point.low_node.read_value())
    high_limit = float(await point.high_node.read_value())
    low_alarm_active = bool(await point.low_alarm_node.read_value())
    high_alarm_active = bool(await point.high_alarm_node.read_value())

    point.value = round(clamp(point.value, point.min_value, point.max_value), 2)
    await point.value_node.write_value(ua.Variant(float(point.value), ua.VariantType.Float))

    if point.value < low_limit and not low_alarm_active:
        await point.low_alarm_node.write_value(ua.Variant(True, ua.VariantType.Boolean))
    if point.value > high_limit and not high_alarm_active:
        await point.high_alarm_node.write_value(ua.Variant(True, ua.VariantType.Boolean))


async def simulate_status_device(device: DeviceStatus, auto_run_request: bool):
    available = bool(await device.available_node.read_value())
    fault = bool(await device.fault_node.read_value())
    auto_mode = bool(await device.auto_mode_node.read_value())
    enable_in_auto = bool(await device.enable_in_auto_node.read_value())
    start_cmd = bool(await device.start_cmd_node.read_value())
    stop_cmd = bool(await device.stop_cmd_node.read_value())

    if fault:
        device.status = 4
    elif not available:
        device.status = 0
    elif auto_mode:
        device.status = 1 if (auto_run_request and enable_in_auto) else 0
    else:
        if start_cmd and not stop_cmd:
            device.status = 3
        elif stop_cmd:
            device.status = 2
        else:
            if device.status == 3:
                device.status = 3
            elif device.status == 2:
                device.status = 2
            else:
                device.status = 2

    running = device.status in (1, 3)

    await device.status_node.write_value(ua.Variant(int(device.status), ua.VariantType.Int32))
    await device.running_fb_node.write_value(ua.Variant(bool(running), ua.VariantType.Boolean))
    await device.start_cmd_node.write_value(ua.Variant(False, ua.VariantType.Boolean))
    await device.stop_cmd_node.write_value(ua.Variant(False, ua.VariantType.Boolean))


async def simulate_valve(valve: ValveDevice, plant_auto_run: bool):
    fault = bool(await valve.fault_node.read_value())
    auto_mode = bool(await valve.auto_mode_node.read_value())
    open_cmd = bool(await valve.open_cmd_node.read_value())
    close_cmd = bool(await valve.close_cmd_node.read_value())
    position_cmd = float(await valve.position_cmd_node.read_value())

    if fault:
        valve.status = 4
    else:
        if auto_mode:
            target = clamp(position_cmd, 0.0, 100.0)
        elif open_cmd and not close_cmd:
            target = 100.0
        elif close_cmd and not open_cmd:
            target = 0.0
        else:
            target = valve.position

        if valve.position < target:
            valve.position += min(4.0, target - valve.position)
        elif valve.position > target:
            valve.position -= min(4.0, valve.position - target)

        valve.position = round(clamp(valve.position, 0.0, 100.0), 1)

        if auto_mode:
            valve.status = 1 if (plant_auto_run and valve.position > 0.5) else 0
        else:
            valve.status = 3 if valve.position > 0.5 else 2

    await valve.status_node.write_value(ua.Variant(int(valve.status), ua.VariantType.Int32))
    await valve.position_fb_node.write_value(ua.Variant(float(valve.position), ua.VariantType.Float))
    await valve.open_fb_node.write_value(ua.Variant(valve.position >= 99.5, ua.VariantType.Boolean))
    await valve.closed_fb_node.write_value(ua.Variant(valve.position <= 0.5, ua.VariantType.Boolean))
    await valve.open_cmd_node.write_value(ua.Variant(False, ua.VariantType.Boolean))
    await valve.close_cmd_node.write_value(ua.Variant(False, ua.VariantType.Boolean))


async def main():
    server = Server()
    await server.init()

    server.set_endpoint(ENDPOINT)
    server.set_server_name("Simple Heat Plant Test Server - Cold Start")
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    if hasattr(server, "set_identity_tokens") and hasattr(ua, "AnonymousIdentityToken"):
        server.set_identity_tokens([ua.AnonymousIdentityToken])
    elif hasattr(server, "set_security_IDs"):
        server.set_security_IDs(["Anonymous"])

    server.allow_remote_admin(False)

    idx = await server.register_namespace(NAMESPACE_URI)
    root = await server.nodes.objects.add_object(idx, "SCADA_HeatPlant")

    plant_folder = await root.add_folder(idx, "Plant")
    boiler_folder = await root.add_folder(idx, "Boiler")
    pumps_folder = await root.add_folder(idx, "Pumps")
    valves_folder = await root.add_folder(idx, "Valves")
    tank_folder = await root.add_folder(idx, "Tank")
    process_folder = await root.add_folder(idx, "Process")

    # Plant
    plant = await plant_folder.add_object(idx, "PLANT")
    plant_mode = await plant.add_variable(idx, "PlantMode", ua.Variant(0, ua.VariantType.Int32))
    heat_demand = await plant.add_variable(idx, "HeatDemand", ua.Variant(False, ua.VariantType.Boolean))
    common_alarm = await plant.add_variable(idx, "CommonAlarm", ua.Variant(False, ua.VariantType.Boolean))
    supply_temp_sp = await plant.add_variable(idx, "SupplyTempSP", ua.Variant(72.0, ua.VariantType.Float))
    outside_temp = await plant.add_variable(idx, "OutsideTemp", ua.Variant(3.0, ua.VariantType.Float))
    for n in [plant_mode, heat_demand, common_alarm, supply_temp_sp, outside_temp]:
        await n.set_writable()

    # Main devices
    boiler = await add_status_device(boiler_folder, idx, "BK101", "Biopanna / varmepanna", 0)
    feeder = await add_status_device(boiler_folder, idx, "M101", "Bransleskruv / branslematare", 0)
    fan = await add_status_device(boiler_folder, idx, "F101", "Forbranningsflakt", 0)

    p101 = await add_status_device(pumps_folder, idx, "P101", "Framledningspump", 0)
    p102 = await add_status_device(pumps_folder, idx, "P102", "Returpump", 0)

    v101 = await add_valve_device(valves_folder, idx, "V101", "Shuntventil framledning", 0.0, 0)

    # Boiler / process analogs - kalla startvärden
    tt101 = await add_analog_value(boiler_folder, idx, "TT101", "Pannvattentemperatur", 25.0, 0.0, 100.0, 10.0, 90.0, 0.3)
    pt101 = await add_analog_value(boiler_folder, idx, "PT101", "Panntryck", 0.8, 0.0, 6.0, 0.5, 3.0, 0.05)
    temp_sp = await boiler_folder.add_object(idx, "BoilerSetpoints")
    bk_temp_sp = await temp_sp.add_variable(idx, "TempSP", ua.Variant(75.0, ua.VariantType.Float))
    await bk_temp_sp.set_writable()

    # Tank - kalla startvärden
    lt301 = await add_analog_value(tank_folder, idx, "LT301", "Tankniva", 55.0, 0.0, 100.0, 20.0, 95.0, 0.3)
    tt301 = await add_analog_value(tank_folder, idx, "TT301", "Tank topptemperatur", 30.0, 0.0, 100.0, 10.0, 90.0, 0.25)
    tt302 = await add_analog_value(tank_folder, idx, "TT302", "Tank bottentemperatur", 25.0, 0.0, 100.0, 10.0, 70.0, 0.25)

    # Process lines - kalla startvärden
    tt201 = await add_analog_value(process_folder, idx, "TT201", "Framledningstemperatur", 22.0, 0.0, 100.0, 10.0, 85.0, 0.4)
    tt202 = await add_analog_value(process_folder, idx, "TT202", "Returtemperatur", 20.0, 0.0, 100.0, 10.0, 70.0, 0.4)
    pt201 = await add_analog_value(process_folder, idx, "PT201", "Framledningstryck", 0.7, 0.0, 6.0, 0.3, 3.5, 0.05)
    pt202 = await add_analog_value(process_folder, idx, "PT202", "Returtryck", 0.6, 0.0, 6.0, 0.3, 3.0, 0.05)
    ft201 = await add_analog_value(process_folder, idx, "FT201", "Framledningsflode", 0.0, 0.0, 2000.0, 0.0, 1500.0, 10.0)
    tt401 = await add_analog_value(process_folder, idx, "TT401", "Utetemperatur givare", 3.0, -20.0, 30.0, -15.0, 20.0, 0.3)

    status_devices = [boiler, feeder, fan, p101, p102]
    analogs = [tt101, pt101, lt301, tt301, tt302, tt201, tt202, pt201, pt202, ft201, tt401]

    _logger.info("Server startad: %s", ENDPOINT)
    _logger.info("Root object: Objects/SCADA_HeatPlant")
    _logger.info("Status mapping: 0=Off, 1=Auto on, 2=Man off, 3=Man on, 4=Alarm")
    _logger.info("Cold start enabled: PlantMode=0 and HeatDemand=False at startup")

    async with server:
        while True:
            plant_mode_value = int(await plant_mode.read_value())
            demand = bool(await heat_demand.read_value())
            outside = float(await outside_temp.read_value())
            boiler_sp = float(await bk_temp_sp.read_value())

            plant_auto_run = plant_mode_value == 1 and demand

            for device in status_devices:
                await simulate_status_device(device, auto_run_request=plant_auto_run)

            await simulate_valve(v101, plant_auto_run=plant_auto_run)

            # outside temp drifts slowly
            outside += random.uniform(-0.2, 0.2)
            outside = round(clamp(outside, -15.0, 20.0), 1)
            await outside_temp.write_value(ua.Variant(float(outside), ua.VariantType.Float))
            tt401.value = outside

            boiler_running = bool(await boiler.running_fb_node.read_value())
            feeder_running = bool(await feeder.running_fb_node.read_value())
            fan_running = bool(await fan.running_fb_node.read_value())
            p101_running = bool(await p101.running_fb_node.read_value())
            p102_running = bool(await p102.running_fb_node.read_value())

            burner_power = 1.0 if (boiler_running and feeder_running and fan_running and plant_auto_run) else 0.0
            pump_factor = 1.0 if (p101_running and p102_running) else 0.0
            shunt = v101.position / 100.0

            ambient = 20.0

            if not plant_auto_run:
                # kall vila
                tt101.value += (ambient - tt101.value) * 0.05 + random.uniform(-0.05, 0.05)
                pt101.value += (0.8 - pt101.value) * 0.08 + random.uniform(-0.02, 0.02)

                ft201.value += (0.0 - ft201.value) * 0.25 + random.uniform(-1.0, 1.0)

                tt201.value += (ambient - tt201.value) * 0.08 + random.uniform(-0.08, 0.08)
                tt202.value += (ambient - tt202.value) * 0.08 + random.uniform(-0.08, 0.08)

                pt201.value += (0.7 - pt201.value) * 0.08 + random.uniform(-0.02, 0.02)
                pt202.value += (0.6 - pt202.value) * 0.08 + random.uniform(-0.02, 0.02)

                lt301.value += (55.0 - lt301.value) * 0.03 + random.uniform(-0.05, 0.05)
                tt301.value += (ambient + 10.0 - tt301.value) * 0.04 + random.uniform(-0.05, 0.05)
                tt302.value += (ambient + 5.0 - tt302.value) * 0.04 + random.uniform(-0.05, 0.05)

            else:
                # Boiler temp
                tt101.value += (boiler_sp - tt101.value) * 0.08 * max(0.2, burner_power)
                tt101.value -= 0.12 if burner_power < 0.5 else 0.0
                tt101.value += random.uniform(-tt101.noise_step, tt101.noise_step)

                # Boiler pressure
                pt101.value = 1.3 + (tt101.value / 100.0) * 0.9 + pump_factor * 0.25 + random.uniform(-0.04, 0.04)

                # Flow
                target_flow = 0.0 if pump_factor == 0.0 else 650.0 + 300.0 * shunt
                ft201.value += (target_flow - ft201.value) * 0.18 + random.uniform(-ft201.noise_step, ft201.noise_step)

                # Supply and return temperatures
                tt201_target = (tt101.value * (0.55 + 0.35 * shunt)) - (2.0 if not demand else 0.0)
                tt201.value += (tt201_target - tt201.value) * 0.20 + random.uniform(-tt201.noise_step, tt201.noise_step)

                heat_load = clamp((15.0 - outside) / 30.0, 0.1, 1.0) if demand else 0.05
                tt202_target = tt201.value - (10.0 + 12.0 * heat_load)
                tt202.value += (tt202_target - tt202.value) * 0.18 + random.uniform(-tt202.noise_step, tt202.noise_step)

                # Line pressures
                pt201.value = 1.4 + pump_factor * 0.9 + (ft201.value / 2000.0) * 0.5 + random.uniform(-0.05, 0.05)
                pt202.value = pt201.value - 0.35 + random.uniform(-0.04, 0.04)

                # Tank
                charging = max(0.0, (tt101.value - tt202.value) / 50.0) * pump_factor
                lt301.value += (charging - 0.35) * 0.3 + random.uniform(-lt301.noise_step, lt301.noise_step)
                tt301.value += ((tt101.value - 2.0) - tt301.value) * (0.06 * charging) + random.uniform(-tt301.noise_step, tt301.noise_step)
                tt301.value -= 0.04 if charging < 0.2 else 0.0
                tt302.value += ((tt202.value + 3.0) - tt302.value) * 0.07 + random.uniform(-tt302.noise_step, tt302.noise_step)

            for point in analogs:
                await apply_latched_alarms(point)

            common_alarm_value = False
            for point in analogs:
                if bool(await point.low_alarm_node.read_value()) or bool(await point.high_alarm_node.read_value()):
                    common_alarm_value = True
                    break

            for device in status_devices:
                if bool(await device.fault_node.read_value()):
                    common_alarm_value = True
                    break

            if bool(await v101.fault_node.read_value()):
                common_alarm_value = True

            await common_alarm.write_value(ua.Variant(bool(common_alarm_value), ua.VariantType.Boolean))

            _logger.info(
                "AutoRun=%d | BK101 %.1f C | TT201 %.1f C | TT202 %.1f C | FT201 %.0f | V101 %.0f%% | LT301 %.1f%% | Alarm=%d",
                int(plant_auto_run), tt101.value, tt201.value, tt202.value, ft201.value, v101.position, lt301.value, int(common_alarm_value)
            )

            await asyncio.sleep(UPDATE_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped")