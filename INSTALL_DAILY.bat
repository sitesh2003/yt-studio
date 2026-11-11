@echo off
echo Setting up YT Studio to make the day's videos every day at 1:30 PM...
schtasks /Create /F /SC DAILY /ST 13:30 /TN "YT Studio daily" /TR "\"%~dp0run_daily.bat\""
echo.
echo Done. Each day at 1:30 PM new videos appear in the "jobs" folder (missed runs start when the PC is next on).
echo Open its review.html, and double-click APPROVE.bat to upload and schedule it.
echo To stop it later: schtasks /Delete /TN "YT Studio daily" /F
pause
