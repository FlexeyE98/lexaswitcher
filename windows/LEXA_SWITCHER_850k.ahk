#Requires AutoHotkey v2.0
#SingleInstance Force
Persistent

global APP_NAME := "LEXA_SWITCHER_850k"
global EN_HKL := "00000409"
global RU_HKL := "00000419"
global WM_INPUTLANGCHANGEREQUEST := 0x0050

global gEnabled := true
global gInternalSend := false
global gTypedBuffer := ""
global gForwardLayoutMap := Map()
global gReverseLayoutMap := Map()
global gProjectRoot := A_ScriptDir "\.."
global gConfigPath := gProjectRoot "\config\config.ini"
global gInputHook := 0
global gLastActiveHwnd := 0

global gMaxBufferLength := 400

Initialize()
return

Initialize() {
    BuildLayoutMaps()
    BuildTray()
    StartInputMonitor()
    TrayTip(APP_NAME, "Ready: Right Shift converts typed sentence", 1)
}

BuildTray() {
    global APP_NAME, gEnabled, gConfigPath

    A_TrayMenu.Delete()
    A_TrayMenu.Add(APP_NAME " " (gEnabled ? "ON" : "OFF"), ToggleEnabled)
    A_TrayMenu.Add("Show hotkeys", ShowHotkeys)
    A_TrayMenu.Add()
    A_TrayMenu.Add("Edit config.ini", (*) => Run('notepad.exe "' gConfigPath '"'))
    A_TrayMenu.Add("Exit", (*) => ExitApp())
    A_TrayMenu.Default := APP_NAME " " (gEnabled ? "ON" : "OFF")
    TraySetIcon("shell32.dll", 44)
}

ShowHotkeys(*) {
    MsgBox("Right Shift - convert the whole recently typed sentence`nCtrl+Alt+Pause - enable or disable script", APP_NAME)
}

ToggleEnabled(*) {
    global gEnabled

    gEnabled := !gEnabled
    BuildTray()
    TrayTip(APP_NAME, gEnabled ? "Enabled" : "Disabled", 1)
}

StartInputMonitor() {
    global gInputHook

    if IsObject(gInputHook) {
        try gInputHook.Stop()
        catch {
        }
    }

    gInputHook := InputHook("V")
    gInputHook.KeyOpt("{Backspace}{Delete}{Left}{Right}{Up}{Down}{Home}{End}{PgUp}{PgDn}{Esc}{Enter}{Tab}", "N")
    gInputHook.OnChar := OnInputChar
    gInputHook.OnKeyDown := OnInputKeyDown
    gInputHook.Start()
}

OnInputChar(ih, char) {
    global gTypedBuffer, gInternalSend, gMaxBufferLength

    if gInternalSend
        return

    ResetBufferIfWindowChanged()
    gTypedBuffer .= char

    ; Sentence boundary: keep only the current phrase fragment.
    if RegExMatch(char, "[.!?]") {
        gTypedBuffer := ""
        return
    }

    if StrLen(gTypedBuffer) > gMaxBufferLength
        gTypedBuffer := SubStr(gTypedBuffer, -199)
}

OnInputKeyDown(ih, vk, sc) {
    global gTypedBuffer, gInternalSend

    if gInternalSend
        return

    ResetBufferIfWindowChanged()
    keyName := GetKeyName(Format("vk{:x}sc{:x}", vk, sc))

    if keyName = "Backspace" {
        if gTypedBuffer != ""
            gTypedBuffer := SubStr(gTypedBuffer, 1, -1)
        return
    }

    if RegExMatch(keyName, "^(Delete|Left|Right|Up|Down|Home|End|PgUp|PgDn|Esc|Enter|Tab)$")
        gTypedBuffer := ""
}

ConvertTypedSentence() {
    global gEnabled, gInternalSend, gTypedBuffer

    if !gEnabled || gInternalSend
        return

    ResetBufferIfWindowChanged()
    source := Trim(gTypedBuffer, " `t`r`n")
    if source = ""
        return

    converted := ConvertPreservingCase(source)
    if converted = source
        return

    leadingSpaces := GetLeadingWhitespace(gTypedBuffer)
    trailingSpaces := GetTrailingWhitespace(gTypedBuffer)

    gInternalSend := true
    try {
        Send("{Backspace " StrLen(gTypedBuffer) "}")
        SendText(leadingSpaces converted trailingSpaces)
    } finally {
        gInternalSend := false
    }

    ; Do not carry converted text into the next conversion cycle.
    gTypedBuffer := ""
    SwitchLayoutForText(converted)
    TrayTip(APP_NAME, converted, 1)
}

ResetBufferIfWindowChanged() {
    global gTypedBuffer, gLastActiveHwnd

    hwnd := WinActive("A")
    if !hwnd
        return

    if gLastActiveHwnd = 0 {
        gLastActiveHwnd := hwnd
        return
    }

    if hwnd != gLastActiveHwnd
        gTypedBuffer := ""

    gLastActiveHwnd := hwnd
}

GetLeadingWhitespace(text) {
    if RegExMatch(text, "^\s+")
        return RegExReplace(text, "^(\s+).*$", "$1")
    return ""
}

GetTrailingWhitespace(text) {
    if RegExMatch(text, "\s+$")
        return RegExReplace(text, "^.*?(\s+)$", "$1")
    return ""
}

ConvertPreservingCase(text) {
    result := ""
    token := ""

    for _, char in StrSplit(text) {
        if RegExMatch(char, "[A-Za-zА-Яа-яЁё]")
            token .= char
        else {
            if token != "" {
                result .= StrLower(ConvertLayout(token))
                token := ""
            }
            result .= ConvertLayout(char)
        }
    }

    if token != ""
        result .= StrLower(ConvertLayout(token))
    return result
}

