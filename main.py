import asyncio
from baseus import BASEUS

"""
Command
anc {value:int,str}
*Set Active noise cancellation profile*
- 0-10 : ANC Intensity
- general
- indoor
- outdoor
- off : same as 0
- on : same as general
- transparent

quit
*Quit program*
"""


class APP:
    async def main(self):
        self.base = BASEUS()
        self.base.verbose = True
        await self.base.init()
        if self.base.address is None:
            print("[INFO] No Baseus Bowie MA10 Pro found!")
            print("[INFO] Quitting!")
            return
        while True:
            out = await asyncio.to_thread(input, f"[{self.base.address}] ")
            out = out.split(" ")
            match out[0]:
                case "anc":
                    await self.base.anc(out[1])
                case "read":
                    await self.base.read(out[1])
                case "quit" | "exit":
                    break
                case "battery":
                    batt = await self.base.get_battery()
                    if batt is None:
                        break
                    print(f"Left  :{batt[0]}")
                    print(f"Right :{batt[2]}")
                    print(f"Case  :{batt[1]}")
                case "help":
                    print("anc {value:int|str}")
                    print(" Sets ANC profile")
                    print("     0-10 : ANC Intensity")
                    print("     off : same as 0")
                    print("     on : same as 1")
                    print("     general")
                    print("     indoor")
                    print("     outdoor")
                    print("     transparent")
                    print("quit")
                    print(" quit program")
                    print("help")
                    print(" print help")
                case "write":
                    await self.base.write(out[1])
                case _:
                    print("Invalid command")
        print("[INFO] Cleaning up")
        await self.base.exit()


if __name__ == "__main__":
    asyncio.run(APP().main())
