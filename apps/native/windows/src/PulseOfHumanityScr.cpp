#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shellapi.h>
#include <wrl.h>
#include <wrl/client.h>

#include <memory>
#include <string>
#include <utility>
#include <cwctype>

#include <WebView2.h>

using Microsoft::WRL::Callback;
using Microsoft::WRL::ComPtr;

namespace {

enum class AppMode {
  Config,
  Preview,
  Fullscreen,
};

struct CommandLineOptions {
  AppMode mode = AppMode::Fullscreen;
  HWND previewHost = nullptr;
};

std::wstring ToLower(std::wstring value) {
  for (auto& ch : value) {
    ch = static_cast<wchar_t>(towlower(ch));
  }
  return value;
}

std::wstring DirectoryName(const std::wstring& path) {
  const auto index = path.find_last_of(L"\\/");
  if (index == std::wstring::npos) {
    return {};
  }
  return path.substr(0, index);
}

std::wstring JoinPath(const std::wstring& left, const std::wstring& right) {
  if (left.empty()) {
    return right;
  }
  if (right.empty()) {
    return left;
  }
  if (left.back() == L'\\' || left.back() == L'/') {
    return left + right;
  }
  return left + L"\\" + right;
}

std::wstring ExecutableDirectory() {
  wchar_t buffer[MAX_PATH] = {};
  GetModuleFileNameW(nullptr, buffer, MAX_PATH);
  return DirectoryName(buffer);
}

HWND ParsePreviewHandle(const std::wstring& token) {
  if (token.empty()) {
    return nullptr;
  }
  const auto rawValue = _wcstoui64(token.c_str(), nullptr, 10);
  return reinterpret_cast<HWND>(static_cast<ULONG_PTR>(rawValue));
}

CommandLineOptions ParseCommandLine() {
  CommandLineOptions options;
  int argc = 0;
  LPWSTR* argv = CommandLineToArgvW(GetCommandLineW(), &argc);

  if (!argv || argc <= 1) {
    if (argv) {
      LocalFree(argv);
    }
    return options;
  }

  const std::wstring command = ToLower(argv[1]);
  if (command.rfind(L"/c", 0) == 0 || command.rfind(L"-c", 0) == 0) {
    options.mode = AppMode::Config;
  } else if (command.rfind(L"/p", 0) == 0 || command.rfind(L"-p", 0) == 0) {
    options.mode = AppMode::Preview;
    const auto separator = command.find(L':');
    if (separator != std::wstring::npos) {
      options.previewHost = ParsePreviewHandle(command.substr(separator + 1));
    } else if (argc > 2) {
      options.previewHost = ParsePreviewHandle(argv[2]);
    }
  } else {
    options.mode = AppMode::Fullscreen;
  }

  LocalFree(argv);
  return options;
}

class ScreensaverApp {
 public:
  explicit ScreensaverApp(CommandLineOptions options)
      : options_(std::move(options)) {}

  int Run(HINSTANCE instance, int showCommand) {
    instance_ = instance;
    if (!RegisterWindowClass()) {
      return 1;
    }

    const HRESULT oleResult = OleInitialize(nullptr);
    if (FAILED(oleResult)) {
      return 1;
    }

    const bool created = CreateHostWindow(showCommand);
    if (!created) {
      OleUninitialize();
      return 1;
    }

    MSG message = {};
    static POINT initialMousePos = {};
    static bool mouseInitialized = false;
    while (GetMessageW(&message, nullptr, 0, 0) > 0) {
      if (options_.mode == AppMode::Fullscreen) {
        if (!mouseInitialized) {
          GetCursorPos(&initialMousePos);
          mouseInitialized = true;
        }

        POINT currentPos = {};
        GetCursorPos(&currentPos);
        if (abs(currentPos.x - initialMousePos.x) > 3 ||
            abs(currentPos.y - initialMousePos.y) > 3) {
          PostQuitMessage(0);
        }
      }

      TranslateMessage(&message);
      DispatchMessageW(&message);
    }

    OleUninitialize();
    return static_cast<int>(message.wParam);
  }

