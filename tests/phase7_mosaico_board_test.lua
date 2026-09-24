local board=require("boards.mosaico")
assert(board.id=="mosaico")
assert(board.display.width==480 and board.display.height==480)
assert(board.i2c.addresses.bmi270==0x69)
assert(board.i2c.addresses.bmm150_1==0x11 and board.i2c.addresses.bmm150_2==0x12)
assert(board.i2c.addresses.bq27220==0x55)
for _,pin in ipairs({37,40,49,52,54}) do assert(board.audio_shared_gpio[pin]) end
for _,pin in ipairs({20,21,22,23,24,25,60}) do assert(board.hard_reserved_gpio[pin]) end
print("phase7_mosaico_board_test: PASS")