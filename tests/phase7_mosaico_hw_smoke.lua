local board_manager=require("board_manager")
local board=require("boards.mosaico")


local info=board_manager.get_board_info()
print("board:",info and info.name,info and info.chip,info and info.version)


local ok,err=board_manager.init_device(board.display.lcd_device)
assert(ok,err)


local panel,io,width,height,panel_if,pixel_format=
    board_manager.get_display_lcd_params(board.display.lcd_device)
assert(panel,"missing LCD panel handle")
assert(width==480 and height==480,"unexpected Mosaico LCD size")
print("display:",width,height,panel_if,pixel_format)


local tok,terr=board_manager.init_device(board.display.touch_device)
assert(tok,terr)
local touch=board_manager.get_lcd_touch_handle(board.display.touch_device)
assert(touch,"missing Mosaico touch handle")
print("touch handle: OK")
print("phase7_mosaico_hw_smoke: PASS")