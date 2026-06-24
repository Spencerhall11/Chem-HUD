#define WIN32_LEAN_AND_MEAN
#define NOMINMAX              // Fixes the 'illegal token' errors on lines 81-82
#include <windows.h>
#include <d3d11.h>
#include <dxgi1_2.h>
#include <iostream>
#include <vector>
#include <algorithm>
#include <cstdint>

// Directives to link libraries without manual flags
#pragma comment(lib, "d3d11.lib")
#pragma comment(lib, "dxgi.lib")

class ScreenReaderEye {
private:
    ID3D11Device* m_Device = nullptr;
    ID3D11DeviceContext* m_Context = nullptr;
    IDXGIOutputDuplication* m_DeskDupl = nullptr;
    ID3D11Texture2D* m_StagingTex = nullptr;
    const int m_CaptureSize = 300;

public:
    ScreenReaderEye() {}

    bool Initialize() {
        HRESULT hr;
        D3D_FEATURE_LEVEL featureLevel;

        // Create D3D11 Device
        hr = D3D11CreateDevice(NULL, D3D_DRIVER_TYPE_HARDWARE, NULL, 0, NULL, 0, D3D11_SDK_VERSION, &m_Device, &featureLevel, &m_Context);
        if (FAILED(hr)) return false;

        // Get DXGI interfaces
        IDXGIDevice* dxgiDevice = nullptr;
        m_Device->QueryInterface(__uuidof(IDXGIDevice), (void**)&dxgiDevice);

        IDXGIAdapter* dxgiAdapter = nullptr;
        dxgiDevice->GetParent(__uuidof(IDXGIAdapter), (void**)&dxgiAdapter);
        dxgiDevice->Release();

        IDXGIOutput* dxgiOutput = nullptr;
        dxgiAdapter->EnumOutputs(0, &dxgiOutput);
        dxgiAdapter->Release();

        IDXGIOutput1* dxgiOutput1 = nullptr;
        dxgiOutput->QueryInterface(__uuidof(IDXGIOutput1), (void**)&dxgiOutput1);
        dxgiOutput->Release();

        // Initialize Desktop Duplication
        hr = dxgiOutput1->DuplicateOutput(m_Device, &m_DeskDupl);
        dxgiOutput1->Release();
        if (FAILED(hr)) return false;

        // Create staging texture (for CPU access)
        D3D11_TEXTURE2D_DESC desc = {};
        desc.Width = m_CaptureSize;
        desc.Height = m_CaptureSize;
        desc.MipLevels = 1;
        desc.ArraySize = 1;
        desc.Format = DXGI_FORMAT_B8G8R8A8_UNORM;
        desc.SampleDesc.Count = 1;
        desc.Usage = D3D11_USAGE_STAGING;
        desc.CPUAccessFlags = D3D11_CPU_ACCESS_READ;

        hr = m_Device->CreateTexture2D(&desc, NULL, &m_StagingTex);
        return SUCCEEDED(hr);
    }

    void CaptureAroundMouse(void* sharedBuffer) {
    IDXGIResource* desktopResource = nullptr;
    DXGI_OUTDUPL_FRAME_INFO frameInfo;

    // 1. Increase timeout to 100ms. 
    // DXGI_ERROR_WAIT_TIMEOUT is NORMAL if the screen hasn't changed.
    HRESULT hr = m_DeskDupl->AcquireNextFrame(100, &frameInfo, &desktopResource);
    
    if (hr == DXGI_ERROR_WAIT_TIMEOUT) {
        return; // No new frame, just skip this loop iteration
    }

    if (FAILED(hr)) {
        // If we lost access (e.g., UAC prompt or resolution change), we'd need to re-init.
        return; 
    }

    ID3D11Texture2D* acquireTex = nullptr;
    hr = desktopResource->QueryInterface(__uuidof(ID3D11Texture2D), (void**)&acquireTex);
    if (FAILED(hr)) {
        desktopResource->Release();
        m_DeskDupl->ReleaseFrame();
        return;
    }

    POINT mousePos;
    GetCursorPos(&mousePos);

    D3D11_BOX sourceBox;
    int halfSize = m_CaptureSize / 2;
    
    // 2. Bound the box so it doesn't go off-screen (which causes CopySubresourceRegion to fail)
    sourceBox.left = (UINT)std::max(0, (int)(mousePos.x - halfSize));
    sourceBox.top = (UINT)std::max(0, (int)(mousePos.y - halfSize));
    sourceBox.front = 0;
    sourceBox.right = sourceBox.left + m_CaptureSize;
    sourceBox.bottom = sourceBox.top + m_CaptureSize;
    sourceBox.back = 1;

    m_Context->CopySubresourceRegion(m_StagingTex, 0, 0, 0, 0, acquireTex, 0, &sourceBox);

    D3D11_MAPPED_SUBRESOURCE mapped;
    if (SUCCEEDED(m_Context->Map(m_StagingTex, 0, D3D11_MAP_READ, 0, &mapped))) {
        uint8_t* dest = static_cast<uint8_t*>(sharedBuffer);
        uint8_t* src = static_cast<uint8_t*>(mapped.pData);

        for (int y = 0; y < m_CaptureSize; y++) {
            memcpy(dest + (y * m_CaptureSize * 4), 
                   src + (y * mapped.RowPitch), 
                   m_CaptureSize * 4);
        }
        m_Context->Unmap(m_StagingTex, 0);
    }

    acquireTex->Release();
    desktopResource->Release();
    m_DeskDupl->ReleaseFrame();
    }
};

int main() {
    ScreenReaderEye eye;
    if (!eye.Initialize()) {
        std::cerr << "Initialization failed. (Make sure no other duplicators are active)" << std::endl;
        return 1;
    }

    const size_t bufferSize = 300 * 300 * 4;
    // Explicitly use CreateFileMappingW to match the Wide string L"..."
    HANDLE hMapFile = CreateFileMappingW(INVALID_HANDLE_VALUE, NULL, PAGE_READWRITE, 0, (DWORD)bufferSize, L"Global\\ChemHUD_FrameBuffer");

    if (hMapFile == NULL) {
        std::cerr << "Mapping failed. Error: " << GetLastError() << " (Run as Admin!)" << std::endl;
        return 1;
    }

    void* pBuf = MapViewOfFile(hMapFile, FILE_MAP_ALL_ACCESS, 0, 0, bufferSize);
    std::cout << "Eye Active. ESC to quit." << std::endl;

    while (!(GetAsyncKeyState(VK_ESCAPE) & 0x8000)) {
        eye.CaptureAroundMouse(pBuf);
        Sleep(10); 
    }

    UnmapViewOfFile(pBuf);
    CloseHandle(hMapFile);
    return 0;
}