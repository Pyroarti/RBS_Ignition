import asyncio
import logging
import random
from dataclasses import dataclass

from asyncua import Server, ua


ENDPOINT = "opc.tcp://0.0.0.0:4842/scada-general/"
NAMESPACE_URI = "urn:local:scada:testserver"
UPDATE_INTERVAL_SECONDS = 1.0

STATUS_TEXT = {
    0: "Off",
    1: "Auto on",
    2: "Man off",
    3: "Man on",
    4: "Larm",
}

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger("scada_test_server")


@dataclass
class AnalogPoint:
    tag: str
    value_node: object
    low_node: object
    high_node: object
    low_alarm_node: object
    high_alarm_node: object
    min_value: float
    max_value: float
    max_step: float
    value: float


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


async def add_status_group(parent, idx: int, folder_name: str, prefix: str, start: int, end: int):
    """
    Skapar t.ex.:
      Objects/SCADA_Test/Pumps/P101/Status

    Status är skrivbar Int32.
    """
    folder = await parent.add_folder(idx, folder_name)
    nodes = {}

    for number in range(start, end + 1):
        tag = f"{prefix}{number}"
        obj = await folder.add_object(idx, tag)
        status = await obj.add_variable(
            idx,
            "Status",
            ua.Variant(0, ua.VariantType.Int32),
        )
        await status.set_writable()
        nodes[tag] = status

    return nodes

async def add_op_group(parent, idx: int, folder_name: str, prefix: str, start: int, end: int):
    """
    Skapar t.ex.:
      Objects/SCADA_Test/Pumps/P101/OP

    Status är skrivbar Int32.
    """
    folder = await parent.add_folder(idx, folder_name)
    nodes = {}

    for number in range(start, end + 1):
        tag = f"{prefix}{number}"
        obj = await folder.add_object(idx, tag)
        status = await obj.add_variable(
            idx,
            "OP",
            ua.Variant(0, ua.VariantType.Int32),
        )
        await status.set_writable()
        nodes[tag] = status

    return nodes


async def add_analog_group(
    parent,
    idx: int,
    folder_name: str,
    prefix: str,
    start: int,
    end: int,
    eng_low: float,
    eng_high: float,
    default_low_limit: float,
    default_high_limit: float,
    max_step: float,
):
    """
    Skapar t.ex.:
      Objects/SCADA_Test/Temperature/TT101/Value      (REAL, rör sig automatiskt)
      Objects/SCADA_Test/Temperature/TT101/LowLimit   (REAL, skrivbar)
      Objects/SCADA_Test/Temperature/TT101/HighLimit  (REAL, skrivbar)
      Objects/SCADA_Test/Temperature/TT101/LowAlarm   (BOOL, skrivbar reset från SCADA)
      Objects/SCADA_Test/Temperature/TT101/HighAlarm  (BOOL, skrivbar reset från SCADA)

    Larmen är latchade var för sig:
    - LowAlarm sätts True om Value < LowLimit
    - HighAlarm sätts True om Value > HighLimit
    - återställs INTE automatiskt när värdet går tillbaka inom gräns
    - kan återställas genom att SCADA skriver False
    - om värdet fortfarande ligger utanför gräns efter reset, sätts larmet True igen nästa cykel
    """
    folder = await parent.add_folder(idx, folder_name)
    points = {}

    for number in range(start, end + 1):
        tag = f"{prefix}{number}"
        obj = await folder.add_object(idx, tag)

        start_value = round(random.uniform(default_low_limit, default_high_limit), 2)

        value_node = await obj.add_variable(
            idx,
            "Value",
            ua.Variant(float(start_value), ua.VariantType.Float),
        )
        low_node = await obj.add_variable(
            idx,
            "LowLimit",
            ua.Variant(float(default_low_limit), ua.VariantType.Float),
        )
        high_node = await obj.add_variable(
            idx,
            "HighLimit",
            ua.Variant(float(default_high_limit), ua.VariantType.Float),
        )
        low_alarm_node = await obj.add_variable(
            idx,
            "LowAlarm",
            ua.Variant(False, ua.VariantType.Boolean),
        )
        high_alarm_node = await obj.add_variable(
            idx,
            "HighAlarm",
            ua.Variant(False, ua.VariantType.Boolean),
        )

        await low_node.set_writable()
        await high_node.set_writable()
        await low_alarm_node.set_writable()
        await high_alarm_node.set_writable()

        points[tag] = AnalogPoint(
            tag=tag,
            value_node=value_node,
            low_node=low_node,
            high_node=high_node,
            low_alarm_node=low_alarm_node,
            high_alarm_node=high_alarm_node,
            min_value=float(eng_low),
            max_value=float(eng_high),
            max_step=float(max_step),
            value=float(start_value),
        )

    return points


