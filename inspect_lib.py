from mac_vendor_lookup import MacLookup
import asyncio
import inspect

print("Dir:", dir(MacLookup))
try:
    mac = MacLookup()
    print("Instance:", mac)
    try:
        res = mac.lookup("00:00:00:00:00:00")
        print("Sync lookup result:", res)
    except Exception as e:
        print("Sync lookup failed:", e)
        if hasattr(mac, 'lookup'):
            print("Lookup is:", mac.lookup)
            if inspect.iscoroutinefunction(mac.lookup):
                print("It is a coroutine function")
                try:
                    res = asyncio.run(mac.lookup("00:00:00:00:00:00"))
                    print("Async lookup result:", res)
                except Exception as ex:
                    print("Async lookup failed:", ex)
            else:
                print("It is NOT a coroutine function")
except Exception as e:
    print("Overall failure:", e)