ConvertLayout(text) {
    global gForwardLayoutMap, gReverseLayoutMap

    result := ""
    for _, char in StrSplit(text) {
        if gForwardLayoutMap.Has(char)
            result .= gForwardLayoutMap[char]
        else if gReverseLayoutMap.Has(char)
            result .= gReverseLayoutMap[char]
        else
            result .= char
    }
    return result
}


BuildLayoutMaps() {
    global gForwardLayoutMap, gReverseLayoutMap

    gForwardLayoutMap := Map()
    gForwardLayoutMap["``"] := "ё"
    gForwardLayoutMap["~"] := "Ё"
    gForwardLayoutMap["q"] := "й"
    gForwardLayoutMap["Q"] := "Й"
    gForwardLayoutMap["w"] := "ц"
    gForwardLayoutMap["W"] := "Ц"
    gForwardLayoutMap["e"] := "у"
    gForwardLayoutMap["E"] := "У"
    gForwardLayoutMap["r"] := "к"
    gForwardLayoutMap["R"] := "К"
    gForwardLayoutMap["t"] := "е"
    gForwardLayoutMap["T"] := "Е"
    gForwardLayoutMap["y"] := "н"
    gForwardLayoutMap["Y"] := "Н"
    gForwardLayoutMap["u"] := "г"
    gForwardLayoutMap["U"] := "Г"
    gForwardLayoutMap["i"] := "ш"
    gForwardLayoutMap["I"] := "Ш"
    gForwardLayoutMap["o"] := "щ"
    gForwardLayoutMap["O"] := "Щ"
    gForwardLayoutMap["p"] := "з"
    gForwardLayoutMap["P"] := "З"
    gForwardLayoutMap["["] := "х"
    gForwardLayoutMap["{"] := "Х"
    gForwardLayoutMap["]"] := "ъ"
    gForwardLayoutMap["}"] := "Ъ"
    gForwardLayoutMap["a"] := "ф"
    gForwardLayoutMap["A"] := "Ф"
    gForwardLayoutMap["s"] := "ы"
    gForwardLayoutMap["S"] := "Ы"
    gForwardLayoutMap["d"] := "в"
    gForwardLayoutMap["D"] := "В"
    gForwardLayoutMap["f"] := "а"
    gForwardLayoutMap["F"] := "А"
    gForwardLayoutMap["g"] := "п"
    gForwardLayoutMap["G"] := "П"
    gForwardLayoutMap["h"] := "р"
    gForwardLayoutMap["H"] := "Р"
    gForwardLayoutMap["j"] := "о"
    gForwardLayoutMap["J"] := "О"
    gForwardLayoutMap["k"] := "л"
    gForwardLayoutMap["K"] := "Л"
    gForwardLayoutMap["l"] := "д"
    gForwardLayoutMap["L"] := "Д"
    gForwardLayoutMap[";"] := "ж"
    gForwardLayoutMap[":"] := "Ж"
    gForwardLayoutMap["'"] := "э"
    gForwardLayoutMap[Chr(34)] := "Э"
    gForwardLayoutMap["z"] := "я"
    gForwardLayoutMap["Z"] := "Я"
    gForwardLayoutMap["x"] := "ч"
    gForwardLayoutMap["X"] := "Ч"
    gForwardLayoutMap["c"] := "с"
    gForwardLayoutMap["C"] := "С"
    gForwardLayoutMap["v"] := "м"
    gForwardLayoutMap["V"] := "М"
    gForwardLayoutMap["b"] := "и"
    gForwardLayoutMap["B"] := "И"
    gForwardLayoutMap["n"] := "т"
    gForwardLayoutMap["N"] := "Т"
    gForwardLayoutMap["m"] := "ь"
    gForwardLayoutMap["M"] := "Ь"
    gForwardLayoutMap[","] := "б"
    gForwardLayoutMap["<"] := "Б"
    gForwardLayoutMap["."] := "ю"
    gForwardLayoutMap[">"] := "Ю"
    gForwardLayoutMap["/"] := "."
    gForwardLayoutMap["?"] := ","

    gReverseLayoutMap := Map()
    for englishChar, russianChar in gForwardLayoutMap
        gReverseLayoutMap[russianChar] := englishChar
}

HasLatin(text) {
    return RegExMatch(text, "[A-Za-z]")
}

HasCyrillic(text) {
    return RegExMatch(text, "[А-Яа-яЁё]")
}

SwitchLayoutForText(text) {
    if HasCyrillic(text) && !HasLatin(text)
        SwitchToLayout("ru")
    else if HasLatin(text) && !HasCyrillic(text)
        SwitchToLayout("en")
}

GetCurrentLayout() {
    langId := DllCall("GetKeyboardLayout", "UInt", 0, "Ptr") & 0xFFFF
    return langId = 0x419 ? "ru" : "en"
}

SwitchToLayout(targetLayout) {
    global EN_HKL, RU_HKL, WM_INPUTLANGCHANGEREQUEST

    hklHex := targetLayout = "ru" ? RU_HKL : EN_HKL
    hkl := DllCall("LoadKeyboardLayout", "Str", hklHex, "UInt", 1, "Ptr")
    hwnd := WinActive("A")
    if hwnd
        PostMessage(WM_INPUTLANGCHANGEREQUEST, 0, hkl,, "ahk_id " hwnd)
}

^!Pause:: {
    ToggleEnabled()
}

~RShift Up:: {
    ConvertTypedSentence()
}
