import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.getcwd())
import pygame
pygame.init()
from mrp_emu.api.dsmfuncs import DSM_FUNCS
from mrp_emu.api.mrtable import MR_TABLE
from mrp_emu.app import App
from mrp_emu.consts import KEY_SELECT
from mrp_emu.vm import Vm
from mrp_emu.ui.skin import load_skin
from mrp_emu.ui.phone import PhoneUI

R = "runtime"
vm = Vm(log=print)
app = App(vm, R, log=print)
vm.app = app
vm.install_tables(MR_TABLE, DSM_FUNCS)
vm.load_code(os.path.join(R, "cfunction.ext"))
vm.ext_init(); vm.dsm_init()
vm.start_dsm("dsm_gm.mrp", "start.mr", None)
for _ in range(6): vm.timer()
# 光标下移到推箱子 -> 确定 -> 在子菜单确定"启动应用"
vm.key_event(13, True); vm.key_event(13, False)
for _ in range(4): vm.timer()
vm.key_event(20, True); vm.key_event(20, False)
for _ in range(10): vm.timer()

ui = PhoneUI(load_skin(os.path.join(R, "skin.json")))
print(">>> 按启动应用")
h0, p0 = vm.mr_extHelper_addr, vm.mr_c_function_P
vm.key_event(20, True); vm.key_event(20, False)
for _ in range(60): vm.timer()
print(f">>> helper 0x{h0:X} -> 0x{vm.mr_extHelper_addr:X} | P 0x{p0:X} -> 0x{vm.mr_c_function_P:X}")
pygame.image.save(ui.draw(app.gfx.surface()), "out/launch_game.png")
print(">>> 继续跑 100 个 timer 后的稳定画面")
for _ in range(100): vm.timer()
pygame.image.save(ui.draw(app.gfx.surface()), "out/launch_game2.png")
print("done")
