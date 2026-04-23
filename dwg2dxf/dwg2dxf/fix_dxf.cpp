#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <algorithm>
#include <cstring>

#ifdef _WIN32
#include <windows.h>
#endif

// Convert GBK/GB18030 bytes to UTF-8 string using Windows API
// Mimics Python's decode('gbk', errors='replace') behavior
std::string gbkToUtf8(const std::vector<char>& input) {
#ifdef _WIN32
    if (input.empty()) return "";

    // Try GB18030 (CP54936) first, fall back to GBK (CP936)
    int cp = 54936; // GB18030
    int wlen = MultiByteToWideChar(cp, MB_ERR_INVALID_CHARS, input.data(), static_cast<int>(input.size()), nullptr, 0);
    if (wlen == 0) {
        cp = 936; // GBK
        wlen = MultiByteToWideChar(cp, MB_ERR_INVALID_CHARS, input.data(), static_cast<int>(input.size()), nullptr, 0);
    }
    if (wlen > 0) {
        // Valid encoding, convert entire buffer
        std::vector<wchar_t> wstr(wlen);
        MultiByteToWideChar(cp, MB_ERR_INVALID_CHARS, input.data(), static_cast<int>(input.size()), wstr.data(), wlen);
        int u8len = WideCharToMultiByte(CP_UTF8, 0, wstr.data(), wlen, nullptr, 0, nullptr, nullptr);
        std::string result(u8len, '\0');
        WideCharToMultiByte(CP_UTF8, 0, wstr.data(), wlen, &result[0], u8len, nullptr, nullptr);
        return result;
    }

    // Invalid bytes found; process manually to match Python's errors='replace'
    // Python replaces each undecodable byte/sequence with U+FFFD
    std::string result;
    size_t i = 0;
    while (i < input.size()) {
        unsigned char c = static_cast<unsigned char>(input[i]);
        if (c < 0x80) {
            result += static_cast<char>(c);
            ++i;
            continue;
        }
        // Try 2-byte GBK sequence
        bool converted = false;
        if (i + 1 < input.size()) {
            wchar_t wch = 0;
            int ret = MultiByteToWideChar(936, MB_ERR_INVALID_CHARS, &input[i], 2, &wch, 1);
            if (ret > 0) {
                char u8buf[4];
                int u8len = WideCharToMultiByte(CP_UTF8, 0, &wch, 1, u8buf, 4, nullptr, nullptr);
                if (u8len > 0) {
                    result.append(u8buf, u8len);
                    i += 2;
                    converted = true;
                }
            }
        }
        if (!converted) {
            // Invalid byte/sequence - replace with U+FFFD (UTF-8: EF BF BD)
            result += "\xEF\xBF\xBD";
            ++i;
        }
    }
    return result;
#else
    // Linux/macOS fallback: assume input is valid UTF-8 already
    return std::string(input.begin(), input.end());
#endif
}

// Split string by CRLF delimiter
std::vector<std::string> splitLines(const std::string& text) {
    std::vector<std::string> lines;
    size_t start = 0;
    size_t pos = 0;
    while ((pos = text.find("\r\n", start)) != std::string::npos) {
        lines.emplace_back(text.substr(start, pos - start));
        start = pos + 2;
    }
    if (start <= text.size()) {
        lines.emplace_back(text.substr(start));
    }
    return lines;
}

// Join lines with CRLF
std::string joinLines(const std::vector<std::string>& lines) {
    if (lines.empty()) return "";
    std::string result;
    for (size_t i = 0; i < lines.size(); ++i) {
        if (i > 0) result += "\r\n";
        result += lines[i];
    }
    return result;
}

