                                                                **File Transfer Service UI v1.0**  
                                                                        ©2025 - ARC  
===========================
        OVERVIEW
===========================

✔ This is a Python-based User Interface for File Transfer Service (FTS) APIs to manage files efficiently.

✔ The UI is built using the Tkinter library in Python.

✔ Designed to interact with FTS APIs in a user-friendly way, as an alternative to Postman.


===========================
      KEY FEATURES
===========================

✔ Multi-Customer Configuration  
  - Add and manage multiple customers by editing the config.ini file.

✔ Multiple File Upload & Download  
  - Upload and download multiple files to/from FTS in one go.

✔ Threading Support  
  - Keeps the UI responsive during upload/download operations.

✔ Encrypted Client Secret  
  - Client secrets are encrypted and accessible only through the application.

✔ Auto-Filtering  
  - Grid filter updates in real-time as you type, and resets when cleared.

✔ Reset Functionality  
  - Clears local UI data (e.g., grid entries, logs, selections) without affecting files in the FTS bucket.

✔ Live Logging  
  - Logs are stored in the `log/ftsapp.log` file.

✔ Grid Sorting  
  - Sort files by size, name, or date in the grid view.

✔ Export Grid Data  
  - Download the grid data as a CSV file to your local system.

✔ Access Token Caching  
  - Access tokens are cached per customer and reused until they expire, reducing unnecessary API calls.


===========================
       LIMITATIONS
===========================

⚠ Single File Move
  - Only one file can be moved at a time.
	