  void OnCreate() {
    InitializeWebView();
  }

  void OnSize() {
    ResizeWebView();
  }

  void OnDestroy() {
    webview_.Reset();
    controller_.Reset();
    PostQuitMessage(0);
  }

  void MaybeExitFromInput() {
    if (options_.mode == AppMode::Fullscreen) {
      DestroyWindow(window_);
    }
  }

  static LRESULT CALLBACK WindowProc(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam) {
    if (message == WM_NCCREATE) {
      auto* createStruct = reinterpret_cast<CREATESTRUCTW*>(lParam);
      auto* app = static_cast<ScreensaverApp*>(createStruct->lpCreateParams);
      SetWindowLongPtrW(hwnd, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(app));
      app->window_ = hwnd;
    }

    auto* app = reinterpret_cast<ScreensaverApp*>(GetWindowLongPtrW(hwnd, GWLP_USERDATA));
    if (!app) {
      return DefWindowProcW(hwnd, message, wParam, lParam);
    }

    switch (message) {
      case WM_CREATE:
        app->OnCreate();
        return 0;
      case WM_SIZE:
        app->OnSize();
        return 0;
      case WM_MOUSEMOVE:
        app->MaybeExitFromInput();
        return 0;
      case WM_KEYDOWN:
      case WM_SYSKEYDOWN:
        if (wParam == VK_ESCAPE) {
          PostQuitMessage(0);
          return 0;
        }
      case WM_LBUTTONDOWN:
      case WM_RBUTTONDOWN:
      case WM_MBUTTONDOWN:
      case WM_MOUSEWHEEL:
      case WM_MOUSEHWHEEL:
      case WM_TOUCH:
      case WM_POINTERDOWN:
        app->MaybeExitFromInput();
        return 0;
      case WM_CLOSE:
        DestroyWindow(hwnd);
        PostQuitMessage(0);
        return 0;
      case WM_DESTROY:
        app->OnDestroy();
        return 0;
      default:
        return DefWindowProcW(hwnd, message, wParam, lParam);
    }
  }

 private:
  bool RegisterWindowClass() const {
    WNDCLASSEXW windowClass = {};
    windowClass.cbSize = sizeof(windowClass);
    windowClass.hInstance = instance_;
    windowClass.lpfnWndProc = &ScreensaverApp::WindowProc;
    windowClass.lpszClassName = L"PulseOfHumanityScreensaverWindow";
    windowClass.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    return RegisterClassExW(&windowClass) != 0;
  }

  bool CreateHostWindow(int showCommand) {
    DWORD style = WS_VISIBLE;
    DWORD extendedStyle = 0;
    RECT bounds = {};
    HWND parent = nullptr;

    if (options_.mode == AppMode::Preview && options_.previewHost) {
      parent = options_.previewHost;
      style |= WS_CHILD;
      GetClientRect(parent, &bounds);
    } else {
      style |= WS_POPUP;
      extendedStyle = WS_EX_TOPMOST;
      MONITORINFO monitorInfo = { sizeof(monitorInfo) };
      GetMonitorInfoW(MonitorFromWindow(nullptr, MONITOR_DEFAULTTOPRIMARY), &monitorInfo);
      bounds = monitorInfo.rcMonitor;
    }

    const int width = bounds.right - bounds.left;
    const int height = bounds.bottom - bounds.top;

    window_ = CreateWindowExW(
        extendedStyle,
        L"PulseOfHumanityScreensaverWindow",
        L"Pulse of Humanity",
        style,
        bounds.left,
        bounds.top,
        width,
        height,
        parent,
        nullptr,
        instance_,
        this);

    if (!window_) {
      return false;
    }

    ShowWindow(window_, showCommand);
    UpdateWindow(window_);
    return true;
  }

