import asyncio
import logging
import random
from dataclasses import dataclass

from asyncua import Server, ua

ENDPOINT = "opc.tcp://0.0.0.0:4841/scada-pumpstation/"
NAMESPACE_URI = "urn:local:scada:pumpstation"
UPDATE_INTERVAL_SECONDS = 1.0

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("pumpstation_test_server")


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


@dataclass
class PumpDevice:
    tag: str
    status_node: object
    start_cmd_node: object
    stop_cmd_node: object
    auto_mode_node: object
    running_fb_node: object
    available_node: object
    fault_node: object
    status: int = 0   # 0=Off, 1=Auto on, 2=Man off, 3=Man on, 4=Alarm


@dataclass
class AnalogValue:
    tag: str
    value_node: object
    low_alarm_node: object
    high_alarm_node: object
    min_value: float
    max_value: float
    value: float


async def add_pump_device(parent, idx: int, tag: str, description: str, initial_status: int = 0):
    obj = await parent.add_object(idx, tag)
    await obj.add_variable(idx, "Description", ua.Variant(description, ua.VariantType.String))

    status = await obj.add_variable(idx, "Status", ua.Variant(initial_status, ua.VariantType.Int32))
    start_cmd = await obj.add_variable(idx, "StartCmd", ua.Variant(False, ua.VariantType.Boolean))
    stop_cmd = await obj.add_variable(idx, "StopCmd", ua.Variant(False, ua.VariantType.Boolean))
    auto_mode = await obj.add_variable(idx, "AutoMode", ua.Variant(True, ua.VariantType.Boolean))
    running_fb = await obj.add_variable(idx, "RunningFb", ua.Variant(False, ua.VariantType.Boolean))
    available = await obj.add_variable(idx, "Available", ua.Variant(True, ua.VariantType.Boolean))
    fault = await obj.add_variable(idx, "Fault", ua.Variant(False, ua.VariantType.Boolean))

    await status.set_writable()
    await start_cmd.set_writable()
    await stop_cmd.set_writable()
    await auto_mode.set_writable()
    await running_fb.set_writable()
    await available.set_writable()
    await fault.set_writable()

    return PumpDevice(
        tag=tag,
        status_node=status,
        start_cmd_node=start_cmd,
        stop_cmd_node=stop_cmd,
        auto_mode_node=auto_mode,
        running_fb_node=running_fb,
        available_node=available,
        fault_node=fault,
        status=initial_status,
    )


async def add_analog_value(parent, idx: int, tag: str, description: str, start_value: float,
                           eng_low: float, eng_high: float):
    obj = await parent.add_object(idx, tag)
    await obj.add_variable(idx, "Description", ua.Variant(description, ua.VariantType.String))

    value_node = await obj.add_variable(idx, "Value", ua.Variant(float(start_value), ua.VariantType.Float))
    low_alarm = await obj.add_variable(idx, "LowAlarm", ua.Variant(False, ua.VariantType.Boolean))
    high_alarm = await obj.add_variable(idx, "HighAlarm", ua.Variant(False, ua.VariantType.Boolean))

    await value_node.set_writable()
    await low_alarm.set_writable()
    await high_alarm.set_writable()

    return AnalogValue(
        tag=tag,
        value_node=value_node,
        low_alarm_node=low_alarm,
        high_alarm_node=high_alarm,
        min_value=float(eng_low),
        max_value=float(eng_high),
        value=float(start_value),
    )


async def simulate_pump(pump: PumpDevice, auto_run_request: bool):
    available = bool(await pump.available_node.read_value())
    fault = bool(await pump.fault_node.read_value())
    auto_mode = bool(await pump.auto_mode_node.read_value())
    start_cmd = bool(await pump.start_cmd_node.read_value())
    stop_cmd = bool(await pump.stop_cmd_node.read_value())

    if fault:
        pump.status = 4
    elif not available:
        pump.status = 0
    elif auto_mode:
        pump.status = 1 if auto_run_request else 0
    else:
        if start_cmd and not stop_cmd:
            pump.status = 3
        elif stop_cmd:
            pump.status = 2
        else:
            if pump.status not in (2, 3):
                pump.status = 2

    running = pump.status in (1, 3)

    await pump.status_node.write_value(ua.Variant(int(pump.status), ua.VariantType.Int32))
    await pump.running_fb_node.write_value(ua.Variant(bool(running), ua.VariantType.Boolean))
    await pump.start_cmd_node.write_value(ua.Variant(False, ua.VariantType.Boolean))
    await pump.stop_cmd_node.write_value(ua.Variant(False, ua.VariantType.Boolean))


