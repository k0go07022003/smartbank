# Przygotowanie do obrony offline

Projekt trzeba umieć samodzielnie wyjaśnić i zmodyfikować. Stary SmartBank miał wskazanych współautorów; nowa implementacja powstała z pomocą Codex. Nie przedstawiaj tego jako dowodu samodzielnego napisania całości. Zasady dopuszczalnego korzystania z pomocy ustala prowadzący.

## Scenariusz prezentacji

1. Uruchom MariaDB i `php artisan serve` w katalogu `laravel`.
2. Zaloguj Annę (`anna@smartbank.test`, `DemoBank123!`). Pokaż saldo i rachunek.
3. Wykonaj przelew 12,34 zł na rachunek Jana, pokaż ekran potwierdzenia i historię.
4. Zaloguj Jana. Pokaż wzrost salda i przelew przychodzący.
5. Spróbuj przelewu większego od salda, zerowego i na własny rachunek. Pokaż błędy.
6. Zaloguj administratora. Dodaj, wyświetl, edytuj i usuń testowego użytkownika z zerowym saldem. Pokaż też blokadę konta.
7. Zarejestruj nowe konto. Pokaż, że przed aktywacją nie ma dostępu do rachunku. Znajdź link w `storage/logs/laravel.log`, otwórz go i pokaż dostęp po aktywacji.
8. Jako klient otwórz `/admin/users` — odpowiedź 403. Po wylogowaniu `/dashboard` przekierowuje na logowanie.
9. Uruchom `php artisan test`. Wyjaśnij co najmniej test przelewu i test uprawnień.

## Gdzie zmienić kod na polecenie prowadzącego

| Przykładowa zmiana | Miejsce |
|---|---|
| Dłuższe hasło | `app/Support/UserRules.php`, a także `partials/identity.blade.php` |
| Nowa walidacja nazwiska | regex w `UserRules.php` |
| Maksymalna kwota przelewu | `BankController::preview` i `TransferService::send` oraz komunikat i test |
| Inny wygląd panelu | `resources/views/bank/dashboard.blade.php`, `public/css/bank.css` |
| Więcej pozycji historii | `BankController::historyPage`, argument `paginate` |
| Nowa kolumna użytkownika | nowa migracja, model, reguły walidacji, formularz i widok |
| Nowy poziom uprawnień | walidacja roli, middleware, routing i formularz administratora |

Przykład ćwiczenia: zmień tytuł pola „Tytuł przelewu” na „Opis płatności”, następnie ogranicz jego długość do 100 znaków w walidacji i HTML. Uruchom testy, dodaj przypadek 101 znaków i wyjaśnij różnicę między walidacją klienta i serwera.

## Pytania, które warto umieć wyjaśnić

- **Hashowanie a szyfrowanie:** hasła nie odzyskujemy; porównujemy je przez bezpieczne sprawdzenie hasha. Cast `hashed` automatycznie hashuje zapis.
- **Sesja:** cookie identyfikuje sesję, a stan i roboczy przelew znajdują się po stronie serwera. Po zalogowaniu ID sesji się zmienia.
- **Autoryzacja:** samo ukrycie linku administratora nie wystarcza; middleware kontroluje każdy adres i każde żądanie modyfikujące.
- **CSRF:** `@csrf` dodaje token formularza; Laravel sprawdza, czy żądanie pochodzi z właściwej sesji.
- **SQL Injection:** Eloquent przekazuje wartości jako parametry; wprowadzony fragment SQL nie staje się częścią polecenia.
- **XSS:** `{{ ... }}` w Blade koduje znaki HTML pochodzące od użytkownika.
- **Kwoty:** 12,34 zł to 1234 grosze zapisane jako integer. Nie używamy float do sald.
- **Transakcja:** oba salda i wpis historii zapisują się razem albo wszystkie zmiany są wycofywane.
- **Blokada rekordów:** dwa jednoczesne przelewy nie mogą oba wydać tego samego salda. Blokady muszą działać w MariaDB/InnoDB.
- **Idempotencja:** UUID zlecenia i unikalny indeks uniemożliwiają podwójne obciążenie przy ponownym wysłaniu.
- **Soft delete:** usunięty użytkownik nie może się zalogować, ale jego wcześniejsze przelewy pozostają czytelne.
- **Aktywacja e-mail:** link jest podpisany, związany z użytkownikiem i ma termin ważności. Tryb log pokazuje wiadomość lokalnie; SMTP dostarcza ją na skrzynkę.

## Przed wyjściem na zajęcia

- Zainstaluj zależności i upewnij się, że `vendor/` jest na komputerze używanym do obrony.
- Sprawdź działanie MariaDB, `.env`, klucza aplikacji, kont demonstracyjnych i portu 8000.
- Odłącz Internet i przejdź powyższy scenariusz.
- Zachowaj kopię bazy i projektu; nie wykonuj `migrate:fresh` na bazie, którą chcesz zachować.
- Ćwicz zmiany kodu bez wyszukiwarki. Nie regeneruj `APP_KEY` przy każdym uruchomieniu.
