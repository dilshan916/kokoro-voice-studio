// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri_plugin_shell::ShellExt;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // Auto-spawn Python FastAPI sidecar on application launch
            #[cfg(desktop)]
            {
                let handle = app.handle().clone();
                tauri::async_runtime::spawn(async move {
                    if let Ok(sidecar_command) = handle.shell().sidecar("kokoro-server") {
                        let (mut _rx, mut _child) = sidecar_command
                            .spawn()
                            .expect("Failed to spawn Kokoro FastAPI backend sidecar");
                    }
                });
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Kokoro Voice Studio Pro");
}
