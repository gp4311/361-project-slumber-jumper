import dbus
import dbus.mainloop.glib
import dbus.service
from gi.repository import GLib
import time
import threading
import json

BLUEZ_SERVICE_NAME = 'org.bluez'
ADAPTER_IFACE = 'org.bluez.Adapter1'
GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
GATT_CHRC_IFACE = 'org.bluez.GattCharacteristic1'

SERVICE_UUID = '12345678-1234-5678-1234-56789abcdef0'
CHAR_UUID = '12345678-1234-5678-1234-56789abcdef1'
ADVERTISING_PATH = '/org/bluez/example/advertisement0'
DEVICE_NAME = 'PiBLE'

mainloop = None

class Advertisement(dbus.service.Object):
    def __init__(self, bus, index):
        self.path = f'/org/bluez/example/advertisement{index}'
        self.bus = bus
        self.ad_type = 'peripheral'
        self.service_uuids = [SERVICE_UUID]
        self.local_name = DEVICE_NAME
        self.includes = ['tx-power']
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_properties(self):
        return {
            'org.bluez.LEAdvertisement1': {
                'Type': self.ad_type,
                'ServiceUUIDs': self.service_uuids,
                'LocalName': self.local_name,
                'Includes': self.includes
            }
        }

    @dbus.service.method('org.freedesktop.DBus.Properties', in_signature='ss', out_signature='v')
    def Get(self, interface, prop):
        return self.get_properties()[interface][prop]

    @dbus.service.method('org.freedesktop.DBus.Properties', in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        return self.get_properties()[interface]

    @dbus.service.method('org.bluez.LEAdvertisement1')
    def Release(self):
        print("Advertisement released")


class Application(dbus.service.Object):
    def __init__(self, bus):
        self.path = '/org/bluez/example'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            for char in service.characteristics:
                response[char.get_path()] = char.get_properties()
        return response


class Service(dbus.service.Object):
    def __init__(self, bus, index):
        self.path = f"/org/bluez/example/service{index}"
        self.bus = bus
        self.uuid = SERVICE_UUID
        self.primary = True
        self.characteristics = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_properties(self):
        return {
            'org.bluez.GattService1': {
                'UUID': self.uuid,
                'Primary': self.primary
            }
        }


class Characteristic(dbus.service.Object):
    def __init__(self, bus, index, service):
        self.path = service.get_path() + f"/char{index}"
        self.bus = bus
        self.uuid = CHAR_UUID
        self.service = service
        self.notifying = False
        self.value = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_properties(self):
        return {
            GATT_CHRC_IFACE: {
                'UUID': self.uuid,
                'Service': self.service.get_path(),
                'Flags': ['notify'],
                'Notifying': self.notifying
            }
        }

    def send_notification(self, message):
        self.value = [dbus.Byte(c.encode()) for c in message]
        if self.notifying:
            self.PropertiesChanged(
                GATT_CHRC_IFACE,
                {'Value': self.value}, [])

    @dbus.service.method(GATT_CHRC_IFACE)
    def StartNotify(self):
        self.notifying = True

    @dbus.service.method(GATT_CHRC_IFACE)
    def StopNotify(self):
        self.notifying = False

    @dbus.service.signal('org.freedesktop.DBus.Properties', signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass


def send_from_queue(queue, characteristic):
    while True:
        if not queue.empty():
            msg = queue.get()

            # Convert dict to JSON string
            try:
                json_msg = json.dumps(msg)
                print("BLE Sending:", json_msg)
                characteristic.send_notification(json_msg)
            except Exception as e:
                print("Error sending BLE message:", e)

        time.sleep(1)  # Slight delay to prevent busy looping


def main(queue):
    global mainloop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()

    adapter_path = '/org/bluez/hci0'
    adapter_props = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter_path), 'org.freedesktop.DBus.Properties')
    adapter_props.Set(ADAPTER_IFACE, 'Powered', dbus.Boolean(1))

    # Register GATT application
    app = Application(bus)
    service = Service(bus, 0)
    char = Characteristic(bus, 0, service)
    service.add_characteristic(char)
    app.add_service(service)

    gatt_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter_path), GATT_MANAGER_IFACE)
    gatt_manager.RegisterApplication(app.get_path(), {},
        reply_handler=lambda: print("GATT app registered"),
        error_handler=lambda e: print("Failed to register app:", e))

    # Register advertisement
    ad = Advertisement(bus, 0)
    ad_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter_path), LE_ADVERTISING_MANAGER_IFACE)
    ad_manager.RegisterAdvertisement(ad.get_path(), {},
        reply_handler=lambda: print("Advertisement registered"),
        error_handler=lambda e: print("Failed to register advertisement:", e))

    # Start queue-based BLE notifications
    threading.Thread(target=send_from_queue, args=(queue, char), daemon=True).start()

    # Run BLE event loop
    mainloop = GLib.MainLoop()
    mainloop.run()
