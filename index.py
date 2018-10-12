#!/usr/bin/env python3
import re
import sys
from enum import Enum
from fontTools.ttLib import TTFont


# Reference https://docs.microsoft.com/en-us/typography/opentype/spec/os2#usweightclass
class FontWeight(Enum):
    Thin = 100
    ExtraLight = 200  # aka UltraLight
    Light = 300
    Normal = 400  # aka Regular
    Medium = 500
    SemiBold = 600  # aka DemiBold
    Bold = 700
    ExtraBold = 800  # aka UltraBold
    Black = 900  # aka Heavy
    ExtraBlack = 950  # aka UltraBlack


class FontWidth(Enum):
    # Name = 1000ths of normal
    UltraCondensed = 500
    ExtraCondensed = 625  # aka Compressed, but not always
    Condensed = 750
    SemiCondensed = 875
    Medium = 100  # aka Normal
    SemiExpanded = 1125
    Expanded = 1250
    ExtraExpanded = 1500
    UltraExpanded = 2000


class Platform(Enum):
    Unicode = 0
    Mac = 1
    ISO = 2  # deprecated
    Windows = 3
    Custom = 4


class WindowsEncoding(Enum):
    Symbol = 0
    Utf16 = 1  # actually, UCS-2
    Utf32 = 10


class MacEncoding(Enum):
    Roman = 0


class WindowsLanguage(Enum):
    ArabicJordan = 0x2C01
    ArabicSaudi = 0x0401
    English = 0x0409


class MacLanguage(Enum):
    English = 0
    French = 1
    Arabic = 12


class Name(Enum):
    Copyright = 0
    Family = 1
    Subfamily = 2
    Unique = 3
    FullFont = 4  # human-readable
    Version = 5
    PostScript = 6
    Trademark = 7
    Manufacturer = 8
    Designer = 9
    Description = 10
    VendorUrl = 11
    DesignerUrl = 12
    License = 13
    LicenseUrl = 14
    Reserved = 15
    TypographicFamily = 16  # aka Preferred Family
    TypographicSubfamily = 17  # aka Preferred Subfamily
    CompatibleFull = 18
    SampleText = 19
    PostScriptCid = 20
    WwsFamily = 21
    WwsSubfamily = 22
    LightBackgroundPalette = 23
    DarkBackgroundPalette = 24
    VariationsPostScriptPrefix = 25


class FontProperties:
    def Seed(self, seed):
        self._seed = seed


class FontUtils:
    def __init__(font):
        self._font = font

    def ValidateNames():
        names = self._font.get("name")


def shrink(name):
    return (
        name.replace(" ", "")
        .replace("ExtraLight", "XLight")
        .replace("ExtraBold", "XBold")
        .replace("UltraLight", "ULight")
        .replace("UltraBold", "UBold")
    )


# Removes the "Regular" portion from a (sub)family name
def removeRegular(name):
    return name.replace("Regular", "").replace("  ", " ").strip()