async def simulate_process(analog_points: dict[str, AnalogPoint]):
    """
    Samma upplägg som i ditt gamla exempel:
    - while True
    - ändra processvärden lite
    - skriv ut med await node.write_value(...)
    - sleep 1 sekund

    För varje analog signal läses LowLimit, HighLimit, LowAlarm och HighAlarm
    varje cykel, så att skrivningar från SCADA slår igenom direkt.
    """
    while True:
        sample_text = []

        for point in analog_points.values():
            low_limit = float(await point.low_node.read_value())
            high_limit = float(await point.high_node.read_value())
            low_alarm_active = bool(await point.low_alarm_node.read_value())
            high_alarm_active = bool(await point.high_alarm_node.read_value())

            point.value += random.uniform(-point.max_step, point.max_step)
            point.value = clamp(point.value, point.min_value, point.max_value)
            point.value = round(point.value, 2)

            await point.value_node.write_value(
                ua.Variant(float(point.value), ua.VariantType.Float)
            )

            if point.value < low_limit and not low_alarm_active:
                await point.low_alarm_node.write_value(
                    ua.Variant(True, ua.VariantType.Boolean)
                )
                low_alarm_active = True

            if point.value > high_limit and not high_alarm_active:
                await point.high_alarm_node.write_value(
                    ua.Variant(True, ua.VariantType.Boolean)
                )
                high_alarm_active = True

            if point.tag in {"TT101", "PT101", "FT101", "LT101"}:
                sample_text.append(
                    f"{point.tag}={point.value:.2f} "
                    f"(LL={low_limit:.2f}, HL={high_limit:.2f}, "
                    f"LALM={int(low_alarm_active)}, HALM={int(high_alarm_active)})"
                )

        if sample_text:
            _logger.info(" | ".join(sample_text))

        await asyncio.sleep(UPDATE_INTERVAL_SECONDS)


async def main():
    server = Server()
    await server.init()

    server.set_endpoint(ENDPOINT)
    server.set_server_name("Open SCADA Test Server")

    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    if hasattr(server, "set_identity_tokens") and hasattr(ua, "AnonymousIdentityToken"):
        server.set_identity_tokens([ua.AnonymousIdentityToken])
    elif hasattr(server, "set_security_IDs"):
        server.set_security_IDs(["Anonymous"])

    server.allow_remote_admin(False)

    idx = await server.register_namespace(NAMESPACE_URI)
    scada_root = await server.nodes.objects.add_object(idx, "SCADA_Test")

    pump_nodes = await add_status_group(scada_root, idx, "Pumps", "P", 101, 110)
    motor_nodes = await add_status_group(scada_root, idx, "Motors", "M", 101, 110)
    valve_nodes = await add_status_group(scada_root, idx, "Valves", "V", 101, 110)
    valve_op_nodes = await add_op_group(scada_root, idx, "Valves_OP", "V_OP", 101, 110)

    analog_points = {}
    analog_points.update(
        await add_analog_group(
            scada_root,
            idx,
            "Temperature",
            "TT",
            101,
            110,
            0.0,
            100.0,
            10.0,
            90.0,
            0.8,
        )
    )
    analog_points.update(
        await add_analog_group(
            scada_root,
            idx,
            "Pressure",
            "PT",
            101,
            110,
            0.0,
            16.0,
            2.0,
            18.0,
            0.2,
        )
    )
    analog_points.update(
        await add_analog_group(
            scada_root,
            idx,
            "Flow",
            "FT",
            101,
            110,
            0.0,
            2000.0,
            100.0,
            1800.0,
            35.0,
        )
    )
    analog_points.update(
        await add_analog_group(
            scada_root,
            idx,
            "Level",
            "LT",
            101,
            105,
            0.0,
            100.0,
            20.0,
            80.0,
            1.0,
        )
    )

    analog_points.update(
        await add_analog_group(
            scada_root,
            idx,
            "Ampere",
            "Amp",
            101,
            105,
            0.0,
            10.0,
            2.0,
            9.0,
            0.1,
        )
    )

    vars = {
        "pumps": pump_nodes,
        "motors": motor_nodes,
        "valves": valve_nodes,
        "analogs": analog_points,
        "valves_op": valve_op_nodes
    }

    _logger.info("Server startad: %s", ENDPOINT)
    _logger.info("Root object: Objects/SCADA_Test")
    _logger.info("Status mapping: 0=Off, 1=Auto on, 2=Man off, 3=Man on, 4=Larm")
    _logger.info(
        "Antal statuspunkter: Pumps=%d Motors=%d Valves=%d",
        len(vars["pumps"]),
        len(vars["motors"]),
        len(vars["valves"]),
    )
    _logger.info("Antal analoga punkter: %d", len(vars["analogs"]))
    _logger.info(
        "Analoglarm: LowAlarm och HighAlarm är latchade och resetas från SCADA"
    )

    async with server:
        await simulate_process(vars["analogs"])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped")