from ..errors import errors, warnings

try: 
    import webcolors
except ImportError: 
    warnings.NotInstaledWarning("webcolors")
    webcolors = None

class Color(str):
    def __new__(cls, value):
        if isinstance(value, str):
            hex_value = value.lstrip("#").upper()
            
            if len(hex_value) != 6:
                raise errors.ColorsError("Invalid hex")
            
            obj = super().__new__(cls, f"#{hex_value}")
            obj._hex = hex_value
            obj._rgb = tuple(int(hex_value[i:i+2], 16) for i in (0, 2, 4))
            
            return obj

        elif isinstance(value, (tuple, list)) and len(value) == 3:
            if not all(0 <= v <= 255 for v in value):
                raise errors.ColorsError("RGB values should be between 0 and 255.")
            
            hex_value = "".join(f"{v:02X}" for v in value)
            obj = super().__new__(cls, f"#{hex_value}")
            obj._hex = hex_value
            obj._rgb = tuple(value)
            
            return obj

        elif isinstance(value, int):
            if not (0 <= value <= 0xFFFFFF):
                raise errors.ColorsError("Int24 must be between 0x000000 and 0xFFFFFF")
            
            r = (value >> 16) & 0xFF
            g = (value >> 8) & 0xFF
            b = value & 0xFF
            hex_value = f"{r:02X}{g:02X}{b:02X}"
            obj = super().__new__(cls, f"#{hex_value}")
            obj._hex, obj._rgb = hex_value, (r, g, b)
            
            return obj

        else:
            raise errors.ColorsError("The value must be a string (hex) or a tuple/list (RGB).")

    @property
    def hex(self) -> str:
        return f"#{self._hex}"

    @property
    def rgb(self) -> tuple[int, int, int]:
        return self._rgb
        
    @property
    def int24(self) -> int:
        r, g, b = self._rgb
        return (r << 16) | (g << 8) | b

    @property
    def bytes(self) -> bytes:
        return bytes(self._rgb)

    @property
    def brightness(self) -> float:
        r, g, b = self._rgb
        return 0.2126*r + 0.7152*g + 0.0722*b

    @property
    def is_dark(self) -> bool:
        return self.brightness < 128

    @property
    def name(self) -> str | None:
        try: 
            import webcolors
        except ImportError: 
            raise errors.NotInstaledError("webcolors")
            
        try:
            return webcolors.hex_to_name(self.hex)
        
        except ValueError:
            rgb = webcolors.hex_to_rgb(self.hex)
            min_diff = None
            closest = None
            
            for name, hex_code in webcolors.CSS3_NAMES_TO_HEX.items():
                r, g, b = webcolors.hex_to_rgb(hex_code)
                diff = (r - rgb.red)**2 + (g - rgb.green)**2 + (b - rgb.blue)**2
                
                if min_diff is None or diff < min_diff:
                    min_diff = diff
                    closest = name
            
            return f"Approximate name: '{closest}'"

    def __int__(self) -> int:
        return self.int24

    def __str__(self) -> str:
        return f"0x{self.int24:06X}"

    def __repr__(self):
        return (
            f"<Color "
            f"hex={self.hex or '#000000'} "
            f"rgb={self.rgb or (0, 0, 0)} "
            f"int24={str(self) or '0x000000'}>"
        )