def fixNames(font, baseName=""):
    name = font.get("name")

    if len(baseName) == 0:
        baseName = "{0}".format(
            name.getName(
                Name.Family, Platform.Mac, MacEncoding.Roman, MacLanguage.English
            )
        )
    classPlusStyle = name.getName(
        Name.Subfamily, Platform.Mac, MacEncoding.Roman, MacLanguage.English
    )

    # baseName must not include things like "Regular"
    assert removeRegular(baseName) == baseName

    className = input("nameID2 is {0}, what is the class name? ".format(classPlusStyle))
    styleName = input("nameID2 is {0}, what is the style name? ".format(classPlusStyle))

    # FamilyName
    name.setName(
        "{0} {1}".format(baseName, className).strip().replace("  ", " "),
        Name.Family,
        Platform.Mac,
        MacEncoding.Roman,
        MacLanguage.English,
    )
    name.setName(
        "{0} {1} {2}".format(baseName, className, shrink(styleName)),
        Name.Family,
        Platform.Windows,
        WindowsEncoding.Utf16,
        WindowsLanguage.English,
    )

    # SubfamilyName
    name.setName(
        "{0}".format(styleName),
        Name.Subfamily,
        Platform.Mac,
        MacEncoding.Roman,
        MacLanguage.English,
    )

    # FullFontName
    name.setName(
        "{0}{1}-{2}".format(baseName, className, styleName),
        Name.FullFont,
        Platform.Windows,
        WindowsEncoding.Utf16,
        WindowsLanguage.English,
    )
    name.setName(
        "{0}{1}-{2}".format(baseName, className, styleName),
        Name.FullFont,
        Platform.Mac,
        MacEncoding.Roman,
        MacLanguage.English,
    )

    # PostScriptName
    name.setName(
        "{0}{1}-{2}".format(baseName, className, styleName),
        Name.PostScript,
        Platform.Mac,
        MacEncoding.Roman,
        MacLanguage.English,
    )
    name.setName(
        "{0}{1}-{2}".format(baseName, className, styleName),
        Name.PostScript,
        Platform.Windows,
        WindowsEncoding.Utf16,
        WindowsLanguage.English,
    )

    # TypographicFamily
    name.setName(
        "{0} {1}".format(baseName, removeRegular(className)).strip(),
        Name.TypographicFamily,
        Platform.Mac,
        MacEncoding.Roman,
        MacLanguage.English,
    )
    name.setName(
        "{0} {1}".format(baseName, className).strip(),
        Name.TypographicFamily,
        Platform.Windows,
        WindowsEncoding.Utf16,
        WindowsLanguage.English,
    )

    # TypographicSubfamily (Weight/Width/Slope)
    name.setName(
        "{0}".format(styleName),
        Name.TypographicSubfamily,
        Platform.Windows,
        WindowsEncoding.Utf16WindowsLanguage.English,
    )

    # CompatibleFullName (macOS-only drop-down menu name)
    name.setName(
        "{0} {1} {2}".format(baseName, className, shrink(className)).replace("  ", " "),
        Name.CompatibleFull,
        Platform.Mac,
        MacEncoding.Roman,
        MacLanguage.English,
    )

    # If name 17 contains non-WWS data (e.g. Caption, Display, etc.), set field 21 WwsFamilyName to
    # real family name + variant.
    name.setName(
        "", Name.WwsFamily, Platform.Mac, MacEncoding.Roman, MacLanguage.English
    )
    name.setName(
        "",
        Name.WwsFamily,
        Platform.Windows,
        WindowsEncoding.Utf16,
        WindowsLanguage.English,
    )

    # If name 17 contains non-WWS data (e.g. Caption, Display, etc.), repeat here with only WWS data
    name.setName(
        "", Name.WwsSubfamily, Platform.Mac, MacEncoding.Roman, MacLanguage.English
    )
    name.setName(
        "",
        Name.WwsSubfamily,
        Platform.Windows,
        WindowsEncoding.Utf16,
        WindowsLanguage.English,
    )

    name.compile(font)


def setSampleText(font, sampleText):
    name = font.get("name")

    name.setName(
        sampleText,
        Name.SampleText,
        Platform.Mac,
        MacEncoding.Roman,
        MacLanguage.English,
    )
    name.setName(
        sampleText,
        Name.SampleText,
        Platform.Windows,
        WindowsEncoding.Utf16,
        WindowsLanguage.English,
    )

    name.compile(font)


def removeNonEnglish(font):
    name = font.get("name")

    name.names = [
        x
        for x in name.names
        if (x.platformID == Platform.Mac and x.langID == MacLanguage.English)
        or (x.platformID == Platform.Windows and x.langID == WindowsLanguage.English)
    ]

    name.compile(font)


def main():
    inFile = sys.argv[1]
    outFile = "./Fixed/{0}".format(inFile)
    font = TTFont(inFile)
    print("Font: {0}".format(inFile))

    # fixNames(font, "Diwani")
    fixNames(font)
    removeNonEnglish(font)
    setSampleText(font, "Realigned equestrian fez bewilders picky monarch")

    font.save(outFile)


main()
