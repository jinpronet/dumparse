import parser_util

if parser_util.get_system_type() == 'Linux':
    gdb_path = “< replace ANDROID_SRC_PATH?>/prebuilts/gcc/linux-x86/arm/arm-eabi-4.7/bin/arm-eabi-gdb"
    nm_path = “< replace ANDROID_SRC_PATH?>/prebuilts/gcc/linux-x86/arm/arm-eabi-4.7/bin/arm-eabi-nm"
    gdb64_path = “<replace TOOLCHAIL_PATH>/gcc-linaro-aarch64-linux-gnu-4.8-2013.09_linux/bin/aarch64-linux-gnu-gdb"
    nm64_path = “<replace TOOLCHAIL_PATH>/gcc-linaro-aarch64-linux-gnu-4.8-2013.09_linux/bin/aarch64-linux-gnu-nm"
    objdump64_path = “<replace TOOLCHAIL_PATH>/gcc-linaro-aarch64-linux-gnu-4.8-2013.09_linux/bin/aarch64-linux-gnu-objdump"
else:
    #if not linux assume windows
    nm_path =  “D:\\software\\armgcc\\bin\\arm-none-eabi-nm.exe"
    gdb_path = “D:\\software\\armgcc\\bin\\arm-none-eabi-gdb.exe"