async def main():
    server = Server()
    await server.init()

    server.set_endpoint(ENDPOINT)
    server.set_server_name("Simple Pump Station Test Server")
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    if hasattr(server, "set_identity_tokens") and hasattr(ua, "AnonymousIdentityToken"):
        server.set_identity_tokens([ua.AnonymousIdentityToken])
    elif hasattr(server, "set_security_IDs"):
        server.set_security_IDs(["Anonymous"])

    server.allow_remote_admin(False)

    idx = await server.register_namespace(NAMESPACE_URI)
    root = await server.nodes.objects.add_object(idx, "SCADA_PumpStation")

    plant_folder = await root.add_folder(idx, "Plant")
    pumps_folder = await root.add_folder(idx, "Pumps")
    tank_folder = await root.add_folder(idx, "Tank")
    process_folder = await root.add_folder(idx, "Process")

    # Plant / drift
    plant = await plant_folder.add_object(idx, "PST001")
    plant_mode = await plant.add_variable(idx, "PlantMode", ua.Variant(1, ua.VariantType.Int32))  # 1=Auto
    common_alarm = await plant.add_variable(idx, "CommonAlarm", ua.Variant(False, ua.VariantType.Boolean))
    duty_pump = await plant.add_variable(idx, "DutyPump", ua.Variant(1, ua.VariantType.Int32))    # 1=P101, 2=P102

    # Nivågränser
    level_low_sp = await plant.add_variable(idx, "LevelLowSP", ua.Variant(35.0, ua.VariantType.Float))
    level_high_sp = await plant.add_variable(idx, "LevelHighSP", ua.Variant(70.0, ua.VariantType.Float))
    level_hh_sp = await plant.add_variable(idx, "LevelHighHighSP", ua.Variant(90.0, ua.VariantType.Float))

    # Processparametrar
    inflow_rate = await plant.add_variable(idx, "InflowRate", ua.Variant(8.0, ua.VariantType.Float))
    pump_capacity = await plant.add_variable(idx, "PumpCapacity", ua.Variant(12.0, ua.VariantType.Float))

    for n in [plant_mode, common_alarm, duty_pump, level_low_sp, level_high_sp, level_hh_sp, inflow_rate, pump_capacity]:
        await n.set_writable()

    # Pumpar
    p101 = await add_pump_device(pumps_folder, idx, "P101", "Pump 1", 0)
    p102 = await add_pump_device(pumps_folder, idx, "P102", "Pump 2", 0)

    # Analogvärden
    lt101 = await add_analog_value(tank_folder, idx, "LT101", "Niva i pumpbrunn", 50.0, 0.0, 100.0)
    fit101 = await add_analog_value(process_folder, idx, "FIT101", "Inkommande flode", 8.0, 0.0, 50.0)
    fit102 = await add_analog_value(process_folder, idx, "FIT102", "Utgaende flode", 0.0, 0.0, 50.0)

    pumps = [p101, p102]

    _logger.info("Server startad: %s", ENDPOINT)
    _logger.info("Root object: Objects/SCADA_PumpStation")

    last_all_stopped = True

    async with server:
        while True:
            mode = int(await plant_mode.read_value())
            low_sp = float(await level_low_sp.read_value())
            high_sp = float(await level_high_sp.read_value())
            hh_sp = float(await level_hh_sp.read_value())
            inflow = float(await inflow_rate.read_value())
            capacity = float(await pump_capacity.read_value())
            duty = int(await duty_pump.read_value())

            lt101.value = float(await lt101.value_node.read_value())

            auto_enabled = mode == 1

            # Auto-begäran
            p101_auto_req = False
            p102_auto_req = False

            if auto_enabled:
                if lt101.value >= hh_sp:
                    p101_auto_req = True
                    p102_auto_req = True
                elif lt101.value >= high_sp:
                    if duty == 1:
                        p101_auto_req = True
                    else:
                        p102_auto_req = True
                elif lt101.value <= low_sp:
                    p101_auto_req = False
                    p102_auto_req = False
                else:
                    # mellan low och high: behåll aktiv duty-pump igång om någon redan går
                    if bool(await p101.running_fb_node.read_value()):
                        p101_auto_req = True
                    if bool(await p102.running_fb_node.read_value()):
                        p102_auto_req = True

            await simulate_pump(p101, p101_auto_req)
            await simulate_pump(p102, p102_auto_req)

            p101_running = bool(await p101.running_fb_node.read_value())
            p102_running = bool(await p102.running_fb_node.read_value())
            running_count = int(p101_running) + int(p102_running)

            # Alternans: byt duty när båda varit stoppade efter en körning
            all_stopped = running_count == 0
            if last_all_stopped is False and all_stopped:
                new_duty = 2 if duty == 1 else 1
                await duty_pump.write_value(ua.Variant(new_duty, ua.VariantType.Int32))
                duty = new_duty
            last_all_stopped = all_stopped

            # Flöden
            fit101.value = inflow + random.uniform(-0.4, 0.4)
            fit102.value = running_count * capacity + random.uniform(-0.6, 0.6)

            # Nivåsimulering
            level_change = (fit101.value - fit102.value) * 0.20
            lt101.value += level_change + random.uniform(-0.15, 0.15)
            lt101.value = clamp(lt101.value, lt101.min_value, lt101.max_value)

            # Alarm
            low_alarm = lt101.value < 10.0
            high_alarm = lt101.value >= hh_sp

            await lt101.value_node.write_value(ua.Variant(float(round(lt101.value, 2)), ua.VariantType.Float))
            await fit101.value_node.write_value(ua.Variant(float(round(clamp(fit101.value, 0.0, 50.0), 2)), ua.VariantType.Float))
            await fit102.value_node.write_value(ua.Variant(float(round(clamp(fit102.value, 0.0, 50.0), 2)), ua.VariantType.Float))

            await lt101.low_alarm_node.write_value(ua.Variant(bool(low_alarm), ua.VariantType.Boolean))
            await lt101.high_alarm_node.write_value(ua.Variant(bool(high_alarm), ua.VariantType.Boolean))

            common_alarm_value = low_alarm or high_alarm
            for pump in pumps:
                if bool(await pump.fault_node.read_value()):
                    common_alarm_value = True
                    break

            await common_alarm.write_value(ua.Variant(bool(common_alarm_value), ua.VariantType.Boolean))

            _logger.info(
                "Mode=%d | LT101=%.1f %% | P101=%d | P102=%d | Duty=%d | In=%.1f | Out=%.1f | Alarm=%d",
                mode,
                lt101.value,
                int(p101_running),
                int(p102_running),
                duty,
                fit101.value,
                fit102.value,
                int(common_alarm_value),
            )

            await asyncio.sleep(UPDATE_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPump station server stopped")