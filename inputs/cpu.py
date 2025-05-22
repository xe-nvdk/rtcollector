import platform

if platform.system() == "Linux":
    from inputs.linux_cpu import collect
elif platform.system() == "Darwin":
    from inputs.macos_cpu import collect
else:
    def collect():
        return []