  std::wstring AssetDirectory() const {
    return JoinPath(JoinPath(ExecutableDirectory(), L"assets"), L"screensaver");
  }

  std::wstring BootstrapScript() const {
    const std::wstring cursorHideDelay = options_.mode == AppMode::Preview ? L"-1" : L"2000";
    return L"window.__PULSE_OF_HUMANITY_SCREENSAVER_CONFIG__ = {"
           L"startOnLoad:true,"
           L"idleTimeoutMs:0,"
           L"cursorHideDelayMs:" + cursorHideDelay + L","
           L"fullscreen:false,"
           L"exitOnInput:{enabled:false,mousemove:true,keydown:true,click:true,wheel:true,touchstart:true}"
           L"};";
  }

  void ResizeWebView() {
    if (!controller_) {
      return;
    }
    RECT bounds = {};
    GetClientRect(window_, &bounds);
    controller_->put_Bounds(bounds);
  }

  void InitializeWebView() {
    const std::wstring assetDirectory = AssetDirectory();
    const std::wstring userDataDirectory = JoinPath(ExecutableDirectory(), L"webview2-data");

    CreateCoreWebView2EnvironmentWithOptions(
        nullptr,
        userDataDirectory.c_str(),
        nullptr,
        Callback<ICoreWebView2CreateCoreWebView2EnvironmentCompletedHandler>(
            [this, assetDirectory](HRESULT result, ICoreWebView2Environment* environment) -> HRESULT {
              if (FAILED(result) || !environment) {
                DestroyWindow(window_);
                return S_OK;
              }

              return environment->CreateCoreWebView2Controller(
                  window_,
                  Callback<ICoreWebView2CreateCoreWebView2ControllerCompletedHandler>(
                      [this, assetDirectory](HRESULT controllerResult, ICoreWebView2Controller* controller) -> HRESULT {
                        if (FAILED(controllerResult) || !controller) {
                          DestroyWindow(window_);
                          return S_OK;
                        }

                        controller_ = controller;
                        controller_->get_CoreWebView2(&webview_);
                        ResizeWebView();

                        if (webview_) {
                          ComPtr<ICoreWebView2_3> webview3;
                          if (SUCCEEDED(webview_.As(&webview3)) && webview3) {
                            webview3->SetVirtualHostNameToFolderMapping(
                                L"screensaver.local",
                                assetDirectory.c_str(),
                                COREWEBVIEW2_HOST_RESOURCE_ACCESS_KIND_ALLOW);
                          }
                          webview_->AddScriptToExecuteOnDocumentCreated(BootstrapScript().c_str(), nullptr);

                          ComPtr<ICoreWebView2Settings> settings;
                          if (SUCCEEDED(webview_->get_Settings(&settings)) && settings) {
                            settings->put_AreDefaultContextMenusEnabled(FALSE);
                            settings->put_AreDevToolsEnabled(FALSE);
                            settings->put_IsStatusBarEnabled(FALSE);
                            settings->put_IsZoomControlEnabled(FALSE);
                          }

                          webview_->Navigate(L"https://screensaver.local/index.html");
                        }

                        return S_OK;
                      })
                      .Get());
            })
            .Get());
  }

  CommandLineOptions options_;
  HINSTANCE instance_ = nullptr;
  HWND window_ = nullptr;
  ComPtr<ICoreWebView2Controller> controller_;
  ComPtr<ICoreWebView2> webview_;
};

}  // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int showCommand) {
  const CommandLineOptions options = ParseCommandLine();
  if (options.mode == AppMode::Config) {
    MessageBoxW(
        nullptr,
        L"Pulse of Humanity uses the bundled offline screensaver build. Native configuration is not implemented yet.",
        L"Pulse of Humanity",
        MB_OK | MB_ICONINFORMATION);
    return 0;
  }

  ScreensaverApp app(options);
  return app.Run(instance, showCommand);
}