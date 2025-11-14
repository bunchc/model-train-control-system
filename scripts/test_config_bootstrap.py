from central_api.app.services.config_manager import ConfigManager

if __name__ == "__main__":
    try:
        config = ConfigManager()
        print("Config bootstrapped successfully.")
    except Exception as e:
        print(f"Error during config bootstrap: {e}")
        import traceback
        traceback.print_exc()
