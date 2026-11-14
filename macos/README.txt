ВАЖЛИВО / IMPORTANT: розпакуйте Boltsmith_mac.zip НА МАКУ (подвійний клік).
Unzip Boltsmith_mac.zip ON THE MAC (double-click) - unzipping on Windows breaks the app.

Boltsmith — macOS
=================

macOS
-----
1. Перетягніть Boltsmith.app у «Програми» (Applications).
2. Перший запуск: клацніть ПРАВОЮ кнопкою на Boltsmith.app -> «Відкрити» -> «Відкрити»
   (застосунок не підписаний Apple; далі запускається звичайним подвійним кліком).
   Якщо macOS пише «пошкоджений»: у Терміналі
       xattr -dr com.apple.quarantine /Applications/Boltsmith.app
3. Перший запуск завантажує CAD-ядро (кілька хвилин, з'явиться сповіщення).
Файли зберігаються в ~/Documents/Boltsmith/output. Лог: ~/Library/Logs/Boltsmith.log

macOS
-----
1. Drag Boltsmith.app to Applications.
2. First start: RIGHT-click Boltsmith.app -> Open -> Open (the app is not signed by Apple;
   afterwards a normal double-click works). If macOS says it is "damaged", run in Terminal:
       xattr -dr com.apple.quarantine /Applications/Boltsmith.app
3. The first start downloads the CAD kernel (a few minutes, a notification appears).
Files go to ~/Documents/Boltsmith/output. Log: ~/Library/Logs/Boltsmith.log