bool fixFile(const std::string& filepath) {
    std::cout << "Processing: " << filepath << std::endl;

    // Read raw bytes
    std::ifstream ifs(filepath, std::ios::binary);
    if (!ifs) {
        std::cerr << "  ERROR: Cannot open file" << std::endl;
        return false;
    }
    std::vector<char> raw((std::istreambuf_iterator<char>(ifs)), std::istreambuf_iterator<char>());
    ifs.close();
    size_t originalSize = raw.size();

    // Check if already UTF-8
    bool isUtf8 = true;
    for (size_t i = 0; i < raw.size(); ) {
        unsigned char c = static_cast<unsigned char>(raw[i]);
        if (c < 0x80) { ++i; continue; }
        size_t seqLen = 0;
        if ((c & 0xE0) == 0xC0) seqLen = 2;
        else if ((c & 0xF0) == 0xE0) seqLen = 3;
        else if ((c & 0xF8) == 0xF0) seqLen = 4;
        else { isUtf8 = false; break; }

        if (i + seqLen > raw.size()) { isUtf8 = false; break; }
        for (size_t j = 1; j < seqLen; ++j) {
            if ((static_cast<unsigned char>(raw[i+j]) & 0xC0) != 0x80) {
                isUtf8 = false; break;
            }
        }
        if (!isUtf8) break;
        i += seqLen;
    }

    std::string text;
    std::string encoding;
    if (isUtf8) {
        text = std::string(raw.begin(), raw.end());
        encoding = "utf-8";
        std::cout << "  Already UTF-8, no conversion needed" << std::endl;
    } else {
        text = gbkToUtf8(raw);
        if (text.empty()) {
            std::cerr << "  ERROR: Failed to decode" << std::endl;
            return false;
        }
        encoding = "gbk";
    }

    // Fix negative layer colors
    std::vector<std::string> lines = splitLines(text);
    bool inLayerTable = false;
    int fixedColors = 0;

    for (size_t i = 0; i < lines.size(); ++i) {
        const std::string& line = lines[i];
        if (line == "LAYER") {
            inLayerTable = true;
        } else if (line == "ENDTAB") {
            inLayerTable = false;
        } else if (inLayerTable) {
            // Trim whitespace
            std::string trimmed = line;
            trimmed.erase(0, trimmed.find_first_not_of(" \t"));
            trimmed.erase(trimmed.find_last_not_of(" \t") + 1);

            if (trimmed == "62" && i + 1 < lines.size()) {
                std::string valStr = lines[i + 1];
                valStr.erase(0, valStr.find_first_not_of(" \t"));
                valStr.erase(valStr.find_last_not_of(" \t") + 1);

                try {
                    int color = std::stoi(valStr);
                    if (color < 0) {
                        lines[i + 1] = "    " + std::to_string(-color);
                        fixedColors++;
                    }
                } catch (...) {
                    // not a number, skip
                }
            }
        }
    }

    if (fixedColors > 0) {
        std::cout << "  Fixed " << fixedColors << " negative layer colors" << std::endl;
    }

    text = joinLines(lines);

    // Update DWGCODEPAGE
    size_t pos = 0;
    while ((pos = text.find("$DWGCODEPAGE\r\n  3\r\nANSI_936", pos)) != std::string::npos) {
        text.replace(pos, 27, "$DWGCODEPAGE\r\n  3\r\nUTF-8");
        pos += 24;
    }

    // Write back as UTF-8
    std::ofstream ofs(filepath, std::ios::binary);
    if (!ofs) {
        std::cerr << "  ERROR: Cannot write file" << std::endl;
        return false;
    }
    ofs.write(text.data(), text.size());
    ofs.close();

    std::cout << "  " << originalSize << " bytes -> " << text.size()
              << " bytes (" << encoding << " -> UTF-8)" << std::endl;
    return true;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: fix_dxf <directory>" << std::endl;
        return 1;
    }

    std::string dir = argv[1];

    // Simple glob: iterate all .dxf files
#ifdef _WIN32
    std::string pattern = dir + "\\*.dxf";
    WIN32_FIND_DATAA fd;
    HANDLE hFind = FindFirstFileA(pattern.c_str(), &fd);
    if (hFind == INVALID_HANDLE_VALUE) {
        std::cerr << "No DXF files found in " << dir << std::endl;
        return 1;
    }

    std::vector<std::string> files;
    do {
        if (!(fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
            files.push_back(dir + "\\" + fd.cFileName);
        }
    } while (FindNextFileA(hFind, &fd));
    FindClose(hFind);
#else
    // Linux: use glob
    std::string pattern = dir + "/*.dxf";
    glob_t globResult;
    if (glob(pattern.c_str(), GLOB_TILDE, nullptr, &globResult) != 0) {
        std::cerr << "No DXF files found in " << dir << std::endl;
        return 1;
    }
    std::vector<std::string> files;
    for (size_t i = 0; i < globResult.gl_pathc; ++i) {
        files.push_back(globResult.gl_pathv[i]);
    }
    globfree(&globResult);
#endif

    if (files.empty()) {
        std::cerr << "No DXF files found in " << dir << std::endl;
        return 1;
    }

    std::sort(files.begin(), files.end());

    std::cout << "Found " << files.size() << " DXF files" << std::endl;
    std::cout << std::string(60, '=') << std::endl;

    int success = 0;
    for (const auto& f : files) {
        if (fixFile(f)) {
            success++;
        }
    }

    std::cout << std::string(60, '=') << std::endl;
    std::cout << "Done. " << success << "/" << files.size() << " files processed." << std::endl;
    return 0;
}

