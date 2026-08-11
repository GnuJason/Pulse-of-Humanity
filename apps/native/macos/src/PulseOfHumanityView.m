#import <Cocoa/Cocoa.h>
#import <ScreenSaver/ScreenSaver.h>
#import <WebKit/WebKit.h>

@interface PulseOfHumanityView : ScreenSaverView

@property(nonatomic, strong) WKWebView *webView;
@property(nonatomic, strong) id localEventMonitor;
@property(nonatomic, assign, getter=isPreviewMode) BOOL previewMode;

@end

@implementation PulseOfHumanityView

- (instancetype)initWithFrame:(NSRect)frame isPreview:(BOOL)isPreview {
  self = [super initWithFrame:frame isPreview:isPreview];
  if (self) {
    _previewMode = isPreview;
    [self setAnimationTimeInterval:(1.0 / 30.0)];
    [self setWantsLayer:YES];
    [self configureWebView];
    [self loadScreensaver];
  }
  return self;
}

- (void)configureWebView {
  WKUserContentController *contentController = [[WKUserContentController alloc] init];
  NSString *cursorHideDelay = self.previewMode ? @"-1" : @"2000";
  NSString *scriptSource = [NSString stringWithFormat:
      @"window.__PULSE_OF_HUMANITY_SCREENSAVER_CONFIG__ = {"
       "startOnLoad:true,"
       "idleTimeoutMs:0,"
       "cursorHideDelayMs:%@,"
       "fullscreen:false,"
       "exitOnInput:{enabled:false,mousemove:true,keydown:true,click:true,wheel:true,touchstart:true}"
       "};",
      cursorHideDelay];
  WKUserScript *bootstrapScript = [[WKUserScript alloc] initWithSource:scriptSource
                                                         injectionTime:WKUserScriptInjectionTimeAtDocumentStart
                                                      forMainFrameOnly:YES];
  [contentController addUserScript:bootstrapScript];

  WKWebViewConfiguration *configuration = [[WKWebViewConfiguration alloc] init];
  configuration.userContentController = contentController;

  self.webView = [[WKWebView alloc] initWithFrame:self.bounds configuration:configuration];
  self.webView.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;
  self.webView.translatesAutoresizingMaskIntoConstraints = YES;
  [self addSubview:self.webView];
}

- (void)loadScreensaver {
  NSBundle *bundle = [NSBundle bundleForClass:[self class]];
  NSURL *indexURL = [bundle URLForResource:@"index" withExtension:@"html" subdirectory:@"screensaver"];
  NSURL *readAccessURL = [[bundle resourceURL] URLByAppendingPathComponent:@"screensaver"];
  if (indexURL && readAccessURL) {
    [self.webView loadFileURL:indexURL allowingReadAccessToURL:readAccessURL];
  }
}

- (BOOL)hasConfigureSheet {
  return NO;
}

- (NSWindow *)configureSheet {
  return nil;
}

- (BOOL)acceptsFirstResponder {
  return YES;
}

- (void)startAnimation {
  [super startAnimation];
  [[self window] makeFirstResponder:self];
  [self installExitMonitorIfNeeded];
}

- (void)stopAnimation {
  [self removeExitMonitor];
  [super stopAnimation];
}

- (void)animateOneFrame {
}

- (void)requestExitIfNeeded {
  if (!self.previewMode) {
    [NSApp terminate:nil];
  }
}

- (void)installExitMonitorIfNeeded {
  if (self.previewMode || self.localEventMonitor != nil) {
    return;
  }

  NSEventMask mask = NSEventMaskMouseMoved |
                     NSEventMaskLeftMouseDown |
                     NSEventMaskRightMouseDown |
                     NSEventMaskOtherMouseDown |
                     NSEventMaskScrollWheel |
                     NSEventMaskKeyDown;

  __weak typeof(self) weakSelf = self;
  self.localEventMonitor = [NSEvent addLocalMonitorForEventsMatchingMask:mask
                                                                  handler:^NSEvent * _Nullable(NSEvent *event) {
    [weakSelf requestExitIfNeeded];
    return event;
  }];
}

- (void)removeExitMonitor {
  if (self.localEventMonitor != nil) {
    [NSEvent removeMonitor:self.localEventMonitor];
    self.localEventMonitor = nil;
  }
}

- (void)mouseDown:(NSEvent *)event {
  [self requestExitIfNeeded];
}

- (void)mouseMoved:(NSEvent *)event {
  [self requestExitIfNeeded];
}

- (void)rightMouseDown:(NSEvent *)event {
  [self requestExitIfNeeded];
}

- (void)otherMouseDown:(NSEvent *)event {
  [self requestExitIfNeeded];
}

- (void)scrollWheel:(NSEvent *)event {
  [self requestExitIfNeeded];
}

- (void)keyDown:(NSEvent *)event {
  [self requestExitIfNeeded];
}

@end