package com.pdfscrapper.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.webkit.DownloadListener;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.app.DownloadManager;
import android.net.Uri;
import android.os.Environment;
import android.widget.EditText;
import android.widget.Toast;

public class MainActivity extends Activity {

    private WebView webView;
    private SharedPreferences prefs;
    private static final String PREF_SERVER_URL = "server_url";
    private static final String DEFAULT_SERVER_URL = "http://192.168.0.160:8000";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        prefs = getSharedPreferences("PDFScrapperPrefs", Context.MODE_PRIVATE);
        String serverUrl = prefs.getString(PREF_SERVER_URL, DEFAULT_SERVER_URL);

        webView = new WebView(this);
        setContentView(webView);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setUserAgentString("Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36");

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                String currentUrl = prefs.getString(PREF_SERVER_URL, DEFAULT_SERVER_URL);
                String offlineHtml = "<html><body style='background:#07090e;color:#fff;font-family:sans-serif;padding:24px;text-align:center;'>"
                        + "<h2>⚡ Article PDF Generator</h2>"
                        + "<p style='color:#94a3b8;'>Server URL: <b>" + currentUrl + "</b></p>"
                        + "<p style='color:#ef4444;'>Unable to connect to server.</p>"
                        + "<button onclick='location.reload()' style='background:#ed193b;color:#fff;border:none;padding:12px 24px;border-radius:8px;font-weight:bold;margin:8px;'>🔄 Retry</button>"
                        + "<br><br>"
                        + "<button onclick='window.AndroidBridge.showServerConfig()' style='background:#2563eb;color:#fff;border:none;padding:12px 24px;border-radius:8px;font-weight:bold;margin:8px;'>⚙️ Change Server URL</button>"
                        + "</body></html>";
                view.loadDataWithBaseURL(null, offlineHtml, "text/html", "UTF-8", null);
            }
        });

        // Bridge to allow JS server URL configuration
        webView.addJavascriptInterface(new Object() {
            @android.webkit.JavascriptInterface
            public void showServerConfig() {
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        promptChangeServerUrl();
                    }
                });
            }
        }, "AndroidBridge");

        // Handle File Downloads
        webView.setDownloadListener(new DownloadListener() {
            @Override
            public void onDownloadStart(String url, String userAgent, String contentDisposition, String mimeType, long contentLength) {
                try {
                    DownloadManager.Request request = new DownloadManager.Request(Uri.parse(url));
                    request.setMimeType(mimeType);
                    request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                    request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, Uri.parse(url).getLastPathSegment());
                    
                    DownloadManager dm = (DownloadManager) getSystemService(DOWNLOAD_SERVICE);
                    if (dm != null) {
                        dm.enqueue(request);
                        Toast.makeText(getApplicationContext(), "Downloading PDF to Downloads folder...", Toast.LENGTH_LONG).show();
                    }
                } catch (Exception e) {
                    Toast.makeText(getApplicationContext(), "Download Error: " + e.getMessage(), Toast.LENGTH_LONG).show();
                }
            }
        });

        // Handle Incoming Shared Links
        Intent intent = getIntent();
        String action = intent.getAction();
        String type = intent.getType();

        if (Intent.ACTION_SEND.equals(action) && type != null && "text/plain".equals(type)) {
            String sharedText = intent.getStringExtra(Intent.EXTRA_TEXT);
            if (sharedText != null) {
                webView.loadUrl(serverUrl + "/?text=" + Uri.encode(sharedText));
                return;
            }
        }

        webView.loadUrl(serverUrl);
    }

    private void promptChangeServerUrl() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("⚙️ Set Server URL");
        builder.setMessage("Enter your free cloud server URL (e.g. https://your-app.onrender.com or your PC IP):");

        final EditText input = new EditText(this);
        input.setText(prefs.getString(PREF_SERVER_URL, DEFAULT_SERVER_URL));
        builder.setView(input);

        builder.setPositiveButton("Save", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                String newUrl = input.getText().toString().trim();
                if (!newUrl.isEmpty()) {
                    prefs.edit().putString(PREF_SERVER_URL, newUrl).apply();
                    webView.loadUrl(newUrl);
                }
            }
        });
        builder.setNegativeButton("Cancel", null);
        builder.show();
    }
}
